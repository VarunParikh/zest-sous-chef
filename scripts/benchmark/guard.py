"""E4 guard benchmark (Evaluation Plan §4 E4; ADR-006). Systems: rules only; rules plus
Llama Guard via Ollama (NOT RUN if the model is not installed; never pulled here).
"Blocked" = no action and a templated redirect (owner decision 2026-10-17).
Run: .venv/bin/python scripts/benchmark/guard.py [--split test] [--smoke --out DIR]
"""
import time

import httpx
from _common import parser, rows, save

from backend.config import load_settings
from backend.evaluation.results import gate_status, load_thresholds, make_result, overall_status
from backend.evaluation.stats import proportion
from backend.guard import default_guard

CLASSIFIER = "llama-guard3:1b"
ATTACKS = {"injection", "injection_via_transcript", "off_topic", "hazardous"}
CONTAMINATION = "rules author saw test items G02 and G04 while checking the file format (disclosed 2026-10-18)"


def installed(base: str) -> set[str]:
    try:
        return {m["name"] for m in httpx.get(f"{base}/api/tags", timeout=3).json().get("models", [])}
    except httpx.HTTPError:
        return set()


def classify(base: str, text: str) -> bool:
    r = httpx.post(f"{base}/api/chat", timeout=30, json={"model": CLASSIFIER, "stream": False, "options": {"temperature": 0},
                                                         "messages": [{"role": "user", "content": text}]})
    return r.json()["message"]["content"].strip().lower().startswith("unsafe")


def main():
    args = parser(__doc__).parse_args()
    settings, guard, th = load_settings(), default_guard(), load_thresholds()["E4_guard"]
    data = rows("guard_v1.jsonl", args.split, args.smoke)
    split = "dev-smoke" if args.smoke else args.split
    systems = ["rules"] + (["rules+llama-guard3:1b"] if CLASSIFIER in installed(settings.ollama_base_url) else [])
    for system in ["rules", "rules+llama-guard3:1b"]:
        if system not in systems:
            save(make_result("E4", system, "guard_v1.jsonl", split, {}, [], [], "NOT RUN",
                             notes=f"{CLASSIFIER} not installed (download needs owner approval)"), args.out)
            continue
        per = []
        for g in data:
            t0 = time.perf_counter()
            source = "transcript" if g["category"] == "injection_via_transcript" else "user"
            s = guard.screen(g["text"], source=source)
            blocked = s.label != "ok" and s.message_id is not None
            if not blocked and system != "rules":
                blocked = classify(settings.ollama_base_url, g["text"])
            per.append({"id": g["id"], "category": g["category"], "expected": g["expected"], "blocked": blocked,
                        "label": s.label, "latency_ms": round((time.perf_counter() - t0) * 1000, 2)})
        attacks = [p for p in per if p["category"] in ATTACKS]
        benign = [p for p in per if p["category"] == "benign"]
        block = proportion(sum(p["blocked"] for p in attacks), len(attacks))
        fp = proportion(sum(p["blocked"] for p in benign), len(benign))
        gates = {"attack_block_rate": gate_status(block, minimum=th["attack_block_rate_min"]),
                 "false_positive_rate": gate_status(fp, maximum=th["false_positive_max"])}
        status = overall_status(gates, [])
        save(make_result("E4", system, "guard_v1.jsonl", split, {"attack_block_rate": block, "false_positive_rate": fp,
                                                                 "gates": gates}, per, [], status,
                         notes=("smoke run: plumbing only, not a result; " if args.smoke else "") + CONTAMINATION
                         + "; end-to-end cart-change critical check runs with the E9 harness (block 2)"), args.out)


if __name__ == "__main__":
    main()
