"""Result files `eval/results/{id}.json` (Evaluation Plan §6) and pre-registered thresholds.

Point estimates decide PASS or FAIL; `separable` says whether the 95% interval clears
the threshold. How a non-separable result is reported is logged as C28.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

import yaml

from backend.config import REPO_ROOT

DATASETS = REPO_ROOT / "eval" / "datasets"
RESULTS = REPO_ROOT / "eval" / "results"
THRESHOLDS = REPO_ROOT / "eval" / "thresholds.yaml"
STATUSES = {"PASS", "FAIL", "INCONCLUSIVE", "NOT RUN"}
PACKAGES = ("chromadb", "rank-bm25", "pydantic", "httpx", "fastapi")


def load_thresholds(path: Path = THRESHOLDS) -> dict:
    return yaml.safe_load(path.read_text())


def gate_status(p: dict, minimum: float | None = None, maximum: float | None = None) -> dict:
    rate, ci = p["rate"], p["ci95"]
    if rate is None:
        return {"status": "NOT RUN", "separable": False}
    if minimum is not None:
        ok, separable = rate >= minimum, (ci[0] >= minimum or ci[1] < minimum)
        threshold = {"min": minimum}
    else:
        ok, separable = rate <= maximum, (ci[1] <= maximum or ci[0] > maximum)
        threshold = {"max": maximum}
    return {"status": "PASS" if ok else "FAIL", "separable": separable, **threshold}


def overall_status(gates: dict, critical: list) -> str:
    """FAIL on any critical failure or missed gate; INCONCLUSIVE if a gate could not be measured (n = 0)."""
    if critical or any(g["status"] == "FAIL" for g in gates.values()):
        return "FAIL"
    if any(g["status"] == "NOT RUN" for g in gates.values()):
        return "INCONCLUSIVE"
    return "PASS"


def environment(extra: dict | None = None) -> dict:
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True).stdout.strip())
    except OSError:
        commit, dirty = "unknown", True
    pkgs = {}
    for name in PACKAGES:
        try:
            pkgs[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            pkgs[name] = None
    return {"commit": commit, "dirty": dirty, "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "python": platform.python_version(), "machine": platform.machine(), "platform": platform.platform(),
            "packages": pkgs, **(extra or {})}


def make_result(eval_id: str, system: str, dataset: str, split: str, metrics: dict, per_example: list[dict],
                critical_failures: list, status: str, notes: str = "", env: dict | None = None) -> dict:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {sorted(STATUSES)}")
    path = DATASETS / dataset
    digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    return {"id": eval_id, "system": system, "dataset": {"name": dataset, "sha256": digest, "split": split},
            "environment": environment(env), "metrics": metrics, "critical_failures": critical_failures,
            "per_example": per_example, "status": status, "notes": notes}


def write_result(result: dict, out_dir: Path = RESULTS) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{result['id']}-{result['system'].replace(':', '_').replace('/', '_')}.json"
    path.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    return path
