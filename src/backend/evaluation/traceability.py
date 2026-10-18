"""E14 traceability (Evaluation Plan v0.6 §4.16; C58, C64, C65).

Everything is parsed from the documents, the test files and the JUnit results; the only
hand-made input is the owner-reviewed `eval/headline.yaml`. A test file's module docstring
maps its IDs to every test in the module; a function's name (`test_t050_…`) or docstring maps
them to that function only. Each passing link records which of the two it came from.
"""
from __future__ import annotations

import ast
import re
import xml.etree.ElementTree as ET

_NUM = r"(\d{2,3})"


def expand_ids(text: str, prefix: str) -> set[str]:
    """IDs with one prefix, expanding "FR-06, 08, 104", "AC-43 to AC-45" and "T-001 to 004". Lower-case
    `t050` in test names counts for T-IDs only."""
    out: set[str] = set()
    pat = re.compile(rf"(?<![A-Za-z]){prefix}-{_NUM}((?:\s*(?:,|to|and)\s*(?:{prefix}-)?\d{{2,3}}(?![\d-]))*)")
    for m in pat.finditer(text):
        nums, last = [int(m.group(1))], int(m.group(1))
        for sep, n in re.findall(rf"\s*(,|to|and)\s*(?:{prefix}-)?(\d{{2,3}})", m.group(2)):
            n = int(n)
            nums += list(range(last + 1, n + 1)) if sep == "to" else [n]
            last = n
        out |= {f"{prefix}-{n:0{len(m.group(1))}d}" for n in nums}
    if prefix == "T":
        out |= {f"T-{n}" for n in re.findall(r"(?<![a-z])t(\d{3})(?=_|\b)", text)}
    return out


def _all_ids(text: str) -> set[str]:
    return expand_ids(text, "T") | expand_ids(text, "AC") | expand_ids(text, "FR") | expand_ids(text, "US") \
        | expand_ids(text, "NFR") | {f"E2E-{n}" for n in re.findall(r"E2E-(\d{3})", text)}


def parse_stories(md: str) -> dict:
    out = {}
    for m in re.finditer(r"^\*\*(US-\d{2})\*\*.*?\*([A-Z/]+) · [A-Z/]+\*(.*)$", md, re.M):
        covers = m.group(3).split("Covers", 1)[1] if "Covers" in m.group(3) else ""
        out[m.group(1)] = {"priority": m.group(2), "frs": expand_ids(covers, "FR") | expand_ids(covers, "NFR"),
                           "acs": expand_ids(covers, "AC")}
    return out


def parse_ac_table(prd: str) -> dict:
    return {m.group(1): expand_ids(m.group(2), "FR") for m in re.finditer(r"^\| (AC-\d{2}) \|.*\| ([^|]*) \|\s*$", prd, re.M)}


def parse_test_plan(md: str) -> tuple[dict, dict]:
    tests = {}
    for m in re.finditer(r"^\| ((?:T|E2E)-\d{3}) \| .*? \| ([^|]*) \| (P\d)(?: \([^)|]*\))? \|\s*$", md, re.M):
        cov = m.group(2)
        tests[m.group(1)] = {"covers": expand_ids(cov, "FR") | expand_ids(cov, "NFR") | expand_ids(cov, "AC"), "priority": m.group(3)}
    section = md.split("## 5.", 1)[1].split("\n## ", 1)[0] if "## 5." in md else ""
    ac_map: dict[str, set] = {}
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        for ac, refs in zip(cells[0::2], cells[1::2]):
            if re.fullmatch(r"AC-\d{2}", ac):
                ac_map[ac] = expand_ids(refs, "T") | {f"E2E-{n}" for n in re.findall(r"E2E-(\d{3})", refs)} \
                    | set(re.findall(r"\bE\d{1,2}\b", refs))
    return tests, ac_map


class Refs(dict):
    """ID -> test node IDs, plus `function_level` for links made by a function's own name or docstring."""

    def __init__(self):
        super().__init__()
        self.function_level: dict[str, set] = {}


def scan_tests(files: dict[str, str]) -> Refs:
    refs = Refs()
    for path, src in files.items():
        tree = ast.parse(src)
        funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
        nodes = [f"{path}::{f.name}" for f in funcs]
        for i in _all_ids(ast.get_docstring(tree) or ""):
            refs.setdefault(i, set()).update(nodes)
        for f, node in zip(funcs, nodes):
            for i in _all_ids(f.name + " " + (ast.get_docstring(f) or "")):
                refs.setdefault(i, set()).add(node)
                refs.function_level.setdefault(i, set()).add(node)
    return refs


def parse_junit(xml_texts: list[str]) -> dict:
    """node -> passed | failed | xfail | skipped; a parametrised test fails if any case fails."""
    rank = {"passed": 0, "skipped": 1, "xfail": 2, "failed": 3}
    out: dict[str, str] = {}
    for text in xml_texts:
        for case in ET.fromstring(text).iter("testcase"):
            node = case.get("classname").replace(".", "/") + ".py::" + case.get("name").split("[", 1)[0]
            status = "passed"
            if case.find("failure") is not None or case.find("error") is not None:
                status = "failed"
            elif (sk := case.find("skipped")) is not None:
                status = "xfail" if "xfail" in (sk.get("type") or "") else "skipped"
            if rank[status] >= rank[out.get(node, "passed")]:
                out[node] = status
    return out


def _resolved(conflicts_md: str, cid: str) -> bool:
    row = next((ln for ln in conflicts_md.splitlines() if ln.startswith(f"| {cid} |")), "")
    return "Resolved" in row.rsplit("|", 2)[-2] if row else False


def _links(ids: set[str], refs: Refs, junit: dict) -> tuple[list[str], str | None]:
    passing = sorted({n for i in ids for n in refs.get(i, ()) if junit.get(n) == "passed"})
    fn = {n for i in ids for n in refs.function_level.get(i, ())}
    level = None if not passing else ("function" if any(n in fn for n in passing) else "module")
    return passing, level


def evaluate(stories, ac_table, plan_tests, ac_map, refs: Refs, junit, headline: dict, conflicts_md: str) -> dict:
    fr_tests: dict[str, set] = {}
    for tid, row in plan_tests.items():
        for c in row["covers"]:
            fr_tests.setdefault(c, set()).add(tid)
    story_rows = []
    for sid, s in sorted(stories.items()):
        if s["priority"] == "S/M":  # C65: US-25 counts as Must for FR-77 only
            frs, acs = {"FR-77"} & s["frs"], set()
        elif s["priority"] == "M":
            frs, acs = s["frs"], s["acs"]
        else:
            continue
        ids = {sid} | frs | acs | {t for a in acs for t in ac_map.get(a, ()) if not t.startswith("E")} \
            | {t for f in frs | acs for t in fr_tests.get(f, ())}
        passing, level = _links(ids, refs, junit)
        story_rows.append({"id": sid, "priority": s["priority"], "tests": passing, "level": level, "pass": bool(passing)})
    ac_rows = []
    for ac in sorted(ac_table):
        mapped = ac_map.get(ac, set())
        evals = sorted(e for e in mapped if re.fullmatch(r"E\d{1,2}", e) and e in headline)
        passing, level = _links((mapped - set(evals)) | {ac}, refs, junit)
        ac_rows.append({"id": ac, "mapped": sorted(mapped), "tests": passing, "level": level, "evidence": evals,
                        "pass": bool(passing or evals)})
    open_fails, accepted = [], []
    for eid, h in sorted(headline.items()):
        for f, status in sorted(h["files"].items()):
            if status != "FAIL":
                continue
            cid = h.get("accepted")
            if cid and _resolved(conflicts_md, cid):
                accepted.append({"eval": eid, "file": f, "conflict": cid})
            else:
                open_fails.append({"kind": "evaluation", "id": eid, "file": f})
    open_fails += [{"kind": "test", "id": n} for n, st in sorted(junit.items()) if st == "failed"]
    xfails = sorted(n for n, st in junit.items() if st == "xfail")
    p0_unref = sorted(t for t, row in plan_tests.items() if row["priority"] == "P0" and not refs.get(t))
    ok = all(r["pass"] for r in story_rows) and all(r["pass"] for r in ac_rows) and not open_fails
    return {"stories": story_rows, "acs": ac_rows, "open_fails": open_fails, "accepted_fails": accepted, "xfails": xfails,
            "p0_unreferenced": p0_unref, "status": "PASS" if ok else "FAIL"}
