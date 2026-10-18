"""E4 guard benchmark (Evaluation Plan §4 E4, §4.15 C46 and C51; ADR-006 v3).

Rerun after C40, C43 and C44 through the production pipeline: `InputGuard` with the rules and
`LlamaGuard` built from settings (model and `GUARD_IGNORE_CATEGORIES`), recording the
classifier's categories for every row. Systems: rules only; rules plus classifier (the gated,
pre-registered arm); and, supplementary and not gated, the full front gate (rules, classifier,
then the intent model's off_topic or unsafe redirect). Classifier arms run 3 times (C51).
"Blocked" = no action and a templated redirect (owner decision 2026-10-17). The first E4 files
(`E4-rules.json`, `E4-rules+llama-guard3_1b.json`) are kept; these carry the suffix `-adr006v3`.
Run: .venv/bin/python scripts/benchmark/guard.py [--split test] [--runs 3] [--smoke --out DIR]
"""
import time

import httpx
from _common import parser, rows, save

from backend.config import load_settings
from backend.evaluation.results import load_thresholds, make_result
from backend.evaluation.runs import aggregate
from backend.evaluation.stats import proportion
from backend.flows.chat import REDIRECT_INTENTS
from backend.guard import default_guard
from backend.guard.pipeline import InputGuard, LlamaGuard
from backend.intent.classify import classify
from backend.llm.client import LLMError, OllamaClient

ATTACKS = {"injection", "injection_via_transcript", "off_topic", "hazardous"}
CONTAMINATION = ("rules author saw test items G02 and G04 while checking the file format (disclosed 2026-10-18); the C43 rules "
                 "words came from owner hand-test phrases (dev item G27 'kill the heat' is one); the block 2.6 planning session "
                 "read all 40 rows and the first run's per-row outcomes, and no rule or prompt changed afterwards")


def installed(base: str) -> set[str]:
    try:
        return {m["name"] for m in httpx.get(f"{base}/api/tags", timeout=3).json().get("models", [])}
    except httpx.HTTPError:
        return set()


def one_run(system, data, rules, classifier, llm):
    per = []
    for g in data:
        t0 = time.perf_counter()
        source = "transcript" if g["category"] == "injection_via_transcript" else "user"
        s = rules.screen(g["text"], source=source)
        blocked, categories, intent = s.label != "ok" and s.message_id is not None, (), None
        layer = "rules" if blocked else None
        if not blocked and classifier is not None:
            try:
                blocked, categories = classifier.verdict(g["text"])
            except httpx.HTTPError as e:  # the production fallback: the rules result stands
                categories = (f"error:{type(e).__name__}",)
            layer = "classifier" if blocked else None
        if not blocked and system == "full-gate" and source == "user":
            try:
                intent = classify(llm, g["text"]).intent
            except LLMError as e:
                intent = f"error:{type(e).__name__}"
            blocked = intent in REDIRECT_INTENTS
            layer = "intent" if blocked else None
        per.append({"id": g["id"], "category": g["category"], "expected": g["expected"], "blocked": blocked, "layer": layer,
                    "rules_label": s.label, "classifier_categories": list(categories), "intent": intent,
                    "latency_ms": round((time.perf_counter() - t0) * 1000, 2)})
    attacks = [p for p in per if p["category"] in ATTACKS]
    benign = [p for p in per if p["category"] == "benign"]
    return per, proportion(sum(p["blocked"] for p in attacks), len(attacks)), proportion(sum(p["blocked"] for p in benign), len(benign))


def main():
    ap = parser(__doc__)
    ap.add_argument("--runs", type=int, default=3)
    args = ap.parse_args()
    settings, th = load_settings(), load_thresholds()["E4_guard"]
    data = rows("guard_v1.jsonl", args.split, args.smoke)
    split = "dev-smoke" if args.smoke else args.split
    available = settings.guard_model in installed(settings.ollama_base_url)
    classifier = LlamaGuard(settings.ollama_base_url, settings.guard_model, settings.timeout_llm_s,
                            ignore=frozenset(settings.guard_ignore_categories)) if available else None
    llm = OllamaClient(settings.ollama_base_url, settings.llm_model, settings.timeout_llm_s, num_ctx=settings.llm_num_ctx)
    rules = default_guard()
    gates = {"attack_block_rate": ("min", th["attack_block_rate_min"]), "false_positive_rate": ("max", th["false_positive_max"])}
    arms = [("rules", None, 1), (f"rules+{settings.guard_model}", classifier, args.runs), ("full-gate", classifier, args.runs)]
    for system, clf, runs in arms:
        name = f"{system}-adr006v3"
        if system != "rules" and clf is None:
            save(make_result("E4", name, "guard_v1.jsonl", split, {}, [], [], "NOT RUN",
                             notes=f"{settings.guard_model} not installed (download needs owner approval)"), args.out, args.post_hoc)
            continue
        results = [one_run(system, data, rules, clf, llm) for _ in range(runs)]
        agg = aggregate([{"attack_block_rate": b["rate"], "false_positive_rate": f["rate"]} for _, b, f in results], gates,
                        critical=[[] for _ in results])
        metrics = {"runs": [{"attack_block_rate": b, "false_positive_rate": f} for _, b, f in results], "aggregate": agg["metrics"],
                   "ignore_categories": sorted(settings.guard_ignore_categories)}
        status = agg["status"]
        per = [{**p, "run": i + 1} for i, (rows_, _, _) in enumerate(results) for p in rows_]
        notes = CONTAMINATION + "; end-to-end cart-change critical check runs in the E9 harness"
        if system == "full-gate":
            notes = "SUPPLEMENTARY, not gated (C46). " + notes
        save(make_result("E4", name, "guard_v1.jsonl", split, metrics, per, [], status, notes=notes), args.out, args.post_hoc)
        print(name, status, {k: (v["median"], v["range"]) for k, v in agg["metrics"].items()})


if __name__ == "__main__":
    main()
