"""E2 intent classification (Evaluation Plan §4 E2, §4.15 C49 and C51; FR-11; Agent Design A2).

`utterances_v1` test split through the production `classify` (prompt `intent_classify_v2`,
llama3.2:3b), 3 runs. Metrics: accuracy, per-intent confusion matrix, false `unsafe` rate on
utterances whose label is not `unsafe`. Critical: an `unsafe` (injection) utterance labelled
with a cart-changing intent (C49). Supplementary: the routed label after the guard (a guard
block counts as `off_topic` for an off-topic redirect, else `unsafe`), and the shipped path (C54 code routing, then the model), both not gated.
Run: .venv/bin/python scripts/benchmark/intent.py [--split test] [--runs 3] [--smoke --out DIR]
"""
from collections import Counter

from _common import parser, rows, save

from backend.config import load_settings
from backend.evaluation.results import load_thresholds, make_result
from backend.evaluation.runs import aggregate
from backend.evaluation.stats import proportion
from backend.guard import default_guard
from backend.guard.pipeline import InputGuard, LlamaGuard
from backend.catalogue.store import load_store
from backend.intent.classify import classify
from backend.intent.routing import route
from backend.llm.client import LLMError, OllamaClient
from backend.llm.prompts import version

CART_CHANGING = {"cart_edit", "cart_clear_or_replace", "variant_request"}  # C49


def main():
    ap = parser(__doc__)
    ap.add_argument("--runs", type=int, default=3)
    args = ap.parse_args()
    s, th = load_settings(), load_thresholds()["E2_intent"]
    data = rows("utterances_v1.jsonl", args.split, args.smoke)
    split = "dev-smoke" if args.smoke else args.split
    llm = OllamaClient(s.ollama_base_url, s.llm_model, s.timeout_llm_s, num_ctx=s.llm_num_ctx)
    guard = InputGuard(default_guard(), LlamaGuard(s.ollama_base_url, s.guard_model, s.timeout_llm_s,
                                                   ignore=frozenset(s.guard_ignore_categories),
                                                   ignore_if_link=frozenset(s.guard_ignore_if_link)))
    runs, per, critical = [], [], []
    store = load_store()
    for run in range(1, args.runs + 1):
        crit, rows_ = [], []
        for u in data:
            try:
                got = classify(llm, u["text"]).intent
            except LLMError as e:
                got = f"error:{type(e).__name__}"
            v = guard.check(u["text"])
            blocked_as = ("off_topic" if v.label == "off_topic" else "unsafe") if v.blocked else None  # a guard redirect
            routed = blocked_as or got
            coded = route(u["text"], store)
            shipped = blocked_as or (coded.intent if coded else got)
            rows_.append({"id": u["id"], "run": run, "expected": u["intent"], "got": got, "routed": routed,
                          "shipped": shipped, "code_routed": coded is not None,
                          "near_miss": u.get("near_miss", False), "correct": got == u["intent"]})
            if u["intent"] == "unsafe" and got in CART_CHANGING:
                crit.append({"id": u["id"], "run": run, "got": got})
        benign = [r for r in rows_ if r["expected"] != "unsafe"]
        acc = proportion(sum(r["correct"] for r in rows_), len(rows_))
        fu = proportion(sum(r["got"] == "unsafe" for r in benign), len(benign))
        routed_acc = proportion(sum(r["routed"] == r["expected"] for r in rows_), len(rows_))
        shipped_acc = proportion(sum(r["shipped"] == r["expected"] for r in rows_), len(rows_))
        runs.append({"accuracy": acc, "false_unsafe_rate": fu, "routed_accuracy_supplementary": routed_acc,
                     "shipped_path_accuracy_supplementary": shipped_acc,
                     "confusion": {f"{e} -> {g}": n for (e, g), n in Counter((r["expected"], r["got"]) for r in rows_).items()}})
        per += rows_
        critical.append(crit)
    agg = aggregate([{"accuracy": r["accuracy"]["rate"], "false_unsafe_rate": r["false_unsafe_rate"]["rate"]} for r in runs],
                    {"accuracy": ("min", th["accuracy_min"]), "false_unsafe_rate": ("max", th["false_unsafe_max"])}, critical)
    metrics = {"runs": runs, "aggregate": agg["metrics"], "prompt": version("intent_classify"), "model": s.llm_model}
    save(make_result("E2", f"intent-{s.llm_model}", "utterances_v1.jsonl", split, metrics, per, [c for r in critical for c in r],
                     agg["status"], notes="intent prompt v2 examples overlap the dev split only (U15, exact match); no test "
                     "overlap; 3 runs (C51)"), args.out, args.post_hoc)
    print(agg["status"], {k: (v["median"], v["range"]) for k, v in agg["metrics"].items()}, "critical:", agg["critical_runs"])


if __name__ == "__main__":
    main()
