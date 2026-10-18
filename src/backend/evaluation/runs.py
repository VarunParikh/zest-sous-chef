"""C51: three runs of a real-model evaluation. Rate gates use the median run; a critical
failure in any run fails the evaluation; the range is always reported."""
from __future__ import annotations

from statistics import median


def aggregate(runs: list[dict[str, float]], gates: dict[str, tuple[str, float]], critical: list[list]) -> dict:
    metrics = {}
    for name, (kind, threshold) in gates.items():
        values = [r[name] for r in runs if r.get(name) is not None]
        if not values:
            metrics[name] = {"median": None, "range": None, "status": "NOT RUN"}
            continue
        m = median(values)
        passed = m >= threshold if kind == "min" else m <= threshold
        metrics[name] = {"median": m, "range": [min(values), max(values)], kind: threshold,
                         "status": "PASS" if passed else "FAIL", "runs": values}
    failed = [c for run in critical for c in run]
    if failed or any(v["status"] == "FAIL" for v in metrics.values()):
        status = "FAIL"
    elif any(v["status"] == "NOT RUN" for v in metrics.values()):
        status = "INCONCLUSIVE"
    else:
        status = "PASS"
    return {"metrics": metrics, "critical_runs": [len(c) for c in critical], "status": status}
