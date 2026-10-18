"""E14 traceability (Evaluation Plan v0.6 §4.16; C58, C64, C65). Run after `make test`, `make test-e2e` and
`make test-embedder` so the JUnit files are current. Reads the User Stories, the PRD AC table, the Test Plan,
the test files, the JUnit results, `eval/headline.yaml` and `open-conflicts.md`; nothing is typed by hand.
"""
from __future__ import annotations

import json

import yaml
from _common import ROOT, parser, save

from backend.evaluation.results import environment, make_result
from backend.evaluation.traceability import evaluate, parse_ac_table, parse_junit, parse_stories, parse_test_plan, scan_tests

DOCS = ROOT / "docs"
JUNIT = ROOT / "docs/epics/zest/verify/test-results"


def main():
    args = parser(__doc__).parse_args()
    stories = parse_stories((DOCS / "epics/zest/requirements/user-stories.md").read_text())
    acs = parse_ac_table((DOCS / "epics/zest/requirements/product-spec.md").read_text())
    plan_tests, ac_map = parse_test_plan((DOCS / "epics/zest/verify/test-plan.md").read_text())
    refs = scan_tests({str(p.relative_to(ROOT)): p.read_text() for p in sorted((ROOT / "tests").rglob("test_*.py"))})
    junit_files = [JUNIT / n for n in ("latest.xml", "e2e.xml", "embedder.xml")]
    missing_junit = [p.name for p in junit_files if not p.exists()]
    junit = parse_junit([p.read_text() for p in junit_files if p.exists()])
    raw = yaml.safe_load((ROOT / "eval/headline.yaml").read_text())
    headline, missing = {}, []
    for eid, h in raw.items():
        files = {}
        for f in h["files"]:
            path = ROOT / "eval/results" / f
            if path.exists():
                files[f] = json.loads(path.read_text())["status"]
            else:
                missing.append(f"{eid}: {f}")
        headline[eid] = {"files": files, "accepted": h.get("accepted"), "not_run_by_owner": h.get("not_run_by_owner", {})}
    out = evaluate(stories, acs, plan_tests, ac_map, refs, junit, headline, (DOCS / "core/open-conflicts.md").read_text())
    status = "PASS" if out["status"] == "PASS" and not missing and not missing_junit else "FAIL"
    metrics = {"must_stories": len(out["stories"]), "must_stories_with_passing_test": sum(r["pass"] for r in out["stories"]),
               "acs": len(out["acs"]), "acs_mapped_and_passing": sum(r["pass"] for r in out["acs"]),
               "open_fails": out["open_fails"], "accepted_fails": out["accepted_fails"], "xfails": out["xfails"],
               "not_run_by_owner": {e: h["not_run_by_owner"] for e, h in headline.items() if h["not_run_by_owner"]},
               "headline_status": {e: h["files"] for e, h in headline.items()}, "missing_headline_files": missing,
               "missing_junit": missing_junit, "p0_ids_no_test_references": out["p0_unreferenced"],
               "junit_cases": len(junit), "mapping_note": "module docstrings map to every test in the module; function names "
                                                           "and docstrings map to one function; each passing link records its level"}
    per = [{"kind": "story", **r} for r in out["stories"]] + [{"kind": "ac", **r} for r in out["acs"]]
    save(make_result("E14", "traceability", "docs/epics/zest/requirements/user-stories.md", "all", metrics, per,
                     out["open_fails"], status, env=environment()), args.out, args.post_hoc)
    print(status, {k: metrics[k] for k in ("must_stories", "must_stories_with_passing_test", "acs", "acs_mapped_and_passing")})
    for r in per:
        if not r["pass"]:
            print("  no passing test:", r["kind"], r["id"])
    print("  open fails:", out["open_fails"], "| missing:", missing, missing_junit)
    print("  accepted:", out["accepted_fails"])
    print("  P0 IDs with no test reference:", out["p0_unreferenced"])


if __name__ == "__main__":
    main()
