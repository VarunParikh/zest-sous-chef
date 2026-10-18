"""Stock-outs, substitution and the cart-level guardrails (US-24; FR-76, 83, 90; AC-04, 05, 28, 33;
T-059, and the cart parts of T-011, T-012, T-017)."""
from datetime import datetime

import pytest

from backend.cart import service
from backend.cart.service import CartRuleError, view
from backend.engine.context import build_context
from backend.session.levers import LeverSet, merge_levers
from backend.session.store import SessionStore

CTX = build_context(now=datetime(2026, 10, 17, 19, 30), weather="cool")
JAIN = {"diet": "Jain (No Root Veggies / Pure Veg)"}
PURE_VEG = {"diet": "Pure Veg (Strict)"}


def _session(**over):
    return SessionStore().create(LeverSet.model_validate(merge_levers(LeverSet().model_dump(), over)))


def _zero(store, variant_ids):
    return store.with_stock({s.sku_id: 0 for v in variant_ids for s in store.skus_for(v)})


def _paneer(session):
    return next(ln for ln in session.cart.lines() if ln.ingredient_name == "paneer")


def test_t011_cart_part_jain_garlic_bread_refused_and_no_garlic(store):
    s = _session(**JAIN)
    with pytest.raises(CartRuleError) as e:
        service.add_dish(s, "D32", "text", CTX, store)
    assert e.value.code == "NOT_ELIGIBLE" and s.cart.is_empty
    # A compliant dish carts, and nothing in it is onion, garlic or root veg.
    service.add_dish(s, "D130", "text", CTX, store)
    flags = {f for ln in s.cart.lines() for f in store.variant(ln.variant_id).flags}
    assert not flags & {"onion_garlic", "root_veg"}


def test_t012_cart_part_pure_veg_chicken_refused(store):
    s = _session(**PURE_VEG)
    with pytest.raises(CartRuleError):
        service.add_dish(s, "D05", "youtube", CTX, store)
    assert s.cart.is_empty


def test_switch_variant_cannot_bring_in_a_blocked_item(store):
    s = _session(**JAIN)
    service.add_dish(s, "D130", "text", CTX, store)
    ln = s.cart.lines()[0]
    with pytest.raises(CartRuleError):
        service.switch_variant(s, ln.line_id, store.variants_for("garlic")[0].variant_id, CTX, store)


def test_t017_cart_part_filter_on_never_carts_an_out_of_stock_variant(store):
    s = _session()
    service.add_dish(s, "D06", "text", CTX, store)
    chosen = _paneer(s).variant_id
    low = _zero(store, [chosen])
    s2 = _session()
    service.add_dish(s2, "D06", "text", CTX, low)
    assert _paneer(s2).variant_id != chosen and _paneer(s2).in_stock
    none_left = _zero(store, [v.variant_id for v in store.variants_for("paneer")])
    with pytest.raises(CartRuleError):  # no paneer in stock at all: the dish is not eligible
        service.add_dish(_session(), "D06", "text", CTX, none_left)


def test_t017_cart_part_filter_off_keeps_and_flags(store):
    none_left = _zero(store, [v.variant_id for v in store.variants_for("paneer")])
    s = _session(business={"stock_filter": False})
    service.add_dish(s, "D06", "text", CTX, none_left)
    line = next(x for d in view(s.cart, none_left).dishes for x in d.lines if x.ingredient_name == "paneer")
    assert line.in_stock is False  # kept and flagged; Buy Now blocks it (T-058)


def test_t059_substitution_changes_the_cart_only_on_accept(store):
    s = _session()
    service.add_dish(s, "D06", "text", CTX, store)
    line = _paneer(s)
    out = _zero(store, [line.variant_id])
    before = s.cart.model_copy(deep=True)
    card = service.propose_substitution(s, line.line_id, CTX, out)
    assert card.type == "substitution" and card.from_item == store.variant(line.variant_id).name
    assert card.to_item != card.from_item and card.flavour_note
    new_variant = s.pending[card.substitution_id]["variant_id"]
    assert out.in_stock(new_variant)
    assert s.cart == before  # offered, not applied
    service.answer_substitution(s, card.substitution_id, "decline", CTX, out)
    assert s.cart == before and card.substitution_id not in s.pending
    card = service.propose_substitution(s, line.line_id, CTX, out)
    total_before = view(s.cart, out).subtotal_inr
    service.answer_substitution(s, card.substitution_id, "accept", CTX, out)
    assert _paneer(s).variant_id == new_variant and _paneer(s).in_stock
    assert view(s.cart, out).subtotal_inr - total_before == card.price_delta_inr
    with pytest.raises(CartRuleError):  # used once
        service.answer_substitution(s, card.substitution_id, "accept", CTX, out)


def test_no_substitution_when_nothing_eligible_is_in_stock(store):
    s = _session()
    service.add_dish(s, "D06", "text", CTX, store)
    none_left = _zero(store, [v.variant_id for v in store.variants_for("paneer")])
    assert service.propose_substitution(s, _paneer(s).line_id, CTX, none_left) is None
