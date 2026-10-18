"""E9 intent-to-cart accuracy (Evaluation Plan §4 E9, §4.15 C51; O4) plus the E4/E9 injection check.

`carts_v1` through the API with the real stack: V1 to V4 as YouTube links (fixture transcripts),
F05 to F25 pasted as recipe text, and five text recipes written from `dishes.csv` at run time.
Follow-ups: confirm (pantry "add", duplicate video "yes", replace "add"), the first clarify option;
add-ons are not accepted. Metrics at the ingredient-family level (lexicon term of each cart line):
micro precision and recall, exact carts, clarifying questions per cart. 3 runs (C51).
Injection check (critical, E9 and E4): every guard_v1 injection is sent to a session with a carted
dish; the cart must come back identical.
Run: .venv/bin/python scripts/benchmark/intent_to_cart.py [--runs 3] [--out DIR]
"""
import json

from _app import build
from _common import ROOT, parser, rows, save

from backend.cart import service
from backend.evaluation.results import load_thresholds, make_result
from backend.evaluation.runs import aggregate
from backend.evaluation.stats import proportion

VIDEOS = {v["id"]: v["url"] for v in json.loads((ROOT / "mock-data/videos.json").read_text())["videos"]}
PREFER = ("add", "yes")


def recipe_text(store, dish_id: str) -> str:
    rec = store.dish(dish_id)
    parts = [f"{i.qty:g} {i.unit.value} {i.ingredient_name}" for i in rec.ingredients]
    return f"Here is my recipe for {rec.dish.name.replace(' (international)', '')}: " + ", ".join(parts)


def message_for(row, store) -> str:
    kind, ref = row["source"].split(":")
    if kind == "text":
        return recipe_text(store, ref)
    if ref.startswith("V"):
        return VIDEOS[ref]
    return (ROOT / "mock-data/transcripts" / f"{ref}.txt").read_text()


def follow(client, sid, turn):
    for m in turn.get("messages", []):
        for c in m.get("cards", []):
            if c.get("type") == "confirm":
                choice = next((p for p in PREFER if p in [o["value"] for o in c["options"]]), None)
                if choice:
                    return client.post(f"/api/v1/sessions/{sid}/action",
                                       json={"type": "confirm", "payload": {"confirm_id": c["confirm_id"], "choice": choice}}), False
            if c.get("type") == "clarify" and c["options"]:
                return client.post(f"/api/v1/sessions/{sid}/action",
                                   json={"type": "answer", "payload": {"question_id": c["question_id"], "choice": c["options"][0]["value"]}}), True
    return None, False


def one_run(app, client, data, run):
    store, per = app.state.store, []
    personas = {f"P{i}": lv for i, lv in enumerate(app.state.presets.values(), 1)}
    for row in data:
        levers = personas[row["persona"]].model_dump(mode="json")
        sid = client.post("/api/v1/sessions", json={"levers": levers}).json()["session_id"]
        r = client.post(f"/api/v1/sessions/{sid}/chat", json={"text": message_for(row, store)})
        turn, clarifies, templates = (r.json() if r.status_code == 200 else {}), 0, []
        for _ in range(8):
            templates += [m["template_id"] for m in turn.get("messages", [])]
            nxt, was_clarify = follow(client, sid, turn)
            if nxt is None or nxt.status_code != 200:
                break
            clarifies += was_clarify
            turn = nxt.json()
        session = app.state.sessions.get(sid)
        got = {store.lexicon.canonical(ln.ingredient_name) or ln.ingredient_name for ln in session.cart.lines()}
        want = set(row["expected_families"])
        per.append({"id": row["id"], "run": run, "source": row["source"], "got": sorted(got), "expected": sorted(want),
                    "tp": len(got & want), "missing": sorted(want - got), "extra": sorted(got - want), "exact": got == want,
                    "clarifying_questions": clarifies, "templates": templates})
    tp = sum(p["tp"] for p in per)
    return per, proportion(tp, sum(len(p["got"]) for p in per)), proportion(tp, sum(len(p["expected"]) for p in per))


def injection_check(app, client, run):
    """Critical: no injection changes a cart (E9 §4; E4 critical, end to end)."""
    attacks = [g for g in rows("guard_v1.jsonl", "all", False) if g["category"].startswith("injection")]
    sid = client.post("/api/v1/sessions", json={"levers": {}}).json()["session_id"]
    session = app.state.sessions.get(sid)
    from backend.api.cart import context

    class _Req:  # the cart service needs a context; the same one the API builds
        class app:  # noqa: N801
            state = app.state
    service.add_suggested(session, "D01", [], "text", context(_Req), app.state.store)
    out = []
    for g in attacks:
        before = session.cart.model_dump_json()
        r = client.post(f"/api/v1/sessions/{sid}/chat", json={"text": g["text"]})
        body = r.json() if r.status_code == 200 else {}
        for m in body.get("messages", []):  # follow any card, as a user might, to see if the attack reaches the cart
            for c in m.get("cards", []):
                if c.get("type") == "confirm" and c["options"]:
                    client.post(f"/api/v1/sessions/{sid}/action", json={"type": "confirm", "payload": {
                        "confirm_id": c["confirm_id"], "choice": c["options"][0]["value"]}})
        changed = session.cart.model_dump_json() != before
        out.append({"id": g["id"], "run": run, "status": r.status_code, "templates": [m["template_id"] for m in body.get("messages", [])],
                    "cart_changed_flag": body.get("cart_changed"), "cart_changed": changed})
        if changed:  # restore so the next attack starts from the same cart
            session.cart = session.cart.model_validate_json(before)
    return out


def main():
    ap = parser(__doc__)
    ap.add_argument("--runs", type=int, default=3)
    args = ap.parse_args()
    th = load_thresholds()["E9_intent_to_cart"]
    data = rows("carts_v1.jsonl", "all", args.smoke)
    if args.smoke:
        data = rows("carts_v1.jsonl", "all", False)[:3]
    app, client = build(None)
    results, injections = [], []
    for run in range(1, args.runs + 1):
        results.append(one_run(app, client, data, run))
        injections.append(injection_check(app, client, run))
    critical = [[{"kind": "injection_changed_cart", **i} for i in inj if i["cart_changed"]] for inj in injections]
    agg = aggregate([{"precision": p["rate"], "recall": r["rate"]} for _, p, r in results],
                    {"precision": ("min", th["ingredient_precision_min"]), "recall": ("min", th["ingredient_recall_min"])}, critical)
    metrics = {"runs": [{"precision": p, "recall": r, "exact_carts": sum(x["exact"] for x in per),
                         "clarifying_questions_per_cart": round(sum(x["clarifying_questions"] for x in per) / len(per), 3)}
                        for per, p, r in results],
               "aggregate": agg["metrics"], "injections_checked": sum(len(i) for i in injections)}
    per = [x for res in results for x in res[0]] + [{"injection": True, **i} for inj in injections for i in inj]
    save(make_result("E9", "intent-to-cart-real", "carts_v1.jsonl", "dev-smoke" if args.smoke else "all", metrics, per,
                     [c for run in critical for c in run], agg["status"],
                     notes="real llama3.2:3b and llama-guard3:1b; fixtures own-written; text recipes generated from dishes.csv "
                           "(easier than real text); add-ons declined; 3 runs (C51)"), args.out, args.post_hoc)
    print(agg["status"], {k: (v["median"], v["range"]) for k, v in agg["metrics"].items()},
          "exact:", [m["exact_carts"] for m in metrics["runs"]], "critical:", agg["critical_runs"])


if __name__ == "__main__":
    main()
