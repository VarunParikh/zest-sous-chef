"""Every benchmark save passes the post-hoc reason (Evaluation Plan §2 rule 8). Block 3.2 found E6 and E12 reruns
filed under post-hoc/ without the marker, because their scripts accepted --post-hoc and dropped it."""
import ast
from pathlib import Path

import pytest

SCRIPTS = sorted(p for p in Path("scripts/benchmark").glob("*.py") if p.name != "_common.py")


@pytest.mark.parametrize("path", SCRIPTS, ids=lambda p: p.name)
def test_every_save_call_passes_the_post_hoc_reason(path):
    tree = ast.parse(path.read_text())
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "save"]
    for c in calls:
        assert len(c.args) >= 3 or any(k.arg == "post_hoc" for k in c.keywords), f"{path.name}:{c.lineno} drops --post-hoc"
