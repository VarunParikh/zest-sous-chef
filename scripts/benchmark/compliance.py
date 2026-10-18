"""E7 persona constraint compliance (Evaluation Plan §4 E7, §4.15 C52; O2; FR-60, FR-90, FR-91).

Every `persona_prompts_v1` prompt runs in a fresh session with the persona's preset levers,
then up to 4 follow-ups (confirm yes or add, the first clarify option, accept the add-on).
Every surface is checked by the independent checker (`backend.evaluation.compliance`): cart
lines and their swap alternatives, carted, swap, add-on, chip and runner-up dishes, add-on
prices against the cap, substitutions and stock. Pass rule: zero violations in any arm.

Arms: `real` (local llama3.2:3b, llama-guard3:1b, intent and extraction; sample photos) and
`adversarial` (scripted model whose transcript extractions always contain forbidden items).
`--sensitivity` runs a few adversarial prompts with the eligibility code switched off, to show
the checker finds violations when the guardrails are absent (not a scored run).
Run: .venv/bin/python scripts/benchmark/compliance.py --arm adversarial|real [--sensitivity] [--out DIR]
"""
import re
import sys

from _app import build
from _common import ROOT, parser, rows, save

sys.path.insert(0, str(ROOT))
from tests.acceptance.chat_harness import FakeOllama  # noqa: E402

from backend.evaluation.compliance import load_variants, violations  # noqa: E402
from backend.evaluation.results import make_result  # noqa: E402

VARIANTS = load_variants()
BY_NAME = {v["name"]: v for v in VARIANTS.values()}
DISH_ID = re.compile(r"^D\d+$")
PREFER = ("yes", "add", "accept")


class Checker:
    def __init__(self, app, levers: dict):
        self.app, self.store, self.levers = app, app.state.store, levers
        self.stock_filter = levers["business"]["stock_filter"]

    def variant(self, vid: str, where: str) -> list[dict]:
        v = VARIANTS.get(vid)
        if v is None:
            return [{"surface": where, "item": vid, "rule": "unknown_variant"}]
        return [{"surface": where, "item": v["name"], "rule": r} for r in violations(v, self.levers)]

    def dish(self, dish_id: str, where: str) -> list[dict]:
        """A suggested dish complies when every essential ingredient has a compliant (and, with the filter, in-stock) variant."""
        rec, out = self.store.dish(dish_id), []
        for line in rec.ingredients:
            if not line.essential:
                continue
            ok = [v for v in self.store.variants_for(line.ingredient_name)
                  if not violations(VARIANTS[v.variant_id], self.levers) and (not self.stock_filter or self.store.in_stock(v.variant_id))]
            if not ok:
                out.append({"surface": where, "item": f"{dish_id} {rec.dish.name}", "rule": f"no_compliant_variant:{line.ingredient_name}"})
        return out

    def dish_by_name(self, name: str, where: str) -> list[dict]:
        rec = next((d for d in self.store.dishes if d.dish.name == name), None)
        return self.dish(rec.dish.dish_id, where) if rec else [{"surface": where, "item": name, "rule": "unknown_dish"}]

    def turn(self, turn: dict) -> tuple[list[dict], int]:
        out, n = [], 0
        for d in turn.get("cart", {}).get("dishes", []):
            for ln in d["lines"]:
                n += 1
                out += self.variant(ln["variant_id"], "cart_line")
                for alt in ln["alternative_variant_ids"]:
                    n += 1
                    out += self.variant(alt, "line_alternative")
                if self.stock_filter and not ln["in_stock"]:
                    out.append({"surface": "cart_line", "item": ln["variant_name"], "rule": "stock"})
        for m in turn.get("messages", []):
            for c in m.get("cards", []):
                t = c.get("type")
                if t == "dish_added":
                    n += 1
                    out += self.dish(c["dish_id"], "dish_added")
                elif t == "swap_options":
                    for o in c["options"]:
                        n += 1
                        out += self.dish(o["dish_id"], "swap_option")
                elif t == "addon_suggestion":
                    n += 1
                    out += self.dish_by_name(c["item"]["name"], "addon")
                    if c["item"]["price_inr"] > self.levers["business"]["price_cap_inr"]:
                        out.append({"surface": "addon", "item": c["item"]["name"], "rule": "price_cap"})
                elif t == "clarify":
                    for o in c["options"]:
                        if DISH_ID.match(o["value"]):
                            n += 1
                            out += self.dish(o["value"], "dish_chip")
                elif t == "substitution":
                    n += 1
                    v = BY_NAME.get(c["to_item"])
                    out += self.variant(v["variant_id"], "substitution") if v else []
                elif t == "why_this":
                    for a in (c.get("breakdown") or {}).get("alternatives", []):
                        n += 1
                        out += self.dish(a["dish_id"], "runner_up")
        return out, n


def follow_up(client, sid, turn):
    """One follow-up from the latest turn: confirm, clarify, or accept the add-on."""
    for m in turn.get("messages", []):
        for c in m.get("cards", []):
            if c.get("type") == "confirm":
                values = [o["value"] for o in c["options"]]
                choice = next((p for p in PREFER if p in values), None)
                if choice:
                    return client.post(f"/api/v1/sessions/{sid}/action",
                                       json={"type": "confirm", "payload": {"confirm_id": c["confirm_id"], "choice": choice}})
            if c.get("type") == "clarify" and c["options"]:
                return client.post(f"/api/v1/sessions/{sid}/action",
                                   json={"type": "answer", "payload": {"question_id": c["question_id"], "choice": c["options"][0]["value"]}})
            if c.get("type") == "addon_suggestion":
                return client.post(f"/api/v1/sessions/{sid}/action",
                                   json={"type": "add_on", "payload": {"suggestion_id": c["suggestion_id"], "choice": "add"}})
    return None


def scripted(data) -> FakeOllama:
    fake = FakeOllama()
    for r in data:
        if r["text"] and r["scripted_intent"]:
            i = r["scripted_intent"]
            fake.intents[r["text"]] = {"intent": i["intent"], "confidence": 0.95, "mood_tags": i["mood_tags"],
                                       "dish_name": i["dish_name"], "servings": None}
        if r["kind"] == "ingredients":
            fake.extractions[r["text"].split(":")[0] + ":"] = r["scripted_extraction"]
    adv = next(r["scripted_extraction"] for r in data if r["kind"] == "transcript")
    fake.extractions[""] = adv  # any other content (the video fixtures): the adversarial extraction
    return fake


def disable_eligibility():
    """Sensitivity check only: every variant passes, as if the guardrails were missing."""
    from backend.engine import eligibility

    def permissive(v, levers, store, declared_allergens=()):
        return eligibility.Mask(True)

    for name, mod in list(sys.modules.items()):
        if name.startswith("backend.") and getattr(mod, "check_variant", None) is eligibility.check_variant:
            mod.check_variant = permissive
    eligibility.check_variant = permissive


def main():
    ap = parser(__doc__)
    ap.add_argument("--arm", choices=["adversarial", "real"], default="adversarial")
    ap.add_argument("--sensitivity", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    data = rows("persona_prompts_v1.jsonl", "all", False)
    if args.sensitivity:
        data = [r for r in data if r["persona"] in ("P1", "P6") and r["kind"] in ("named", "ingredients", "transcript")]
        disable_eligibility()
    if args.limit:
        data = data[:args.limit]
    fake = scripted(data) if args.arm == "adversarial" else None
    app, client = build(fake, data[0]["context_now"], data[0]["context_weather"])
    personas = {f"P{i}": lv for i, lv in enumerate(app.state.presets.values(), 1)}
    per, found, checked = [], [], 0
    for r in data:
        levers = personas[r["persona"]].model_dump(mode="json")
        check = Checker(app, levers)
        sid = client.post("/api/v1/sessions", json={"levers": levers}).json()["session_id"]
        body = {"sample_photo_id": r["sample_photo_id"]} if r["kind"] == "photo" else {"text": r["text"]}
        resp = client.post(f"/api/v1/sessions/{sid}/chat", json=body)
        turns, statuses = [], [resp.status_code]
        turn = resp.json() if resp.status_code == 200 else {}
        for _ in range(5):
            if not turn:
                break
            turns.append(turn)
            nxt = follow_up(client, sid, turn)
            if nxt is None:
                break
            statuses.append(nxt.status_code)
            turn = nxt.json() if nxt.status_code == 200 else {}
        cart = client.get(f"/api/v1/sessions/{sid}/cart").json()
        bad, n = [], 0
        for t in turns + [{"cart": cart}]:
            b, k = check.turn(t)
            bad += b
            n += k
        checked += n
        for b in bad:
            found.append({"id": r["id"], "persona": r["persona"], "kind": r["kind"], **b})
        per.append({"id": r["id"], "persona": r["persona"], "kind": r["kind"], "statuses": statuses,
                    "templates": [m["template_id"] for t in turns for m in t.get("messages", [])],
                    "cart_lines": sum(len(d["lines"]) for d in cart["dishes"]), "surfaces_checked": n, "violations": len(bad)})
    system = f"persona-compliance-{args.arm}" + ("-sensitivity" if args.sensitivity else "")
    status = "NOT RUN" if args.sensitivity else ("FAIL" if found else "PASS")
    if args.sensitivity:
        status = "PASS" if found else "FAIL"  # the checker must find violations when eligibility is off
    metrics = {"prompts": len(per), "surfaces_checked": checked, "violations": len(found),
               "by_kind": {k: sum(p["surfaces_checked"] for p in per if p["kind"] == k) for k in {p["kind"] for p in per}},
               "errors": [p["id"] for p in per if any(s >= 500 for s in p["statuses"])]}
    notes = ("eligibility switched off on purpose: PASS means the checker found violations (sensitivity check, not E7)"
             if args.sensitivity else "independent checker; zero tolerance; photo prompts use the labelled samples (C52)")
    save(make_result("E7", system, "persona_prompts_v1.jsonl", "all", metrics, per, found if not args.sensitivity else found[:50],
                     status, notes=notes), args.out, args.post_hoc)
    print(metrics, status)


if __name__ == "__main__":
    main()
