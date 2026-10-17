"""E1 text-model benchmark (Evaluation Plan §4 E1; ADR-002). Models must already be
installed in Ollama; a missing model is reported NOT RUN and is never pulled here.
Metrics: ingredient F1 after synonym resolution, quantity accuracy, schema-valid rate
(after one retry), invention rate (critical above 10%), latency and time to first
token from Ollama's own timings, memory from `ollama ps`, free RAM with Chroma loaded.
Run: .venv/bin/python scripts/benchmark/text_models.py --models a,b [--split test] [--smoke --out DIR]
"""
import re
import subprocess
import time

import httpx
from _common import parser, rows, save

from backend.catalogue.seed import load_lexicon, load_synonyms
from backend.config import load_settings
from backend.evaluation.metrics import f1
from backend.evaluation.results import gate_status, load_thresholds, make_result, overall_status
from backend.evaluation.stats import proportion
from backend.llm.client import LLMError, OllamaClient
from backend.llm.prompts import render, version
from backend.llm.schemas import ExtractionResult
from backend.retrieval.text import doc_tokens

UNIT_G = {"kg": 1000, "g": 1}
UNIT_ML = {"l": 1000, "ml": 1}


def canon(name: str, lex, syn: dict) -> str:
    n = name.strip().lower()
    return lex.canonical(syn.get(n, n)) or syn.get(n, n)


def norm_qty(qty, unit):
    if qty is None:
        return None, unit
    if unit in UNIT_G:
        return qty * UNIT_G[unit], "g"
    if unit in UNIT_ML:
        return qty * UNIT_ML[unit], "ml"
    return qty, unit


def free_ram_gb() -> float:
    out = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
    pages = sum(int(re.search(r"(\d+)", line.split(":")[1]).group(1)) for line in out.splitlines()
                if line.startswith(("Pages free", "Pages inactive", "Pages speculative")))
    return round(pages * 16384 / 2**30, 2)


def main():
    ap = parser(__doc__)
    ap.add_argument("--models", required=True)
    args = ap.parse_args()
    settings, th = load_settings(), load_thresholds()["E1_text_model"]
    lex = load_lexicon()
    syn = {s["query_term"].lower(): s["maps_to"] for s in load_synonyms() if s["type"] == "ingredient"}
    data = rows("recipes_v1.jsonl", args.split, args.smoke)
    split = "dev-smoke" if args.smoke else args.split
    tags = {m["name"] for m in httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=3).json().get("models", [])}
    from backend.catalogue.store import load_store
    from backend.retrieval.embedder import default_embedder
    from backend.retrieval.vector import VectorStore
    VectorStore(settings.resolve(settings.chroma_path), default_embedder(settings)).ensure(load_store())  # Chroma loaded, as in the app
    for model in args.models.split(","):
        if model not in tags:
            save(make_result("E1", model, "recipes_v1.jsonl", split, {}, [], [], "NOT RUN",
                             notes="model not installed (download needs owner approval)"), args.out)
            continue
        client = OllamaClient(settings.ollama_base_url, model, timeout_s=settings.timeout_llm_s)
        per, invented, predicted_total, valid = [], 0, 0, 0
        for r in data:
            system, user = render("recipe_extract", r["text"])
            t0 = time.perf_counter()
            try:
                out = client.generate(system, user, ExtractionResult)
                ok = True
            except LLMError as e:
                out, ok = None, False
                err = str(e)[:120]
            wall = (time.perf_counter() - t0) * 1000
            valid += ok
            exp = {canon(x["name"], lex, syn): norm_qty(x.get("qty"), x.get("unit")) for x in r["expected"]}
            got = {canon(x.name, lex, syn): norm_qty(x.qty, x.unit) for x in (out.ingredients if out else [])}
            text_tokens = set(doc_tokens(r["text"]))
            inv = [n for n, item in zip(got, out.ingredients if out else []) if not set(doc_tokens(item.name)) & text_tokens]
            invented += len(inv)
            predicted_total += len(got)
            matched = set(got) & set(exp)
            qty_ok = sum(1 for n in matched if exp[n][0] is not None and got[n][0] is not None
                         and exp[n][1] == got[n][1] and abs(got[n][0] - exp[n][0]) <= 0.05 * exp[n][0])
            qty_n = sum(1 for n in matched if exp[n][0] is not None)
            per.append({"id": r["id"], "kind": r["kind"], "schema_valid": ok, "f1": round(f1(set(got), set(exp)), 4),
                        "qty_correct": qty_ok, "qty_total": qty_n, "invented": inv, "wall_ms": round(wall, 1),
                        **({"error": err} if not ok else {}), **client.last_stats})
        n = len(per)
        ps = subprocess.run(["ollama", "ps"], capture_output=True, text=True).stdout
        mean_f1 = round(sum(p["f1"] for p in per) / n, 4) if n else None
        lat = sorted(p["wall_ms"] for p in per)
        metrics = {"extraction_f1_mean": mean_f1, "schema_valid": proportion(valid, n),
                   "quantity_accuracy": proportion(sum(p["qty_correct"] for p in per), sum(p["qty_total"] for p in per)),
                   "invention_rate": proportion(invented, predicted_total),
                   "latency_ms_median": lat[n // 2] if n else None, "latency_ms_p95": lat[min(n - 1, int(0.95 * n))] if n else None,
                   "free_ram_gb_after": free_ram_gb(), "ollama_ps": ps.strip(), "prompt_version": version("recipe_extract")}
        gates = {"schema_valid": gate_status(metrics["schema_valid"], minimum=th["schema_valid_min"]),
                 "free_ram": {"status": "PASS" if metrics["free_ram_gb_after"] >= th["free_ram_gb_min"] else "FAIL"}}
        gates["extraction_f1"] = {"status": "NOT RUN" if mean_f1 is None else ("PASS" if mean_f1 >= th["extraction_f1_min"] else "FAIL")}
        crit = [{"invention_rate_above_10pct": metrics["invention_rate"]}] if (metrics["invention_rate"]["rate"] or 0) > 0.10 else []
        status = overall_status(gates, crit)
        save(make_result("E1", model, "recipes_v1.jsonl", split, {**metrics, "gates": gates, "f1_gate_min": th["extraction_f1_min"]},
                         per, crit, status, notes="smoke run: plumbing only, not a result" if args.smoke else ""), args.out)


if __name__ == "__main__":
    main()
