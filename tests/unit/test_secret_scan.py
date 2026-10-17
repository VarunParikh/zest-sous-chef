"""T-106: repository secret scan of tree and full history finds nothing (S-01)."""
import subprocess
from pathlib import Path

from scripts.secret_scan import scan

ROOT = Path(__file__).resolve().parents[2]
# Assembled at runtime so this file never contains a key-shaped string.
CANARY = "AI" + "za" + "Q" * 35


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.invalid")
    _git(tmp_path, "config", "user.name", "t")
    return tmp_path


def test_canary_found_in_tree_and_history(tmp_path):
    repo = _repo(tmp_path)
    (repo / "a.py").write_text(f'KEY = "{CANARY}"\n')
    _git(repo, "add", "a.py")
    _git(repo, "commit", "-qm", "add")
    where = {f.where for f in scan(repo)}
    assert where == {"tree", "history"}


def test_canary_found_in_history_after_deletion(tmp_path):
    repo = _repo(tmp_path)
    (repo / "a.py").write_text(f'KEY = "{CANARY}"\n')
    _git(repo, "add", "a.py")
    _git(repo, "commit", "-qm", "add")
    (repo / "a.py").unlink()
    _git(repo, "commit", "-qam", "remove")
    assert {f.where for f in scan(repo)} == {"history"}


def test_ignored_env_file_not_scanned_but_assignment_elsewhere_is(tmp_path):
    repo = _repo(tmp_path)
    (repo / ".gitignore").write_text(".env\n")
    value = "x" * 30
    (repo / ".env").write_text(f"GEMINI_API_KEY={value}\n")
    (repo / "leak.txt").write_text(f"GEMINI_API_KEY={value}\n")
    paths = {f.path for f in scan(repo)}
    assert paths == {"leak.txt"}


def test_findings_are_masked(tmp_path):
    repo = _repo(tmp_path)
    (repo / "a.py").write_text(f'KEY = "{CANARY}"\n')
    [finding] = scan(repo)
    assert CANARY not in str(finding)


def test_this_repository_is_clean():
    findings = scan(ROOT)
    assert findings == [], [str(f) for f in findings]


def test_fixture_marker_exempts_only_the_assignment_rule(tmp_path):
    repo = _repo(tmp_path)
    marked = "test-value-not-a-real-key"
    (repo / "a.txt").write_text(f"GEMINI_API_KEY={marked}\nGEMINI_API_KEY={'z' * 25}\nKEY={CANARY}-not-a-real-key\n")
    rules = sorted(f.rule for f in scan(repo))
    assert rules == ["gemini_key_assignment", "google_api_key"]
