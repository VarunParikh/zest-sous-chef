"""E6 lever sensitivity (Evaluation Plan §4 E6, §4.15 C47 and C48; O1; FR-40, FR-61).

Each `levers_v1` prompt runs through the API in a fresh session for the baseline levers (the
Settings Panel defaults) and for each of the 18 groups moved to its contrast (C47), with the
row's scripted intent, pinned context and stock-outs, and the real retrieval stack. The top 3
come from the inspector: the dish suggestions, or for add-on rows the add-on list. Group
applicability is computed on the baseline pool before any top 3 is compared. Also: Kendall
distance over the pool ranking, a random re-ranker baseline, and the 11-persona overlap matrix.
Run: .venv/bin/python scripts/benchmark/levers.py [--split test|dev] [--out DIR]
"""
import random
import sys
from itertools import combinations
from statistics import mean

from _app import build, set_context
from _common import ROOT, parser, rows, save

sys.path.insert(0, str(ROOT))
from tests.acceptance.chat_harness import FakeOllama, intent  # noqa: E402

from backend.engine.context import build_context, load_trends, matching_trends  # noqa: E402
from backend.engine.eligibility import check_dish  # noqa: E402
from backend.engine.features import history_buckets, premium_level  # noqa: E402
from backend.evaluation.lever_sensitivity import (CONTRASTS, apply_contrast, divergence, group_status,  # noqa: E402
                                                   kendall_distance, random_rdi)
from backend.evaluation.results import make_result  # noqa: E402
from backend.session.levers import LeverSet  # noqa: E402

BASE = LeverSet()
WEIGHT_COMPONENT = {"w_pairing": "s_p", "w_history": "s_h", "w_trend": "s_t", "w_gourmet": "s_g"}
TREND_GROUP = {"t_weekend": "indulgence", "t_cooling": "cooling"}
FILTERS = {"diet", "faith", "specialised", "addon_cap", "stock_filter"}


class Runner:
    def __init__(self):
        self.fake = FakeOllama()
        self.app, self.client = build(self.fake)
        self.store = self.app.state.store

    def prepare(self, row):
        self.fake.intents[row["text"]] = intent(row["intent"]["intent"], mood_tags=row["intent"]["mood_tags"],
                                                dish_name=row["intent"]["dish_name"])
        set_context(self.app, row["context_now"], row["context_weather"])
        self.store.stock_override.clear()
        for term in row["stock_out_terms"]:
            for v in self.store.variants_for(term):
                for s in self.store.skus_for(v.variant_id):
                    self.store.stock_override[s.sku_id] = 0

    def run(self, row, levers: LeverSet) -> dict:
        sid = self.client.post("/api/v1/sessions", json={"levers": levers.model_dump(mode="json")}).json()["session_id"]
        self.client.post(f"/api/v1/sessions/{sid}/chat", json={"text": row["text"]})
        insp = self.client.get(f"/api/v1/sessions/{sid}/inspector").json()
        part = insp.get("addon", {"rows": [], "shown": []}) if row["type"] == "addon" else insp
        ranked = sorted((r for r in part["rows"] if r["eligible"]),
                        key=lambda r: (-round(r["final"], 12), -r["components"]["s_p"], r["candidate_id"]))
        session = self.app.state.sessions.get(sid)
        return {"top3": part["shown"][:3], "ranking": [r["candidate_id"] for r in ranked], "rows": part["rows"],
                "cart_terms": frozenset(ln.ingredient_name for ln in session.cart.lines())}


def applicable(group: str, row, base: dict, store, ctx) -> bool:
    """C47: computed on the baseline pool, before any top 3 is compared."""
    eligible = [r for r in base["rows"] if r["eligible"]]
    kind = "addon" if row["type"] == "addon" else "dish"
    if group in WEIGHT_COMPONENT:
        return len({round(r["components"][WEIGHT_COMPONENT[group]], 9) for r in eligible}) > 1
    if group == "gourmet":
        return len({round(premium_level(store.dish(r["candidate_id"]), store), 9) for r in eligible}) > 1
    if group == "organic":
        return False  # no dish-level organic feature (C24: organic acts on variants only; E12 measures it)
    if group.startswith("h_"):
        has = [group[2:] in history_buckets(store.dish(r["candidate_id"]), store) for r in eligible]
        return any(has) and not all(has)
    if group in TREND_GROUP:
        trends = load_trends()
        has = [any(t["group"] == TREND_GROUP[group] and t["multiplier"] != 1
                   for t in matching_trends(store.dish(r["candidate_id"]), ctx, trends)) for r in eligible]
        return any(has) and not all(has)
    if group == "stock_filter":
        return any(not r["eligible"] and r["filtered_by"] == ["stock"] for r in base["rows"])
    changed = apply_contrast(BASE, group)
    return any(not check_dish(store.dish(r["candidate_id"]), changed, store, kind=kind, cart_terms=base["cart_terms"]).eligible
               for r in eligible)


def simulated_random(base: dict, rng: random.Random, draws: int = 1000) -> float:
    pool = base["ranking"]
    if len(pool) <= 3:
        return 0.0
    return mean(divergence(base["top3"], rng.sample(pool, 3)) for _ in range(draws))


def main():
    args = parser(__doc__).parse_args()
    data = rows("levers_v1.jsonl", args.split, args.smoke)
    split = "dev-smoke" if args.smoke else args.split
    r = Runner()
    rng = random.Random(20261018)
    per, by_group = [], {g: [] for g in CONTRASTS}
    baselines = {}
    for row in data:
        r.prepare(row)
        ctx = build_context(settings=r.app.state.settings)
        base = r.run(row, BASE)
        baselines[row["id"]] = base
        n_eligible = len(base["ranking"])
        rec = {"id": row["id"], "type": row["type"], "base_top3": base["top3"], "eligible_pool": n_eligible,
               "random_rdi_expected": random_rdi(n_eligible), "random_rdi_simulated": round(simulated_random(base, rng), 4),
               "groups": {}}
        for g in CONTRASTS:
            app_ = applicable(g, row, base, r.store, ctx)
            changed = r.run(row, apply_contrast(BASE, g))
            d = divergence(base["top3"], changed["top3"])
            rec["groups"][g] = {"applicable": app_, "top3": changed["top3"], "divergence": round(d, 4),
                                "kendall": kendall_distance(base["ranking"], changed["ranking"]),
                                "pool_removed": len(base["ranking"]) - len([x for x in changed["ranking"] if x in base["ranking"]])}
            if app_:
                by_group[g].append((row, d, rec))
        per.append(rec)
    groups, critical = {}, []
    for g, items in by_group.items():
        values = [d for _, d, _ in items]
        status, crit = group_status(values)
        types = {}
        for row, d, _ in items:
            types.setdefault(row["type"], []).append(d)
        groups[g] = {"rdi": round(mean(values), 4) if values else None, "applicable": len(values),
                     "changed": sum(d > 0 for d in values), "status": status,
                     "by_type": {t: round(mean(v), 4) for t, v in types.items()},
                     "random_rdi_expected": round(mean(rec["random_rdi_expected"] for _, _, rec in items), 4) if items else None,
                     "random_rdi_simulated": round(mean(rec["random_rdi_simulated"] for _, _, rec in items), 4) if items else None,
                     "kendall_mean": round(mean(k for _, _, rec in items if (k := rec["groups"][g]["kendall"]) is not None), 4)
                     if any(rec["groups"][g]["kendall"] is not None for _, _, rec in items) else None,
                     "excluded_prompts": [p["id"] for p in per if not p["groups"][g]["applicable"]],
                     "zero_prompts": [row["id"] for row, d, _ in items if d == 0]}
        if crit:
            critical.append({"group": g, "rdi": 0, "prompts": [row["id"] for row, _, _ in items]})
    # persona contrast: the 11 presets on the same prompts
    names = list(r.app.state.presets)
    persona_top = {}
    for name in names:
        persona_top[name] = {}
        for row in data:
            r.prepare(row)
            persona_top[name][row["id"]] = r.run(row, r.app.state.presets[name])["top3"]
    overlap = {f"{a} | {b}": round(mean(len(set(persona_top[a][p]) & set(persona_top[b][p])) / 3 for p in persona_top[a]), 4)
               for a, b in combinations(names, 2)}
    r.store.stock_override.clear()
    statuses = [v["status"] for v in groups.values()]
    status = "FAIL" if critical or "FAIL" in statuses else ("INCONCLUSIVE" if "INCONCLUSIVE" in statuses else "PASS")
    metrics = {"groups": groups, "persona_overlap_top3": overlap, "personas": names,
               "under_exercised": [g for g, v in groups.items() if v["status"] == "INCONCLUSIVE"]}
    save(make_result("E6", f"lever-sensitivity-{split}", "levers_v1.jsonl", split, metrics,
                     per + [{"id": "persona_top3", "top3": persona_top}], critical, status,
                     notes="scripted intent, real hybrid retrieval and engine through the API; fresh session per run; "
                           "applicability computed on the baseline pool before comparison (C47)"), args.out, args.post_hoc)
    for g, v in groups.items():
        print(f"{g:13s} {v['status']:12s} rdi={v['rdi']} n={v['applicable']} random={v['random_rdi_expected']} zero={v['zero_prompts']}")
    print("overall:", status)


if __name__ == "__main__":
    main()
