"""Retrieve, then guard, then rank (Architecture §5; FR-60, 111, 112, 115, 119; G9).

Guardrails run in code on every retrieved candidate; each removal is traced as
`guardrail_filtered`. Add-ons are only suggested: nothing enters a cart here (FR-64).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.catalogue.store import Store
from backend.engine.context import Context
from backend.engine.features import dish_candidate
from backend.engine.scoring import Scored, score_pool, select
from backend.retrieval.retriever import Hit, Retriever
from backend.session.levers import LeverSet


@dataclass
class Recommendation:
    pool: list[Hit]
    scored: list[Scored]
    shown: list[Scored]
    inspector: list[dict]
    fallback_used: bool = False
    added: list = field(default_factory=list)  # always empty: suggestions need a tap (FR-64)


def _inspector(pool: list[Hit], scored: list[Scored]) -> list[dict]:
    by_id = {s.candidate_id: s for s in scored}
    rows = []
    for h in pool:
        b = by_id[h.id].breakdown
        rows.append({
            "candidate_id": h.id, "lexical_rank": h.lexical_rank, "vector_rank": h.vector_rank,
            "vector_distance": h.vector_distance, "curated_rank": h.curated_rank, "curated_strength": h.curated_strength,
            "fused_rank": h.fused_rank, "fused_score": h.fused_score, "eligible": b.eligible,
            "filtered_by": list(b.filtered_by), "final": b.final,
            "components": {"s_p": b.s_p, "s_h": b.s_h, "s_t": b.s_t, "s_g": b.s_g},
        })
    return rows


def _rank(pool, levers, ctx, store, tracer, session_id, display, kind, cart_terms=frozenset()) -> tuple[list[Scored], list[Scored]]:
    cands = [dish_candidate(store.dish(h.id), levers, ctx, store, match_rank=h.fused_rank, kind=kind, cart_terms=cart_terms)
             for h in pool]
    if tracer is not None:
        for c in cands:
            if not c.eligible:
                tracer.emit("guardrail_filtered", session_id, candidate_id=c.candidate_id, rules_failed=list(c.filtered_by))
    scored = score_pool(cands, levers.weights)
    return scored, select(scored, display)


def recommend_dishes(query: str, levers: LeverSet, ctx: Context, store: Store, retriever: Retriever,
                     tracer=None, session_id: str = "-", display: int = 3) -> Recommendation:
    res = retriever.dishes(query, session_id)
    scored, shown = _rank(res.hits, levers, ctx, store, tracer, session_id, display, "dish")
    return Recommendation(res.hits, scored, shown, _inspector(res.hits, scored), res.fallback_used)
