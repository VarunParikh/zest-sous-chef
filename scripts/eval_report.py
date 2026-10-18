"""Build the evidence report (Evaluation Plan §9; v0.7 §4.17, C69 to C71): `make report`.

Writes docs/epics/zest/verify/report/index.html and report.md from eval/results/, eval/headline.yaml and
eval/thresholds.yaml, plus git metadata (HEAD and per-file staleness). Exits 1 if any required evaluation
has no result (C69), so the block 3.2 gate is checked by the exit code.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from backend.evaluation.report import build_model, load_inputs, render_html, render_markdown  # noqa: E402

OUT = ROOT / "docs" / "epics" / "zest" / "verify" / "report"
CODE_PATHS = ["src", "mock-data", "eval/datasets"]


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def main() -> int:
    inputs = load_inputs(ROOT / "eval" / "results", yaml.safe_load((ROOT / "eval" / "headline.yaml").read_text()),
                         yaml.safe_load((ROOT / "eval" / "thresholds.yaml").read_text()))
    head = _git("rev-parse", "--short", "HEAD")
    staleness = {}
    for f, r in inputs["results"].items():
        commit = r.get("environment", {}).get("commit")
        if commit:
            n = _git("rev-list", "--count", f"{commit}..HEAD", "--", *CODE_PATHS)
            staleness[f] = int(n) if n.isdigit() else ""
    model = build_model(inputs, (ROOT / "docs" / "core" / "open-conflicts.md").read_text(), {"head": head, "staleness": staleness})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "index.html").write_text(render_html(model))
    (OUT / "report.md").write_text(render_markdown(model))
    s = model["summary"]
    print(f"overall {s['overall']}; open FAILs {len(s['open_fails'])}; critical {len(s['critical'])}; "
          f"accepted {[a['eval'] for a in s['accepted']]}; required without a result: {s['missing'] or 'none'}")
    print(f"wrote {OUT.relative_to(ROOT)}/index.html and report.md")
    return 1 if s["missing"] else 0


if __name__ == "__main__":
    sys.exit(main())
