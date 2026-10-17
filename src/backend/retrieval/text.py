"""Query normalisation: lowercase, synonym phrases, filler removal (Data Model §7.4 step 1)."""
from __future__ import annotations

import re

FILLERS = {
    "i", "im", "i'm", "am", "a", "an", "the", "to", "of", "and", "for", "with", "in", "on", "my", "me", "some",
    "something", "want", "wanna", "need", "like", "would", "please", "can", "you", "make", "cook", "give", "get",
    "feel", "feeling", "today", "tonight", "is", "it", "that", "this", "what", "have", "let", "lets", "let's", "us",
}
_TOKEN = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in FILLERS]


def doc_tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


def expand(query: str, synonyms: list[dict]) -> list[str]:
    """Synonym phrases (`treat myself` -> indulgent, `kandha` -> onion) add their target's tokens."""
    q = " " + " ".join(doc_tokens(query)) + " "
    extra: list[str] = []
    for s in sorted(synonyms, key=lambda s: -len(s["query_term"])):
        phrase = " " + " ".join(doc_tokens(s["query_term"])) + " "
        if phrase.strip() and phrase in q:
            extra += doc_tokens(s["maps_to"])
    return tokens(query) + extra
