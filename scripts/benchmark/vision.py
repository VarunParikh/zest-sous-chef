"""E3 vision benchmark (Evaluation Plan §4 E3; ADR-003 v2; thresholds v3; C29).

For each candidate: the text model (llama3.2:3b at 4k) and the guard (llama-guard3:1b)
stay resident, one unscored warm-up call loads the vision model, then 3 runs over all
11 photos. Precision and recall use clear photos (RF04 blurry and RF10 dark are scored
on quality flags and invented items instead) and detections at or above
CONFIDENCE_THRESHOLD. Labels are assistant-written and UNVERIFIED (owner decision).
Models must already be installed; nothing is pulled here.
Run: .venv/bin/python scripts/benchmark/vision.py [--models a,b] [--gemini-model M] [--runs 3] [--smoke --out DIR]
"""
import json
import re
import subprocess
import time

import httpx
from _common import ROOT, parser, save

from backend.catalogue.seed import load_lexicon
from backend.config import load_settings
from backend.evaluation.photos import labels_from, match
from backend.evaluation.results import gate_status, load_thresholds, make_result, overall_status
from backend.evaluation.stats import proportion
from backend.llm.client import LLMError
from backend.llm.image import prepare_image
from backend.llm.vision import GeminiVision, OllamaVision

CANDIDATES = "qwen3-vl:4b-instruct,qwen3-vl:8b-instruct,gemma4:e2b-it-qat"
RESIDENT = {"llama3.2:3b": 4096, "llama-guard3:1b": None}
UNCLEAR = {"RF04": "blurry", "RF10": "dark"}
DEMO = {"RF01", "RF02", "RF03", "RF07"}
LABEL_NOTE = "photo labels are assistant-written and UNVERIFIED (owner decision 2026-10-17)"


def ollama_ps() -> str:
    return subprocess.run(["ollama", "ps"], capture_output=True, text=True).stdout.strip()


def swapouts() -> int:
    out = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
    return int(re.search(r"Swapouts:\s+(\d+)", out).group(1))


def keep_resident(base: str):
    for model, ctx in RESIDENT.items():
        opts = {"num_predict": 1, **({"num_ctx": ctx} if ctx else {})}
        httpx.post(f"{base}/api/chat", timeout=120, json={"model": model, "stream": False, "keep_alive": "60m",
                                                          "options": opts, "messages": [{"role": "user", "content": "ok"}]})


def unload_vision(base: str):
    for line in ollama_ps().splitlines()[1:]:
        name = line.split()[0] if line.split() else ""
        if name and name not in RESIDENT:
            subprocess.run(["ollama", "stop", name], capture_output=True)


def gpu_only(name: str, ps: str) -> bool:
    for line in ps.splitlines()[1:]:
        if line.startswith(name):
            return "100% GPU" in line
    return False


def run_candidate(provider, photos, runs, lex, threshold, pause_s=0.0):
    per, failures, latencies = [], 0, []
    for run in range(1, runs + 1):
        for p in photos:
            image = prepare_image((ROOT / p["file"]).read_bytes())
            t0 = time.perf_counter()
            try:
                res = provider.detect(image)
                err = None
            except LLMError as e:
                res, err = None, str(e)[:120]
                failures += 1
            ms = (time.perf_counter() - t0) * 1000
            latencies.append(ms)
            items = [(i.name, i.confidence) for i in (res.items if res else [])]
            confident = [it for it in items if it[1] >= threshold]
            row = {"run": run, "photo": p["id"], "subset": "demo" if p["id"] in DEMO else "test", "latency_ms": round(ms),
                   "quality": res.quality if res else None, "scene_is_food": res.scene_is_food if res else None,
                   "items": items, "error": err}
            if p["id"] in UNCLEAR:
                row["expected_quality"] = UNCLEAR[p["id"]]
                row["confident_items_on_unclear_photo"] = len(confident)
            else:
                m = match(confident, labels_from(p["visible"], lex), lex)  # a failed call matches nothing
                row.update(tp=m.true_positives, fp=m.false_positives, found=m.required_found, required=m.required_total, pairs=m.pairs)
            per.append(row)
            if pause_s:
                time.sleep(pause_s)
    return per, failures, sorted(latencies)


def summarise(per, failures, lat, runs):
    def pr(rows):
        tp, fp = sum(r["tp"] for r in rows), sum(r["fp"] for r in rows)
        return proportion(tp, tp + fp), proportion(sum(r["found"] for r in rows), sum(r["required"] for r in rows))
    clear = [r for r in per if "tp" in r]  # failed calls stay in: they found nothing (fix 2026-10-18)
    prec, rec = pr(clear)
    prec_test, rec_test = pr([r for r in clear if r["subset"] == "test"])
    prec_demo, rec_demo = pr([r for r in clear if r["subset"] == "demo"])
    unclear = [r for r in per if "expected_quality" in r]
    q_ok = sum(1 for r in per if r["quality"] == r.get("expected_quality", "ok"))
    per_run = {run: dict(zip(("precision", "recall"), (x["rate"] for x in pr([r for r in clear if r["run"] == run]))))
               for run in range(1, runs + 1)}
    return {"precision_clear": prec, "recall_clear": rec, "precision_test_photos": prec_test, "recall_test_photos": rec_test,
            "precision_demo_photos": prec_demo, "recall_demo_photos": rec_demo, "per_run": per_run,
            "quality_flag_accuracy": proportion(q_ok, len(per)),
            "confident_items_on_unclear_photos": sum(r["confident_items_on_unclear_photo"] for r in unclear),
            "failures": proportion(failures, len(per)),
            "latency_ms_median": round(lat[len(lat) // 2]) if lat else None,
            "latency_ms_p95": round(lat[min(len(lat) - 1, int(0.95 * len(lat)))]) if lat else None}


def main():
    ap = parser(__doc__)
    ap.add_argument("--models", default=CANDIDATES)
    ap.add_argument("--gemini-model", default="gemini-3.5-flash-lite")
    ap.add_argument("--runs", type=int, default=3)
    args = ap.parse_args()
    settings, th, lex = load_settings(), load_thresholds()["E3_vision"], load_lexicon()
    photos = json.loads((ROOT / "mock-data" / "photos.json").read_text())["photos"]
    runs = 1 if args.smoke else args.runs
    if args.smoke:
        photos = [p for p in photos if p["id"] in {"RF03", "RF04"}]
    split = "smoke" if args.smoke else "all-11-photos"
    base = settings.ollama_base_url
    installed = {m["name"] for m in httpx.get(f"{base}/api/tags", timeout=5).json().get("models", [])}
    candidates = [("ollama", m) for m in args.models.split(",")] + [("gemini", args.gemini_model)]
    for kind, model in candidates:
        system = f"{kind}:{model}"
        if kind == "ollama" and model not in installed:
            save(make_result("E3", system, "mock-data/photos.json", split, {}, [], [], "NOT RUN", notes="model not installed"), args.out, args.post_hoc)
            continue
        if kind == "gemini" and not settings.gemini_api_key.get_secret_value():
            save(make_result("E3", system, "mock-data/photos.json", split, {}, [], [], "NOT RUN", notes="no GEMINI_API_KEY in .env"), args.out, args.post_hoc)
            continue
        keep_resident(base)
        unload_vision(base)
        if kind == "ollama":
            provider = OllamaVision(base, model, timeout_s=120, num_ctx=settings.vision_num_ctx)
            t0 = time.perf_counter()
            try:
                provider.detect(prepare_image((ROOT / "assets" / "sample-photos" / "RF05.jpeg").read_bytes()))  # warm-up, unscored
            except LLMError:
                pass
            cold_ms = round((time.perf_counter() - t0) * 1000)
        else:
            provider, cold_ms = GeminiVision(settings.gemini_api_key.get_secret_value(), model, timeout_s=settings.timeout_vision_s), None
        swap0 = swapouts()
        per, failures, lat = run_candidate(provider, photos, runs, lex, settings.confidence_threshold,
                                           pause_s=6.5 if kind == "gemini" else 0.0)  # stay under free-tier rate limits
        swap_delta, ps = swapouts() - swap0, ollama_ps()
        m = summarise(per, failures, lat, runs)
        m.update({"num_ctx": settings.vision_num_ctx if kind == "ollama" else None, "served_model": provider.last_served_model, "cold_load_ms": cold_ms, "swapouts_delta": swap_delta,
                  "ollama_ps": ps, "resident_models": list(RESIDENT), "confidence_threshold": settings.confidence_threshold})
        gates = {"precision": gate_status(m["precision_clear"], minimum=th["precision_min"]),
                 "recall": gate_status(m["recall_clear"], minimum=th["recall_min"]),
                 "latency_p95": {"status": "PASS" if m["latency_ms_p95"] is not None and m["latency_ms_p95"] <= th["latency_p95_max_s"] * 1000 else "FAIL"},
                 "no_failures": {"status": "PASS" if failures == 0 else "FAIL"}}
        if kind == "ollama":
            gates["no_swap"] = {"status": "PASS" if swap_delta == 0 else "FAIL"}
            gates["gpu_only"] = {"status": "PASS" if gpu_only(model, ps) else "FAIL"}
            evicted = [r for r in RESIDENT if r not in ps]
            gates["text_model_resident"] = {"status": "PASS" if not evicted else "FAIL", "evicted": evicted}
        m["gates"] = gates
        m["owner_recall_target_0_80_met"] = (m["recall_clear"]["rate"] or 0) >= th["recall_target_owner"]
        notes = "; ".join(x for x in ["smoke run: plumbing only, not a result" if args.smoke else "", LABEL_NOTE,
                                     "Gemini free tier may use submitted content (C8); sample photos only; Flash-Lite chosen because three "
                                     "gemini-3.8-flash probe calls took 23.5 s, 40 s and over 60 s (gate 20 s)" if kind == "gemini" else ""] if x)
        save(make_result("E3", system, "mock-data/photos.json", split, m, per, [], overall_status(gates, []), notes=notes), args.out, args.post_hoc)
    unload_vision(base)


if __name__ == "__main__":
    main()
