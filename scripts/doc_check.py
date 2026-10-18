"""Release-document checks (block 3.3): every relative link resolves, every `make` target named exists, and every
conflict (C..), evaluation (E..) and ADR cited exists. Run: .venv/bin/python -m scripts.doc_check"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ["README.md", *sorted(str(p.relative_to(ROOT)) for p in (ROOT / "docs/epics/zest/release").glob("*.md"))]


def _targets(makefile: str) -> set[str]:
    return set(re.findall(r"^([a-z][a-z-]*):", makefile, re.M))


def check_document(path: Path, root: Path, makefile: str, conflicts_md: str, eval_ids: set[str], adrs: set[str]) -> list[str]:
    text, problems = path.read_text(), []
    for target in re.findall(r"\[[^\]]*\]\(([^)\s]+)\)", text):
        if re.match(r"(https?:|mailto:|#)", target):
            continue
        if not (path.parent / target.split("#", 1)[0]).resolve().exists():
            problems.append(f"broken link: {target}")
    code = " ".join(re.findall(r"`([^`]+)`", text)) + "\n" + "\n".join(re.findall(r"```.*?\n(.*?)```", text, re.S))
    targets = _targets(makefile)
    for t in sorted(set(re.findall(r"(?:^|[\s`&;])make ([a-z][a-z-]*)", code, re.M))):
        if t not in targets:
            problems.append(f"unknown make target: {t}")
    known_c = set(re.findall(r"^\| (C\d+) \|", conflicts_md, re.M))
    for c in sorted(set(re.findall(r"\bC\d{1,3}\b", text)) - known_c):
        problems.append(f"unknown conflict: {c}")
    for e in sorted(set(re.findall(r"\bE\d{1,2}\b", text)) - eval_ids):
        problems.append(f"unknown evaluation: {e}")
    for a in sorted(set(re.findall(r"\bADR-\d{3}\b", text)) - adrs):
        problems.append(f"unknown ADR: {a}")
    return problems


def main() -> int:
    makefile = (ROOT / "Makefile").read_text()
    conflicts = (ROOT / "docs/core/open-conflicts.md").read_text()
    eval_ids = set(re.findall(r"^\| (E\d+) \|", (ROOT / "docs/epics/zest/verify/evaluation-plan.md").read_text(), re.M))
    adrs = {re.match(r"(ADR-\d{3})", p.name).group(1) for p in (ROOT / "docs/epics/zest/design/adr").glob("ADR-*.md")}
    failed = 0
    for rel in DOCS:
        problems = check_document(ROOT / rel, ROOT, makefile, conflicts, eval_ids, adrs)
        print(f"{rel}: {'ok' if not problems else '; '.join(problems)}")
        failed += bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
