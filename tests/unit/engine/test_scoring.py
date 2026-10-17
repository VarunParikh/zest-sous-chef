"""Scoring, normalisation, ties, lever sensitivity, context (FR-61, 66, 67, 111; App. A; T-030 to T-034, T-037, T-038)."""
from datetime import datetime

from backend.config import load_settings
from backend.engine.context import build_context, load_trends, trend_multiplier
from backend.engine.features import dish_candidate, history_buckets
from backend.engine.scoring import RawCandidate, effective_weights, minmax, rank_normalise, score_pool, select
from backend.session.levers import Weights
from tests.unit.engine.conftest import levers


def test_t030_normalisation():
    assert rank_normalise([1, 2, 3]) == [1.0, 0.5, 0.0]
    assert rank_normalise([2, 2]) == [0.5, 0.5]
    assert minmax([2.0, 4.0, 3.0]) == [0.0, 1.0, 0.5]
    assert minmax([7.0, 7.0, 7.0]) == [0.5, 0.5, 0.5]


def _pool():
    return [
        RawCandidate("a", match_rank=1, h=0.2, t=1.0, g=0.3),
        RawCandidate("b", match_rank=2, h=0.9, t=1.1, g=0.4),
        RawCandidate("c", match_rank=3, h=0.5, t=1.6, g=0.5),
        RawCandidate("d", match_rank=4, h=0.4, t=1.2, g=0.95),
    ]


def test_t031_final_is_sum_of_contributions():
    for s in score_pool(_pool(), Weights()):
        b = s.breakdown
        assert abs(sum(b.contributions.values()) - b.final) < 1e-9
        for k in ("s_p", "s_h", "s_t", "s_g"):
            assert abs(b.contributions[k] - b.weights_effective[k] * getattr(b, k)) < 1e-9


def test_effective_weights_normalised_and_all_zero_restores_defaults():
    w, restored = effective_weights(Weights(culinary_pairing=1, purchase_history=1, market_trend=0, persona_gourmet=0))
    assert w == {"s_p": 0.5, "s_h": 0.5, "s_t": 0.0, "s_g": 0.0} and not restored
    w0, restored0 = effective_weights(Weights(culinary_pairing=0, purchase_history=0, market_trend=0, persona_gourmet=0))
    assert restored0 and abs(sum(w0.values()) - 1) < 1e-9


def test_t032_ties_break_by_s_p_then_id_reproducibly():
    pool = [RawCandidate("z", 2, 0.5, 1.0, 0.5), RawCandidate("y", 1, 0.5, 1.0, 0.5), RawCandidate("x", 2, 0.5, 1.0, 0.5)]
    zero_p = Weights(culinary_pairing=0, purchase_history=1, market_trend=1, persona_gourmet=1)
    runs = [[s.candidate_id for s in score_pool(pool, zero_p)] for _ in range(5)]
    assert runs[0] == ["y", "x", "z"] and all(r == runs[0] for r in runs)


def test_t033_each_weight_reorders_towards_its_component():
    expected = {"culinary_pairing": "a", "purchase_history": "b", "market_trend": "c", "persona_gourmet": "d"}
    for name, top in expected.items():
        w = Weights(**{k: (1.0 if k == name else 0.0) for k in expected})
        assert score_pool(_pool(), w)[0].candidate_id == top, name


def test_t034_pool_of_15_shows_exactly_3(store):
    settings = load_settings(env={}, env_file=None)
    assert settings.dish_pool > 3  # a pool equal to the display size would make levers inert (FR-111)
    ctx = build_context(datetime(2026, 10, 17, 19, 0))
    lev = levers()
    pool = [dish_candidate(rec, lev, ctx, store, match_rank=i + 1) for i, rec in enumerate(store.dishes[:settings.dish_pool])]
    ranked = score_pool(pool, lev.weights)
    shown = select(ranked, display=3)
    assert len(pool) == 15 and len(shown) == 3 and all(s.breakdown.eligible for s in shown)


def test_dish_features_respond_to_history_lever(store):
    ctx = build_context(datetime(2026, 10, 17, 19, 0))
    kheer = store.dish("D27")
    assert "desserts" in history_buckets(kheer, store)
    low = dish_candidate(kheer, levers(history={"desserts": 0.0}), ctx, store, 1)
    high = dish_candidate(kheer, levers(history={"desserts": 1.0}), ctx, store, 1)
    assert high.h > low.h


def test_t037_frozen_context_is_reproducible(store):
    settings = load_settings(env={"CONTEXT_NOW": "2026-06-14T18:30:00", "CONTEXT_WEATHER": "hot"}, env_file=None)
    a, b = build_context(settings=settings), build_context(settings=settings)
    assert a == b and a.season == "summer" and a.day_type == "weekend" and a.part_of_day == "evening"
    trends, lev = load_trends(), levers()
    lassi = store.dish("D29")
    assert trend_multiplier(lassi, a, trends, lev) == trend_multiplier(lassi, b, trends, lev) > 1.0


def test_trend_slider_scales_effect(store):
    ctx = build_context(datetime(2026, 6, 14, 18, 30), weather="hot")
    trends, lassi = load_trends(), store.dish("D29")
    # weekend evening also matches the indulgence row T01, so hold that slider at 0 to isolate cooling
    off = trend_multiplier(lassi, ctx, trends, levers(trends={"cooling_drinks": 0.0, "weekend_indulgence": 0.0}))
    on = trend_multiplier(lassi, ctx, trends, levers(trends={"cooling_drinks": 1.0, "weekend_indulgence": 0.0}))
    assert off == 1.0 and on > 1.3
    both = trend_multiplier(lassi, ctx, trends, levers(trends={"cooling_drinks": 1.0, "weekend_indulgence": 1.0}))
    assert both > on


def test_t038_gender_boost_capped_and_never_filters(store, personas):
    ctx = build_context(datetime(2026, 10, 17, 19, 0))
    for rec in store.dishes:
        neutral = dish_candidate(rec, levers(), ctx, store, 1)
        for g in ("Female", "Male"):
            c = dish_candidate(rec, levers(gender=g), ctx, store, 1)
            assert 0 <= c.g_boost <= 0.1 * c.g_base + 1e-12
            assert abs(c.g - (c.g_base + c.g_boost)) < 1e-12
            assert c.eligible == neutral.eligible
    lassi = store.dish("D46")
    assert dish_candidate(lassi, levers(gender="Female"), ctx, store, 1).g_boost > 0
    assert dish_candidate(store.dish("D66"), levers(gender="Male"), ctx, store, 1).g_boost > 0
