"""E3 item matching between detections and photo labels (fixed before any E3 run, 2026-10-18).

Labels: "x or y" means either counts; "(uncertain)" or "(unclear ...)" items are optional
(they count for precision if found, not for recall); other parentheticals are dropped.
Names are lowercased, singularised and mapped through lexicon aliases (bell pepper ->
capsicum). A detection matches a label alternative when one token set contains the other.
Matching is one-to-one, highest-confidence detection first.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from backend.catalogue.seed import Lexicon
from backend.retrieval.text import doc_tokens


def _singular(t: str) -> str:
    if t.endswith("ies") and len(t) > 4:
        return t[:-3] + "y"
    if t.endswith(("oes", "ches", "shes")):
        return t[:-2]
    if t.endswith("s") and not t.endswith("ss") and len(t) > 3:
        return t[:-1]
    return t


def tokens(name: str, lex: Lexicon) -> set[str]:
    clean = re.sub(r"\s*\(.*?\)", "", name.lower()).strip()
    words = [_singular(t) for t in doc_tokens(clean)]
    phrase = " ".join(words)
    for size in (3, 2, 1):  # replace the longest alias phrases with their canonical term
        for i in range(len(words) - size + 1):
            chunk = " ".join(words[i:i + size])
            canon = lex.canonical(chunk)
            if canon and canon != chunk:
                phrase = phrase.replace(chunk, canon)
    return set(phrase.split())


@dataclass
class Label:
    text: str
    alternatives: list[set[str]]
    optional: bool


@dataclass
class MatchResult:
    true_positives: int
    false_positives: int
    required_found: int
    required_total: int
    pairs: list[tuple[str, str]]


def labels_from(visible: list[str], lex: Lexicon) -> list[Label]:
    out = []
    for text in visible:
        optional = bool(re.search(r"\b(uncertain|unclear)\b", text))
        alts = [tokens(a, lex) for a in re.sub(r"\s*\(.*?\)", "", text).split(" or ")]
        out.append(Label(text, [a for a in alts if a], optional))
    return out


def _hit(det: set[str], alt: set[str]) -> bool:
    return bool(det) and bool(alt) and (det <= alt or alt <= det)


def match(detections: list[tuple[str, float]], labels: list[Label], lex: Lexicon) -> MatchResult:
    used: set[int] = set()
    tp, pairs = 0, []
    for name, _ in sorted(detections, key=lambda d: -d[1]):
        det = tokens(name, lex)
        for i, label in enumerate(labels):
            if i not in used and any(_hit(det, alt) for alt in label.alternatives):
                used.add(i)
                tp += 1
                pairs.append((name, label.text))
                break
    required = [i for i, l in enumerate(labels) if not l.optional]
    return MatchResult(tp, len(detections) - tp, sum(1 for i in required if i in used), len(required), pairs)
