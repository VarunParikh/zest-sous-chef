"""E14 traceability pure parts (Evaluation Plan v0.6 §4.16; C58, C64, C65)."""
from backend.evaluation.traceability import (evaluate, expand_ids, parse_ac_table, parse_junit, parse_stories,
                                             parse_test_plan, scan_tests)

STORIES = """
**US-01** As Rohan, I want levers. *M · M* Covers FR-01, 02, 03; AC-01.
**US-12** As a user, I want scaling. *C · S* Covers FR-32. (Could; first to cut.)
**US-19** As Meera, I want add-ons. *M · S* Covers FR-62, 64, 118; AC-43 to AC-45.
**US-22** As Meera, I want totals. *M · M* Covers FR-72, 73.
**US-25** As a user, I want chat cart edits. *S/M · S* Covers FR-77, 78.
**US-34** As the owner, I want timeouts. *M · M* Covers NFR-02, 10; section 9.
"""
PRD = """| AC | Criterion | FR |
|---|---|---|
| AC-01 | Snapshot | FR-02, 03 |
| AC-02 | RDI meets the objective | FR-01, 08, 61 |
| AC-43 | Add-on offered | FR-118 |
| AC-44 | Add-on cap | FR-60 |
| AC-45 | Curated fallback | FR-117 |
"""
PLAN = """## 4. Test catalogue
| ID | Test | Covers | Pri |
|---|---|---|---|
| T-001 | Snapshot holds | FR-02, AC-01 | P0 |
| T-049 | Add-ons | FR-118, 117, AC-43, AC-45 | P0 |
| T-053 | Totals | FR-72 | P0 |
| T-091 | Timeout fallback | NFR-02 | P0 |
| T-099 | Never written | FR-77 | P0 |
| T-110 | Responsive | FR-100 | P1 |
| T-075 | Markup inert | S-06 | P0 (E2E) |
## 5. Acceptance criteria to test map
| AC | Test(s) | AC | Test(s) |
|---|---|---|---|
| AC-01 | T-001 | AC-43 | T-049 |
| AC-02 | Evaluation E6 (not a unit test) | AC-44 | T-048 |
| AC-45 | T-049 | | |
## 6. Next
"""
TESTS = {
    "tests/unit/test_levers.py": '"""Levers (US-01; T-001)."""\n\ndef test_snapshot():\n    pass\n',
    "tests/unit/test_addons.py": '"""Add-ons (T-047 to T-049)."""\n\ndef test_curated():\n    pass\n\ndef test_vector():\n    pass\n',
    "tests/unit/test_cart.py": '"""Cart."""\n\ndef test_t053_totals():\n    pass\n\ndef test_clear():\n    """Confirmed clear (FR-77)."""\n',
    "tests/unit/test_timeouts.py": '"""Timeouts."""\n\ndef test_t091_timeout():\n    pass\n',
}
JUNIT = """<?xml version="1.0"?><testsuites><testsuite>
<testcase classname="tests.unit.test_levers" name="test_snapshot" />
<testcase classname="tests.unit.test_addons" name="test_curated" />
<testcase classname="tests.unit.test_addons" name="test_vector[a]" />
<testcase classname="tests.unit.test_cart" name="test_t053_totals"><failure message="boom" /></testcase>
<testcase classname="tests.unit.test_cart" name="test_clear" />
<testcase classname="tests.unit.test_timeouts" name="test_t091_timeout"><skipped type="pytest.xfail" message="known" /></testcase>
</testsuite></testsuites>"""


def test_expand_ids_handles_lists_and_ranges():
    assert expand_ids("FR-01, 02, 03; AC-01", "FR") == {"FR-01", "FR-02", "FR-03"}
    assert expand_ids("AC-43 to AC-45", "AC") == {"AC-43", "AC-44", "AC-45"}
    assert expand_ids("T-001 to 004, 030", "T") == {"T-001", "T-002", "T-003", "T-004", "T-030"}
    assert expand_ids("test_t050_two_packs and test_ac08_butter", "T") == {"T-050"}
    assert expand_ids("NFR-02, 10", "NFR") == {"NFR-02", "NFR-10"} and expand_ids("NFR-02", "FR") == set()


def test_parse_stories_priority_and_coverage():
    s = parse_stories(STORIES)
    assert s["US-01"] == {"priority": "M", "frs": {"FR-01", "FR-02", "FR-03"}, "acs": {"AC-01"}}
    assert s["US-12"]["priority"] == "C" and s["US-25"]["priority"] == "S/M"
    assert s["US-19"]["acs"] == {"AC-43", "AC-44", "AC-45"} and "NFR-02" in s["US-34"]["frs"]


def test_parse_ac_table_and_test_plan():
    assert parse_ac_table(PRD)["AC-02"] == {"FR-01", "FR-08", "FR-61"}
    tests, ac_map = parse_test_plan(PLAN)
    assert tests["T-049"] == {"covers": {"FR-118", "FR-117", "AC-43", "AC-45"}, "priority": "P0"}
    assert ac_map["AC-02"] == {"E6"} and ac_map["AC-45"] == {"T-049"} and ac_map["AC-44"] == {"T-048"}


def test_scan_maps_module_and_function_references():
    refs = scan_tests(TESTS)
    assert refs["T-001"] == {"tests/unit/test_levers.py::test_snapshot"}
    assert refs["T-048"] == {"tests/unit/test_addons.py::test_curated", "tests/unit/test_addons.py::test_vector"}
    assert refs["T-053"] == {"tests/unit/test_cart.py::test_t053_totals"}
    assert refs["FR-77"] == {"tests/unit/test_cart.py::test_clear"} and refs["US-01"]


def test_parse_junit_aggregates_parametrised_cases():
    j = parse_junit([JUNIT])
    assert j["tests/unit/test_addons.py::test_vector"] == "passed"
    assert j["tests/unit/test_cart.py::test_t053_totals"] == "failed"
    assert j["tests/unit/test_timeouts.py::test_t091_timeout"] == "xfail"


def _evaluate(headline=None, conflicts="| C57 | x | y | z | **Resolved 2026-10-18** |"):
    return evaluate(parse_stories(STORIES), parse_ac_table(PRD), *parse_test_plan(PLAN), scan_tests(TESTS), parse_junit([JUNIT]),
                    headline or {"E6": {"files": {"E6.json": "FAIL"}, "accepted": "C57"}}, conflicts)


def test_story_and_ac_checks_follow_the_rules():
    out = _evaluate()
    stories = {r["id"]: r for r in out["stories"]}
    assert set(stories) == {"US-01", "US-19", "US-22", "US-25", "US-34"}  # Must only; US-25 counts for FR-77 (C65)
    assert stories["US-01"]["pass"] and stories["US-19"]["pass"] and stories["US-25"]["pass"]
    assert stories["US-22"]["pass"] is False  # its only test (T-053) failed
    assert stories["US-34"]["pass"] is False  # its test is an xfail, not a pass
    acs = {r["id"]: r for r in out["acs"]}
    assert acs["AC-02"]["pass"] and acs["AC-02"]["evidence"] == ["E6"]  # an evaluation with a headline result
    assert acs["AC-44"]["pass"] and acs["AC-44"]["level"] == "module"  # T-048 maps only through the module range


def test_open_fail_rules():
    out = _evaluate()
    assert out["accepted_fails"] == [{"eval": "E6", "file": "E6.json", "conflict": "C57"}]
    assert {"kind": "test", "id": "tests/unit/test_cart.py::test_t053_totals"} in out["open_fails"]
    assert out["xfails"] == ["tests/unit/test_timeouts.py::test_t091_timeout"]
    assert out["status"] == "FAIL"
    unaccepted = _evaluate(conflicts="| C57 | x | y | z | **Open** |")
    assert {"kind": "evaluation", "id": "E6", "file": "E6.json"} in unaccepted["open_fails"]


def test_p0_ids_without_a_test_are_listed():
    assert "T-099" in _evaluate()["p0_unreferenced"]


def test_annotated_priority_cells_are_parsed():
    """Block 3.5 finding: a row whose priority reads "P0 (E2E)" was skipped, hiding an unimplemented P0 test."""
    tests, _ = parse_test_plan(PLAN)
    assert tests["T-075"]["priority"] == "P0"
    assert "T-075" in _evaluate()["p0_unreferenced"]
