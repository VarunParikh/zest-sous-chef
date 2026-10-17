"""T-107: `.gitignore` covers `.env`, logs, the Chroma folder and uploads (S-07)."""
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _ignored(path: str) -> bool:
    return subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT).returncode == 0


@pytest.mark.parametrize("path", [".env", "logs/trace.jsonl", "data/chroma/chroma.sqlite3", "uploads/a.jpg"])
def test_sensitive_paths_ignored(path):
    assert _ignored(path)


def test_env_example_not_ignored():
    assert not _ignored(".env.example")
