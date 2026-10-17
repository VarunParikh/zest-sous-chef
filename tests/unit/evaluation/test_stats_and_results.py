"""Evaluation harness: Wilson intervals, retrieval metrics, result files (Evaluation Plan §2, §6)."""
import json

import pytest

from backend.evaluation.metrics import f1, mrr, recall_at
from backend.evaluation.results import gate_status, load_thresholds, make_result, overall_status, write_result
from backend.evaluation.stats import proportion, wilson


def test_wilson_known_values():
    lo, hi = wilson(8, 10)
    assert lo == pytest.approx(0.4902, abs=1e-4) and hi == pytest.approx(0.9433, abs=1e-4)
    lo0, hi0 = wilson(0, 10)
    assert lo0 == 0.0 and hi0 == pytest.approx(0.2775, abs=1e-4)
    assert wilson(0, 0) is None


def test_proportion_reports_k_over_n():
    p = proportion(8, 10)
    assert p == {"k": 8, "n": 10, "rate": 0.8, "ci95": [pytest.approx(0.4902, abs=1e-4), pytest.approx(0.9433, abs=1e-4)]}


def test_retrieval_metrics():
    assert recall_at(["a", "b", "c"], {"c", "z"}, 2) == 0.0
    assert recall_at(["a", "b", "c"], {"c", "z"}, 3) == 1.0  # any relevant item in the top k counts as a hit
    assert mrr(["a", "b", "c"], {"b"}) == 0.5 and mrr(["a"], {"q"}) == 0.0


def test_f1():
    assert f1({"a", "b"}, {"a", "b"}) == 1.0
    assert f1({"a", "x"}, {"a", "b"}) == 0.5
    assert f1(set(), set()) == 1.0 and f1({"x"}, set()) == 0.0


def test_gate_status_and_separability():
    g = gate_status(proportion(10, 10), minimum=0.80)
    assert g["status"] == "PASS" and g["separable"] is False  # CI (0.72, 1.0) straddles 0.80 (C28)
    assert gate_status(proportion(5, 10), minimum=0.80)["status"] == "FAIL"
    assert gate_status(proportion(1, 40), maximum=0.05)["status"] == "PASS"


def test_thresholds_load_with_safe_yaml():
    t = load_thresholds()
    assert t["E1_text_model"]["extraction_f1_min"] == 0.80 and t["version"] == 3


def test_result_file_shape(tmp_path):
    r = make_result("E5", system="lexical", dataset="retrieval_v1.jsonl", split="dev",
                    metrics={"recall_at_pool": proportion(3, 4)}, per_example=[{"id": "q1", "hit": True}],
                    critical_failures=[], status="PASS", notes="smoke")
    assert set(r) >= {"id", "system", "dataset", "environment", "metrics", "critical_failures", "per_example", "status"}
    assert len(r["dataset"]["sha256"]) == 64 and r["dataset"]["split"] == "dev"
    assert {"commit", "date", "python", "packages"} <= set(r["environment"])
    path = write_result(r, tmp_path)
    assert json.loads(path.read_text())["status"] == "PASS"
    with pytest.raises(ValueError):
        make_result("E5", system="x", dataset="retrieval_v1.jsonl", split="dev", metrics={}, per_example=[],
                    critical_failures=[], status="GREAT")


def test_overall_status():
    ok = {"a": {"status": "PASS"}}
    assert overall_status(ok, []) == "PASS"
    assert overall_status({**ok, "b": {"status": "NOT RUN"}}, []) == "INCONCLUSIVE"
    assert overall_status({**ok, "b": {"status": "FAIL"}}, []) == "FAIL"
    assert overall_status(ok, [{"x": 1}]) == "FAIL"
