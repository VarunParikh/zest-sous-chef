"""E11 latency pure parts (Evaluation Plan v0.6 §4.16; C59, C60, C61)."""
import pytest

from backend.evaluation.latency import breakdown, flow_status, percentile, summarise


def test_percentile_linear_interpolation():
    xs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert percentile(xs, 50) == 5.5 and percentile(xs, 95) == pytest.approx(9.55) and percentile(xs, 100) == 10
    assert percentile([4.0], 95) == 4.0
    with pytest.raises(ValueError):
        percentile([], 50)


def test_summarise_reports_n_median_p95_min_max():
    s = summarise([300, 100, 200])
    assert s == {"n": 3, "median_ms": 200.0, "p95_ms": 290.0, "min_ms": 100.0, "max_ms": 300.0}


def test_breakdown_sums_model_time_per_kind_per_run_then_takes_medians():
    runs = [{"total_ms": 1000, "llm": [("guard", 100), ("intent", 300), ("reason", 200)]},
            {"total_ms": 2000, "llm": [("guard", 100), ("intent", 500), ("intent", 500), ("reason", 400)]}]
    b = breakdown(runs)
    assert b["guard"]["median_ms"] == 100 and b["intent"]["median_ms"] == 650 and b["reason"]["median_ms"] == 300
    assert b["other"]["median_ms"] == 450  # (1000 - 600, 2000 - 1500) -> median 450


def test_flow_passes_only_with_ten_normal_runs():
    assert flow_status([{"normal": True}] * 10, required=10) == "PASS"
    assert flow_status([{"normal": True}] * 9 + [{"normal": False}], required=10) == "FAIL"
    assert flow_status([{"normal": True}] * 9, required=10) == "FAIL"
    assert flow_status([], required=10) == "NOT RUN"
