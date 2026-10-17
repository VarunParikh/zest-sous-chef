"""(Weighted) reciprocal rank fusion: score = Σ w_i / (k + rank_i) (FR-110, FR-118; Cormack et al. 2009).

An item in one list scores from that list alone. Ties break by `tiebreak(id)`
(default: ID), so results are reproducible.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Fused:
    id: str
    score: float
    ranks: dict[str, int] = field(default_factory=dict)


def rrf(lists: dict[str, list[str]], k: int = 60, weights: dict[str, float] | None = None,
        tiebreak: Callable[[str], tuple] | None = None) -> list[Fused]:
    out: dict[str, Fused] = {}
    for name, ids in lists.items():
        w = (weights or {}).get(name, 1.0)
        for rank, item in enumerate(ids, start=1):
            f = out.setdefault(item, Fused(item, 0.0))
            if name not in f.ranks:
                f.ranks[name] = rank
                f.score += w / (k + rank)
    key = tiebreak or (lambda i: (i,))
    return sorted(out.values(), key=lambda f: (-round(f.score, 12), *key(f.id)))
