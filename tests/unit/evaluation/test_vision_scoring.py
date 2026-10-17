"""E3 scoring: a failed call on a clear photo counts as finding nothing (harness fix, 2026-10-18)."""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("vision_bench", ROOT / "scripts" / "benchmark" / "vision.py")


def _load():
    import sys
    sys.path.insert(0, str(ROOT / "scripts" / "benchmark"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_failed_call_counts_as_misses():
    v = _load()
    ok = {"run": 1, "photo": "RF06", "subset": "test", "error": None, "quality": "ok", "tp": 3, "fp": 1, "found": 3, "required": 7}
    failed = {"run": 1, "photo": "RF05", "subset": "test", "error": "invalid JSON", "quality": None, "tp": 0, "fp": 0, "found": 0, "required": 6}
    m = v.summarise([ok, failed], failures=1, lat=[1000, 2000], runs=1)
    assert m["recall_clear"]["n"] == 13 and m["recall_clear"]["k"] == 3
    assert m["precision_clear"]["n"] == 4
