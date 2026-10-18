"""E11 latency statistics (Evaluation Plan v0.6 §4.16; C59, C60, C61). No targets live here: E11 measures,
and the owner sets the NFR-01 targets afterwards from these numbers."""
from __future__ import annotations

import statistics


def percentile(values: list[float], q: float) -> float:
    """Linear interpolation between closest ranks (with n = 10 the p95 sits near the maximum)."""
    if not values:
        raise ValueError("no values")
    xs = sorted(values)
    pos = (len(xs) - 1) * q / 100
    lo = int(pos)
    hi = min(lo + 1, len(xs) - 1)
    return round(xs[lo] + (xs[hi] - xs[lo]) * (pos - lo), 4)


def summarise(values: list[float]) -> dict:
    return {"n": len(values), "median_ms": round(float(statistics.median(values)), 1), "p95_ms": round(percentile(values, 95), 1),
            "min_ms": round(float(min(values)), 1), "max_ms": round(float(max(values)), 1)}


def breakdown(runs: list[dict]) -> dict:
    """runs: [{"total_ms": float, "llm": [(call kind, latency_ms), ...]}]. Model time is summed per kind
    within a run; "other" is the run's total minus all model time."""
    per_kind: dict[str, list[float]] = {}
    other = []
    for r in runs:
        sums: dict[str, float] = {}
        for kind, ms in r["llm"]:
            sums[kind] = sums.get(kind, 0.0) + ms
        for kind, ms in sums.items():
            per_kind.setdefault(kind, []).append(ms)
        other.append(r["total_ms"] - sum(sums.values()))
    out = {k: summarise(v) for k, v in sorted(per_kind.items())}
    if runs:
        out["other"] = summarise(other)
    return out


def flow_status(runs: list[dict], required: int = 10) -> str:
    if not runs:
        return "NOT RUN"
    return "PASS" if len(runs) >= required and all(r["normal"] for r in runs) else "FAIL"
