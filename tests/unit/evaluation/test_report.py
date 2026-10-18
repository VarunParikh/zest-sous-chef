"""Evidence report (Evaluation Plan §9; v0.7 §4.17, C69 to C71): status rules, the required-evaluation gate,
provenance, escaping and determinism. Fixture result files only."""
import json

import pytest

from backend.evaluation.report import REQUIRED, build_model, load_inputs, render_html, render_markdown

CONFLICTS = "| C57 | x | y | z | **Resolved 2026-10-18** |\n| C99 | x | y | z | **Open** |\n"
GIT = {"head": "abc1234", "staleness": {}}


def _result(eid, status="PASS", crit=(), notes="", metrics=None, commit="c0ffee1", date="2026-10-18T10:00:00+00:00"):
    return {"id": eid, "system": "s", "status": status, "critical_failures": list(crit), "notes": notes,
            "metrics": metrics or {}, "per_example": [], "dataset": {"name": "d", "version": "v1", "sha256": "0"},
            "environment": {"commit": commit, "date": date, "dirty": False, "machine": "arm64", "platform": "macOS"}}


@pytest.fixture
def tree(tmp_path):
    res = tmp_path / "results"
    res.mkdir()
    headline = {}
    for eid in REQUIRED:
        if eid == "E14":
            continue
        (res / f"{eid}-x.json").write_text(json.dumps(_result(eid)))
        headline[eid] = {"files": [f"{eid}-x.json"]}
    (res / "E14-traceability.json").write_text(json.dumps(_result("E14")))
    return res, headline


def _build(res, headline, conflicts=CONFLICTS):
    return build_model(load_inputs(res, headline, {"targets": {}}), conflicts, GIT)


def test_all_pass_is_pass(tree):
    m = _build(*tree)
    assert m["summary"]["overall"] == "PASS" and m["summary"]["missing"] == [] and m["summary"]["open_fails"] == []


def test_accepted_fail_keeps_overall_fail_but_is_not_open(tree):
    res, headline = tree
    (res / "E6-x.json").write_text(json.dumps(_result("E6", "FAIL")))
    headline["E6"]["accepted"] = "C57"
    s = _build(res, headline)["summary"]
    assert s["overall"] == "FAIL" and s["open_fails"] == []  # C70: §7 applied as written
    assert s["accepted"] == [{"eval": "E6", "file": "E6-x.json", "conflict": "C57"}]
    md = render_markdown(_build(res, headline))
    assert "Overall status: FAIL" in md and "No open FAIL" in md and "E6 (C57)" in md


def test_unaccepted_fail_is_open(tree):
    res, headline = tree
    (res / "E4-x.json").write_text(json.dumps(_result("E4", "FAIL")))
    headline["E4"]["accepted"] = "C99"  # an Open conflict does not accept anything
    s = _build(res, headline)["summary"]
    assert s["overall"] == "FAIL" and s["open_fails"] == [{"eval": "E4", "file": "E4-x.json"}]


def test_critical_failures_are_listed_first(tree):
    res, headline = tree
    (res / "E7-x.json").write_text(json.dumps(_result("E7", "FAIL", crit=[{"id": "P1", "kind": "violation"}])))
    m = _build(res, headline)
    md = render_markdown(m)
    assert m["summary"]["critical"] and md.index("Critical failures") < md.index("## 1.")


def test_missing_headline_is_not_run_and_blocks_the_gate(tree):
    res, headline = tree
    (res / "E9-x.json").unlink()
    m = _build(res, headline)
    assert m["summary"]["missing"] == ["E9"] and m["summary"]["overall"] == "INCONCLUSIVE"
    assert "NOT RUN" in render_markdown(m) and "Required evaluations without a result: E9" in render_markdown(m)


def test_not_run_by_owner_arm_is_listed_not_counted(tree):
    res, headline = tree
    headline["E3"]["not_run_by_owner"] = {"E3-big.json": "owner decision"}
    s = _build(res, headline)["summary"]
    assert s["missing"] == [] and s["not_run_by_owner"] == [{"eval": "E3", "file": "E3-big.json", "reason": "owner decision"}]


def test_numbers_come_from_the_files_and_every_file_is_in_provenance(tree):
    res, headline = tree
    (res / "E11-x.json").write_text(json.dumps(_result("E11", metrics={"flows": {"mood": {
        "status": "PASS", "end_to_end": {"n": 10, "median_ms": 1234.5, "p95_ms": 1500.0, "min_ms": 1.0, "max_ms": 2.0}}}})))
    md = render_markdown(_build(res, headline))
    assert "1.23 s" in md
    (res / "E11-x.json").write_text(json.dumps(_result("E11", metrics={"flows": {"mood": {
        "status": "PASS", "end_to_end": {"n": 10, "median_ms": 2345.6, "p95_ms": 2500.0, "min_ms": 1.0, "max_ms": 2.0}}}})))
    md2 = render_markdown(_build(res, headline))
    assert "2.35 s" in md2 and "1.23 s" not in md2
    for eid, h in headline.items():
        assert h["files"][0] in md2
    assert "E14-traceability.json" in md2


def test_post_hoc_results_are_listed_in_limitations(tree):
    res, headline = tree
    (res / "E8-x.json").write_text(json.dumps(_result("E8", notes="POST-HOC rerun: C68 catalogue fix; first result kept")))
    md = render_markdown(_build(res, headline))
    limits = md.split("## 7.", 1)[1]
    assert "E8-x.json" in limits and "C68 catalogue fix" in limits


def test_html_escapes_result_text(tree):
    res, headline = tree
    (res / "E8-x.json").write_text(json.dumps(_result("E8", notes="POST-HOC rerun: <script>alert(1)</script>")))
    html = render_html(_build(res, headline))
    assert "<script>alert(1)</script>" not in html and "&lt;script&gt;" in html
    assert html.lstrip().startswith("<!doctype html>")


def test_rebuild_is_byte_identical(tree):
    res, headline = tree
    assert render_html(_build(res, headline)) == render_html(_build(res, headline))
    assert render_markdown(_build(res, headline)) == render_markdown(_build(res, headline))


def test_a_rerun_filed_under_post_hoc_without_the_marker_is_still_listed(tree):
    """Block 3.2 finding: E6 and E12 reruns were filed under post-hoc/ but their scripts dropped the marker."""
    res, headline = tree
    (res / "post-hoc").mkdir()
    (res / "post-hoc" / "E6-x.json").write_text(json.dumps(_result("E6", notes="scripted intent")))
    headline["E6"]["files"] = ["post-hoc/E6-x.json"]
    limits = render_markdown(_build(res, headline)).split("## 7.", 1)[1]
    assert "post-hoc/E6-x.json" in limits and "did not record its reason" in limits
