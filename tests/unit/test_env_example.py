"""`.env.example` stays current with Settings (CLAUDE.md working agreements)."""
from pathlib import Path

from backend.config import Settings

ROOT = Path(__file__).resolve().parents[2]


def _parse(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip()
    return out


def test_env_example_lists_every_setting():
    keys = set(_parse(ROOT / ".env.example"))
    expected = {name.upper() for name in Settings.model_fields}
    assert keys == expected


def test_gemini_key_is_blank():
    assert _parse(ROOT / ".env.example")["GEMINI_API_KEY"] == ""
