"""E8 price and data integrity (Evaluation Plan §4 E8; FR-71, FR-76, FR-79, FR-80, FR-83).

200 seeded carts built through the API with a scripted model (no LLM needed for cart maths).
After every step: line, dish and cart totals recomputed from `skus.json`; packs re-derived by
brute force for the combined need of each variant; every rupee amount in a reply checked
against the cart and the cards of that turn; add-on card prices recomputed; substitution
deltas checked after the swap; checkout totals and idempotency checked. Pass rule: zero
mismatches. Run: .venv/bin/python scripts/benchmark/integrity.py [--carts N --out DIR]
"""
import json
import math
import random
import sys
from collections import Counter

from _app import build
from _common import ROOT, parser, save

sys.path.insert(0, str(ROOT))
from tests.acceptance.chat_harness import FakeOllama, intent  # noqa: E402

from backend.engine.eligibility import check_variant  # noqa: E402
from backend.evaluation.integrity import Pack, cart_mismatches, optimal_packs, rupees  # noqa: E402
from backend.evaluation.results import make_result  # noqa: E402

CONFIG = json.loads((ROOT / "eval/datasets/integrity_v1.json").read_text())
SKUS = json.loads((ROOT / "mock-data/generated/skus.json").read_text())
PRICE = {s["sku_id"]: s["price_inr"] for s in SKUS}
BY_VARIANT: dict[str, list[dict]] = {}
for s in SKUS:
    BY_VARIANT.setdefault(s["variant_id"], []).append(s)
BASE = {"g": ("g", 1), "kg": ("g", 1000), "ml": ("ml", 1), "l": ("ml", 1000), "piece": ("piece", 1), "bunch": ("bunch", 1)}
MOODS = [("I am feeling indulgent", ["indulgent"]), ("something comforting", ["comfort"]), ("something cooling", ["cooling"]),
         ("a light dinner", ["light"]), ("something spicy", ["spicy"]), ("something sweet", ["sweet"]),
         ("something festive", ["festive"]), ("a quick meal", ["quick"])]


class Run:
    def __init__(self, rng: random.Random):
        self.rng, self.fake = rng, FakeOllama()
        for text, tags in MOODS:
            self.fake.intents[text] = intent("mood_intent", mood_tags=tags)
        self.app, self.client = build(self.fake, CONFIG["context_now"], CONFIG["context_weather"])
        self.store = self.app.state.store
        self.dish_names = [d.dish.name.replace(" (international)", "") for d in self.store.dishes]
        for name in self.dish_names:
            self.fake.intents[f"I want to make {name}"] = intent("named_dish", dish_name=name.lower())
        self.mismatches, self.checks = [], Counter()

    # ---------- checks ----------
    def stock(self, sku: dict) -> int:
        return self.store.stock_override.get(sku["sku_id"], sku["stock_count"]) if sku["dark_store_ok"] else 0

    def check_packs(self, cart_id: str, session) -> None:
        groups: dict[str, list] = {}
        for ln in session.cart.lines():
            groups.setdefault(ln.variant_id, []).append(ln)
        for vid, lines in groups.items():
            unit = BASE[lines[0].need_unit.value][0]
            same = [ln for ln in lines if BASE[ln.need_unit.value][0] == unit]
            packs = [Pack(s["sku_id"], s["pack"]["qty"] * BASE[s["pack"]["unit"]][1], s["price_inr"], self.stock(s))
                     for s in BY_VARIANT.get(vid, []) if BASE[s["pack"]["unit"]][0] == unit]
            if not packs:
                self.checks["packs_not_rederivable"] += 1  # sold in another unit: one pack, flagged estimated
                continue
            need = sum(ln.need_qty * BASE[ln.need_unit.value][1] for ln in same)
            expected = optimal_packs(need, packs) or optimal_packs(need, packs, limit_by_stock=False)
            actual = Counter()
            for ln in same:
                for p in ln.packs:
                    actual[p.sku_id] += p.count // ln.quantity
            self.checks["pack_groups"] += 1
            if dict(actual) != expected:
                self.mismatches.append({"cart": cart_id, "kind": "packs", "variant_id": vid, "need": need,
                                        "shown": dict(actual), "expected": expected})

    def addon_basket(self, session, dish_name: str) -> int | None:
        rec = next(d for d in self.store.dishes if d.dish.name == dish_name)
        cart_terms = {ln.ingredient_name for ln in session.cart.lines()}
        total = 0
        for line in rec.ingredients:
            term = self.store.lexicon.canonical(line.ingredient_name) or line.ingredient_name
            if not line.essential or term in cart_terms:
                continue
            unit, factor = BASE[line.unit.value]
            costs = []
            for v in self.store.variants_for(line.ingredient_name):
                if not check_variant(v, session.snapshot, self.store).eligible:
                    continue
                for s in BY_VARIANT.get(v.variant_id, []):
                    if session.snapshot.business.stock_filter and self.stock(s) <= 0:
                        continue
                    p_unit, p_factor = BASE[s["pack"]["unit"]]
                    n = math.ceil(line.qty * factor / (s["pack"]["qty"] * p_factor)) if p_unit == unit else 1
                    costs.append(s["price_inr"] * max(1, n))
            if not costs:
                return None
            total += min(costs)
        return total

    def check_turn(self, cart_id: str, sid: str, turn: dict | None) -> None:
        session = self.app.state.sessions.get(sid)
        view = self.client.get(f"/api/v1/sessions/{sid}/cart").json()
        for m in cart_mismatches(view, PRICE):
            self.mismatches.append({"cart": cart_id, **m})
        self.checks["cart_views"] += 1
        self.check_packs(cart_id, session)
        if not turn:
            return
        allowed = {view["subtotal_inr"], *(d["dish_total_inr"] for d in view["dishes"])}
        for msg in turn.get("messages", []):
            for card in msg.get("cards", []):
                if card.get("type") == "addon_suggestion":
                    price = card["item"]["price_inr"]
                    allowed.add(price)
                    expected = self.addon_basket(session, card["item"]["name"])
                    self.checks["addon_prices"] += 1
                    if expected is not None and price != expected:
                        self.mismatches.append({"cart": cart_id, "kind": "addon_price", "item": card["item"]["name"],
                                                "shown": price, "expected": expected})
                if card.get("type") == "dish_added":
                    allowed.add(card["dish_total_inr"])
            if msg["role"] != "assistant":
                continue
            for amount in rupees(msg["text"]):
                self.checks["reply_amounts"] += 1
                if amount not in allowed:
                    self.mismatches.append({"cart": cart_id, "kind": "reply_amount", "template": msg.get("template_id"),
                                            "shown": amount, "allowed": sorted(allowed)})

    # ---------- actions ----------
    def chat(self, sid, text):
        return self.client.post(f"/api/v1/sessions/{sid}/chat", json={"text": text}).json()

    def act(self, sid, type_, **payload):
        r = self.client.post(f"/api/v1/sessions/{sid}/action", json={"type": type_, "payload": payload})
        return r.json() if r.status_code == 200 else None

    def cards(self, turn, kind):
        return [c for m in (turn or {}).get("messages", []) for c in m.get("cards", []) if c.get("type") == kind]

    def one_cart(self, n: int) -> list[str]:
        rng, cart_id = self.rng, f"cart{n:03d}"
        persona = rng.choice(sorted(self.app.state.presets))
        levers = self.app.state.presets[persona].model_dump(mode="json")
        sid = self.client.post("/api/v1/sessions", json={"levers": levers}).json()["session_id"]
        self.store.stock_override.clear()
        last, done = None, []
        for _ in range(rng.randint(*CONFIG["actions_per_cart"])):
            session = self.app.state.sessions.get(sid)
            lines = session.cart.lines()
            options = ["mood_add", "named_add"]
            if self.cards(last, "addon_suggestion"):
                options.append("addon_add")
            if lines:
                options += ["quantity", "swap_variant", "remove_line", "remove_dish", "substitute", "checkout"]
            if self.cards(last, "swap_options"):
                options.append("swap_dish")
            if session.undo_stack:
                options.append("undo")
            action = rng.choice(options)
            done.append(action)
            turn = None
            if action == "mood_add":
                turn = self.chat(sid, rng.choice(MOODS)[0])
            elif action == "named_add":
                turn = self.chat(sid, f"I want to make {rng.choice(self.dish_names)}")
                for c in self.cards(turn, "confirm"):
                    if any(o["value"] == "add" for o in c["options"]):
                        turn = self.act(sid, "confirm", confirm_id=c["confirm_id"], choice="add") or turn
            elif action == "addon_add":
                turn = self.act(sid, "add_on", suggestion_id=self.cards(last, "addon_suggestion")[0]["suggestion_id"], choice="add")
            elif action == "swap_dish":
                c = self.cards(last, "swap_options")[0]
                if c["options"]:
                    turn = self.act(sid, "swap", suggestion_id=c["suggestion_id"], alt_dish_id=rng.choice(c["options"])["dish_id"])
            elif action == "undo":
                turn = self.act(sid, "undo", suggestion_id=session.undo_stack[-1]["suggestion_id"])
            elif action == "quantity":
                ln = rng.choice(lines)
                self.client.patch(f"/api/v1/sessions/{sid}/cart/lines/{ln.line_id}", json={"quantity": rng.randint(1, 9)})
            elif action == "swap_variant":
                ln = rng.choice(lines)
                if ln.alternative_variant_ids:
                    self.client.patch(f"/api/v1/sessions/{sid}/cart/lines/{ln.line_id}",
                                      json={"variant_id": rng.choice(ln.alternative_variant_ids)})
            elif action == "remove_line":
                self.client.delete(f"/api/v1/sessions/{sid}/cart/lines/{rng.choice(lines).line_id}")
            elif action == "remove_dish":
                self.client.delete(f"/api/v1/sessions/{sid}/cart/dishes/{rng.choice(session.cart.dishes).cart_dish_id}")
            elif action == "substitute":
                ln = rng.choice([x for x in lines if x.priced] or lines)
                for s in BY_VARIANT.get(ln.variant_id, []):
                    self.store.stock_override[s["sku_id"]] = 0
                r = self.client.post(f"/api/v1/sessions/{sid}/checkout", headers={"Idempotency-Key": f"{cart_id}-sub-{len(done)}"})
                subs = r.json().get("details", {}).get("substitutions", []) if r.status_code == 409 else []
                if subs:
                    before = self.client.get(f"/api/v1/sessions/{sid}/cart").json()["subtotal_inr"]
                    turn = self.act(sid, "substitute", substitution_id=subs[0]["substitution_id"], choice="accept")
                    if turn is not None:
                        after = self.client.get(f"/api/v1/sessions/{sid}/cart").json()["subtotal_inr"]
                        self.checks["substitution_deltas"] += 1
                        if after - before != subs[0]["price_delta_inr"]:
                            self.mismatches.append({"cart": cart_id, "kind": "substitution_delta",
                                                    "shown": subs[0]["price_delta_inr"], "expected": after - before})
            elif action == "checkout":
                view = self.client.get(f"/api/v1/sessions/{sid}/cart").json()
                key = f"{cart_id}-buy-{len(done)}"
                r = self.client.post(f"/api/v1/sessions/{sid}/checkout", headers={"Idempotency-Key": key})
                if r.status_code == 200:
                    self.checks["orders"] += 1
                    order = r.json()
                    if order["subtotal_inr"] != view["subtotal_inr"]:
                        self.mismatches.append({"cart": cart_id, "kind": "order_total", "shown": order["subtotal_inr"],
                                                "expected": view["subtotal_inr"]})
                    again = self.client.post(f"/api/v1/sessions/{sid}/checkout", headers={"Idempotency-Key": key}).json()
                    if again.get("order_id") != order["order_id"]:
                        self.mismatches.append({"cart": cart_id, "kind": "idempotency", "first": order["order_id"],
                                                "second": again.get("order_id")})
            self.check_turn(cart_id, sid, turn)
            last = turn if turn is not None else last
        self.store.stock_override.clear()
        return done


def main():
    ap = parser(__doc__)
    ap.add_argument("--carts", type=int, default=CONFIG["carts"])
    args = ap.parse_args()
    run = Run(random.Random(CONFIG["seed"]))
    per = []
    for n in range(args.carts):
        before = len(run.mismatches)
        actions = run.one_cart(n)
        per.append({"id": f"cart{n:03d}", "actions": actions, "mismatches": len(run.mismatches) - before})
    actions = Counter(a for p in per for a in p["actions"])
    metrics = {"carts": args.carts, "mismatches": len(run.mismatches), "checks": dict(run.checks),
               "actions": dict(actions)}
    status = "PASS" if not run.mismatches else "FAIL"
    save(make_result("E8", "api-integrity", "integrity_v1.json", "all", metrics, per, run.mismatches[:200], status,
                     notes="scripted model; packs re-derived by brute force; validators V1 to V14 reported from `make data` "
                           "separately"), args.out)
    print(json.dumps(metrics, indent=1))


if __name__ == "__main__":
    main()
