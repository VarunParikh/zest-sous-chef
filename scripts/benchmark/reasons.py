"""E13 reason-line quality (Evaluation Plan §4 E13, §4.15 C50 and C51; Agent Design A4).

`reasons_v1`: 10 mood prompts (P7, P6) × the 3 shown dishes = 30 suggestions. The 3 dishes come
from the mood path in code (retrieval, guardrails, levers, meal steering); for each, the A4 prompt
is called with the real model and the same facts and drivers the app uses, then the app's
validator decides whether the model's line or the template is shown. Metrics: validator pass
rate, template-fallback rate. Critical (C50, checked separately from the validator): a shown
reason with a price, stock, health claim or an ingredient not in the dish. 3 runs (C51).
Run: .venv/bin/python scripts/benchmark/reasons.py [--runs 3] [--out DIR]
"""
from _app import build, set_context
from _common import parser, rows, save

from backend.api.cart import context
from backend.evaluation.claims import shown_reason_problems
from backend.evaluation.results import load_thresholds, make_result
from backend.evaluation.runs import aggregate
from backend.evaluation.stats import proportion
from backend.flows.mood import DRIVERS, TEMPLATE_REASON, meal_for, steer, valid_reason
from backend.llm import prompts
from backend.llm.client import LLMError, OllamaClient
from backend.llm.schemas import ReasonResult


class _Req:
    def __init__(self, app):
        self.app = app


def main():
    ap = parser(__doc__)
    ap.add_argument("--runs", type=int, default=3)
    args = ap.parse_args()
    th = load_thresholds()["E13_reason_line"]
    data = rows("reasons_v1.jsonl", "all", False)[: (2 if args.smoke else None)]
    app, client = build(None)
    s, store = app.state.settings, app.state.store
    llm = OllamaClient(s.ollama_base_url, s.llm_model, s.timeout_llm_s, num_ctx=s.llm_num_ctx)
    personas = {f"P{i}": lv for i, lv in enumerate(app.state.presets.values(), 1)}
    runs, per, critical = [], [], []
    for run in range(1, args.runs + 1):
        rows_, crit = [], []
        for r in data:
            set_context(app, r["context_now"], r["context_weather"])
            ctx = context(_Req(app))
            sid = client.post("/api/v1/sessions", json={"levers": personas[r["persona"]].model_dump(mode="json")}).json()["session_id"]
            session = app.state.sessions.get(sid)
            meal = meal_for(r["text"], r["mood_tags"], ctx)
            query = " ".join([r["text"], *r["mood_tags"], *([meal] if meal else [])])
            rec = session.recommend_dishes(query, ctx, store, app.state.get_retriever(), display=15)
            for k, top in enumerate(steer(rec.shown, meal, store)[: r["cards"]], 1):
                dish = store.dish(top.candidate_id).dish
                drivers = [DRIVERS[c] for c, v in sorted(top.breakdown.contributions.items(), key=lambda kv: -kv[1]) if v > 0][:3]
                tags = [*dish.flavour, *dish.mood_tags][:5]
                facts = f"Suggestion: {dish.name} | Tags: {', '.join(tags)} | Drivers: {', '.join(drivers)}"
                try:
                    raw = llm.generate(prompts.text("reason_line"), facts, ReasonResult, call="reason").reason.strip().rstrip(".")
                except LLMError as e:
                    raw = f"<{type(e).__name__}>"
                valid = not raw.startswith("<") and valid_reason(raw, facts)
                shown = raw if valid else TEMPLATE_REASON
                terms = {store.lexicon.canonical(i.ingredient_name) or i.ingredient_name for i in store.dish(dish.dish_id).ingredients}
                problems = shown_reason_problems(shown, terms, store.lexicon)
                rows_.append({"id": f"{r['id']}-{k}", "run": run, "dish": dish.name, "raw": raw, "valid": valid, "shown": shown,
                              "problems_shown": problems, "problems_raw": shown_reason_problems(raw, terms, store.lexicon)})
                if problems:
                    crit.append({"id": f"{r['id']}-{k}", "run": run, "shown": shown, "problems": problems})
        n = len(rows_)
        runs.append({"validator_pass_rate": proportion(sum(x["valid"] for x in rows_), n),
                     "template_fallback_rate": proportion(sum(not x["valid"] for x in rows_), n)})
        per += rows_
        critical.append(crit)
    agg = aggregate([{"validator_pass_rate": x["validator_pass_rate"]["rate"]} for x in runs],
                    {"validator_pass_rate": ("min", th["validator_pass_rate_min"])}, critical)
    save(make_result("E13", f"reason-line-{s.llm_model}", "reasons_v1.jsonl", "all", {"runs": runs, "aggregate": agg["metrics"]},
                     per, [c for run in critical for c in run], agg["status"],
                     notes="facts and validator as in flows.mood; unsupported-claim check per C50; owner spot check of 20 lines "
                           "(Plan §8) still owed; 3 runs (C51)"), args.out, args.post_hoc)
    print(agg["status"], {k: (v["median"], v["range"]) for k, v in agg["metrics"].items()}, "critical:", agg["critical_runs"])


if __name__ == "__main__":
    main()
