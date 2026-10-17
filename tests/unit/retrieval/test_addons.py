"""Add-on retrieval: curated plus vector, course rule, weighted RRF, fallback
(US-19; ADR-004 v2; FR-117 to 119; AC-43 to 45; T-047 to T-049)."""
from datetime import datetime

import pytest

from backend.engine.context import build_context
from backend.engine.eligibility import check_dish
from backend.engine.recommend import recommend_addons
from backend.retrieval.fusion import rrf
from tests.unit.engine.conftest import levers
from tests.unit.retrieval.conftest import events

CTX = build_context(datetime(2026, 10, 17, 19, 0))
COMPANION = {"side", "beverage", "dessert"}


def test_t047_weighted_rrf_hand_calculation():
    fused = rrf({"curated": ["A", "B"], "vector": ["B", "C"]}, k=60, weights={"curated": 2, "vector": 1})
    assert [f.id for f in fused] == ["B", "A", "C"]
    expected = {"A": 2 / 61, "B": 2 / 62 + 1 / 61, "C": 1 / 62}
    for f in fused:
        assert f.score == pytest.approx(expected[f.id], abs=1e-12)
    # a dish in one list scores from that list alone; equal scores break by curated strength, then ID
    strength = {"P": 0.4, "Q": 0.8}
    tied = rrf({"curated": ["P", "Q"], "vector": ["Q", "P"]}, k=60, weights={"curated": 1, "vector": 1},
               tiebreak=lambda i: (-strength.get(i, 0), i))
    assert tied[0].score == pytest.approx(tied[1].score) and [f.id for f in tied] == ["Q", "P"]


def test_t048_course_rule_then_guardrails_after_fusion(store, retriever, tracer):
    jain = levers(diet="Jain (No Root Veggies / Pure Veg)", faith="Jain (Strict Root-Free)")
    raw = retriever.addons("D06")
    for h in raw.hits:
        if h.vector_rank is not None:
            assert store.dish(h.id).dish.course in COMPANION, h.id
    assert all(h.id != "D06" for h in raw.hits)
    rec = recommend_addons("D06", jain, CTX, store, retriever, tracer)
    removed = [h.id for h in rec.pool if not check_dish(store.dish(h.id), jain, store, kind="addon").eligible]
    assert removed, "the fixture must contain at least one persona-breaking companion"
    shown = {s.candidate_id for s in rec.shown}
    assert not shown & set(removed)
    traced = {e["data"]["candidate_id"] for e in events(tracer, "guardrail_filtered")}
    assert set(removed) <= traced


def test_t049_no_curated_pair_still_gets_vector_add_on(store, retriever, tracer):
    assert not [p for p in store.pairings if p.dish_a == "D23"]
    rec = recommend_addons("D23", levers(), CTX, store, retriever, tracer)
    assert rec.shown and all(store.dish(s.candidate_id).dish.course in COMPANION for s in rec.shown)
    assert all(h.curated_rank is None for h in rec.pool)
    assert not rec.added  # suggestions only: nothing enters a cart without a tap (FR-64)


def test_t049_vector_down_uses_curated_only(store, lexical_only, tracer):
    rec = recommend_addons("D23", levers(), CTX, store, lexical_only, tracer)
    assert rec.shown == [] and rec.pool == []
    assert events(tracer, "fallback_used")
    paired = recommend_addons("D04", levers(), CTX, store, lexical_only, tracer)  # biryani has curated pairs
    assert paired.shown and all(h.vector_rank is None and h.curated_rank for h in paired.pool)


def test_cart_dishes_excluded_from_add_ons(store, retriever):
    raw = retriever.addons("D04", cart_dish_ids=("D04", "D36"))
    assert "D36" not in [h.id for h in raw.hits]
