"""S_final = M_elig × Σ ŵ_k × s_k (FR-61, 66, 111; PRD Appendix A).

Eligibility runs first; the surviving candidates are normalised and ranked.
s_p is rank-based, the other components min-max; equal inputs give 0.5.
Ties break by s_p, then candidate ID, so runs are reproducible (FR-66).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.session.levers import Weights

KEYS = ("s_p", "s_h", "s_t", "s_g")


def rank_normalise(ranks: list[int]) -> list[float]:
    """1 − (r − 1)/(N − 1) over the distinct ranks present; a single distinct rank gives 0.5."""
    distinct = sorted(set(ranks))
    if len(distinct) == 1:
        return [0.5] * len(ranks)
    pos = {r: i for i, r in enumerate(distinct)}
    n = len(distinct)
    return [1 - pos[r] / (n - 1) for r in ranks]


def minmax(values: list[float]) -> list[float]:
    lo, hi = min(values), max(values)
    if hi - lo < 1e-12:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def effective_weights(w: Weights) -> tuple[dict[str, float], bool]:
    """ŵ = w / Σw (FR-08). All zero restores the Settings Panel defaults (with a notice upstream)."""
    raw = [w.culinary_pairing, w.purchase_history, w.market_trend, w.persona_gourmet]
    restored = sum(raw) == 0
    if restored:
        d = Weights()
        raw = [d.culinary_pairing, d.purchase_history, d.market_trend, d.persona_gourmet]
    total = sum(raw)
    return dict(zip(KEYS, (x / total for x in raw))), restored


@dataclass
class RawCandidate:
    candidate_id: str
    match_rank: int
    h: float
    t: float
    g: float
    eligible: bool = True
    filtered_by: tuple[str, ...] = ()
    g_base: float | None = None
    g_boost: float = 0.0
    kind: str = "dish"

    def __post_init__(self):
        if self.g_base is None:
            self.g_base = self.g - self.g_boost


@dataclass
class Breakdown:
    s_p: float
    s_h: float
    s_t: float
    s_g: float
    weights_effective: dict[str, float]
    contributions: dict[str, float]
    final: float
    eligible: bool = True
    filtered_by: tuple[str, ...] = ()
    weights_restored: bool = False
    value_term: float | None = None


@dataclass
class Scored:
    candidate_id: str
    breakdown: Breakdown
    raw: RawCandidate = field(repr=False)


def score_pool(cands: list[RawCandidate], weights: Weights) -> list[Scored]:
    w, restored = effective_weights(weights)
    alive = [c for c in cands if c.eligible]
    out: list[Scored] = []
    if alive:
        comps = {
            "s_p": rank_normalise([c.match_rank for c in alive]),
            "s_h": minmax([c.h for c in alive]),
            "s_t": minmax([c.t for c in alive]),
            "s_g": minmax([c.g for c in alive]),
        }
        for i, c in enumerate(alive):
            s = {k: comps[k][i] for k in KEYS}
            contrib = {k: w[k] * s[k] for k in KEYS}
            out.append(Scored(c.candidate_id, Breakdown(**s, weights_effective=w, contributions=contrib,
                                                        final=sum(contrib.values()), weights_restored=restored), c))
    out.sort(key=lambda x: (-round(x.breakdown.final, 12), -x.breakdown.s_p, x.candidate_id))
    for c in sorted((c for c in cands if not c.eligible), key=lambda c: c.candidate_id):
        zero = dict.fromkeys(KEYS, 0.0)
        out.append(Scored(c.candidate_id, Breakdown(**zero, weights_effective=w, contributions=dict(zero), final=0.0,
                                                    eligible=False, filtered_by=c.filtered_by, weights_restored=restored), c))
    return out


def select(scored: list[Scored], display: int = 3) -> list[Scored]:
    """The displayed set: the top eligible candidates (FR-111: the pool is wider than this)."""
    return [s for s in scored if s.breakdown.eligible][:display]
