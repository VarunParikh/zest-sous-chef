"""Prompt files, versioned on disk (Agent Design §3; NFR-07). Untrusted text is spotlighted (§7.2)."""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).parent
VERSIONS = {"recipe_extract": "recipe_extract_v1.txt", "photo_detect": "photo_detect_v1.txt",
            "intent_classify": "intent_classify_v1.txt"}


def spotlight(text: str) -> str:
    """Wrap untrusted text as data; delimiter tokens inside it are neutralised."""
    clean = text.replace("<content>", "&lt;content&gt;").replace("</content>", "&lt;/content&gt;")
    return f"<content>{clean}</content>"


def render(name: str, text: str) -> tuple[str, str]:
    return (HERE / VERSIONS[name]).read_text(), spotlight(text)


def version(name: str) -> str:
    return VERSIONS[name].removesuffix(".txt")


def text(name: str) -> str:
    return (HERE / VERSIONS[name]).read_text()
