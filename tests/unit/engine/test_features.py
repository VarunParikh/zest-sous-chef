"""Dish premium level (C24, rescaled by C53; PRD Appendix A): the gourmet slider must be able to reorder dishes."""
from backend.engine.features import premium_level
from backend.session.levers import LeverSet


def test_premium_spans_zero_to_one_across_stored_dishes(store):
    levels = [premium_level(d, store) for d in store.dishes]
    assert min(levels) == 0.0 and max(levels) == 1.0


def test_gourmet_half_and_full_order_dishes_differently(store):
    """E6 found every raw premium below 0.5, so 0.5 and 1.0 gave the same order (C53)."""
    mains = [d for d in store.dishes if d.dish.course == "main"]

    def order(g):
        lv = LeverSet(gourmet_affinity=g)
        return sorted((d.dish.dish_id for d in mains), key=lambda i: (-(1 - abs(lv.gourmet_affinity - premium_level(store.dish(i), store))), i))

    assert order(0.5) != order(1.0)
