"""Secret scan of the working tree and the full git history (T-106; security note S-01).

Standard library only. Scans tracked plus untracked-but-not-ignored files, and
every patch in `git log -p --all`. Prints `findings: N` with masked locations and
exits 1 when N > 0. Matched values are never printed in full.

Usage: python -I scripts/secret_scan.py [repo_path]
"""
from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

PATTERNS = {
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_\-]{35}"),
    "gemini_key_assignment": re.compile(r"GEMINI_API_KEY\s*[=:]\s*['\"]?([A-Za-z0-9_\-]{20,})"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "github_token": re.compile(r"(ghp|gho|ghs|ghu)_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{60,}"),
    "openai_or_anthropic_key": re.compile(r"sk-(ant-)?[A-Za-z0-9_\-]{32,}"),
}
MAX_BYTES = 5_000_000
# Test fixtures mark fake values with this token. It exempts only the loose
# assignment rule; key-format rules (e.g. `AIza...`) still apply to everything.
FIXTURE_MARKER = "not-a-real-key"


@dataclass(frozen=True)
class Finding:
    where: str  # "tree" or "history"
    path: str
    line: int
    rule: str
    preview: str  # masked

    def __str__(self) -> str:
        return f"{self.where}:{self.path}:{self.line}: {self.rule} ({self.preview})"


def _mask(match: str) -> str:
    return match[:4] + "…" + f"[{len(match)} chars]"


def _scan_text(text: str, where: str, path: str, line_offset: int = 0) -> list[Finding]:
    out = []
    for i, line in enumerate(text.splitlines(), start=1):
        for rule, pattern in PATTERNS.items():
            for m in pattern.finditer(line):
                if rule == "gemini_key_assignment" and FIXTURE_MARKER in m.group(1):
                    continue
                out.append(Finding(where, path, i + line_offset, rule, _mask(m.group(0))))
    return out


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True, errors="replace"
    ).stdout


def scan_tree(repo: Path) -> list[Finding]:
    findings = []
    files = _git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0")
    for rel in filter(None, files):
        p = repo / rel
        if not p.is_file() or p.stat().st_size > MAX_BYTES:
            continue
        raw = p.read_bytes()
        if b"\0" in raw[:8192]:
            continue  # binary
        findings += _scan_text(raw.decode("utf-8", errors="replace"), "tree", rel)
    return findings


def scan_history(repo: Path) -> list[Finding]:
    try:
        log = _git(repo, "log", "-p", "--all", "--no-color", "--no-ext-diff", "--format=commit %H")
    except subprocess.CalledProcessError:
        return []  # no commits yet
    findings, path, commit = [], "?", "?"
    for line in log.splitlines():
        if line.startswith("commit "):
            commit = line.split()[1][:8]
        elif line.startswith("+++ b/"):
            path = line[6:]
        elif line.startswith(("+", "-")) and not line.startswith(("+++", "---")):
            for f in _scan_text(line[1:], "history", f"{commit}:{path}"):
                findings.append(f)
    return findings


def scan(repo: str | Path) -> list[Finding]:
    repo = Path(repo).resolve()
    return scan_tree(repo) + scan_history(repo)


def main(argv: list[str]) -> int:
    repo = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parents[1]
    findings = scan(repo)
    for f in findings:
        print(f)
    print(f"findings: {len(findings)}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
