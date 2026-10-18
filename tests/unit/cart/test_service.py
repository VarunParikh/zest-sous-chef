"""Carting real dishes, totals and edits (US-21, US-22; FR-71 to 74, 114; AC-08; T-053, T-055)."""
from datetime import datetime

import pytest

from backend.cart import service
from backend.cart.service import CartRuleError, view
from backend.engine.context import build_context
from backend.session.levers import LeverSet
from backend.session.store import SessionStore

CTX = build_context(now=datetime(2026, 10, 17, 19, 30), weather="cool")


@pytest.fixture
def session():
    return SessionStore().create(LeverSet())


def _butter(cart, cd):
    return next(ln for d in cart.dishes if d.cart_dish_id == cd for ln in d.lines if ln.ingredient_name == "butter")


def test_add_dish_carts_every_line_from_the_catalogue(session, store):
    cd = service.add_dish(session, "D06", "text", CTX, store)
    d = session.cart.dishes[0]
    assert d.cart_dish_id == cd.cart_dish_id == "cd_1" and d.name == "Paneer Butter Masala" and len(d.lines) == 10
    assert all(store.variant(ln.variant_id) for ln in d.lines) and all(ln.packs for ln in d.lines)
    assert all(ln.reason for ln in d.lines)


def test_ac08_butter_shared_between_two_real_dishes(session, store):
    first = service.add_dish(session, "D06", "text", CTX, store)
    second = service.add_dish(session, "D40", "text", CTX, store)
    a, b = _butter(session.cart, first.cart_dish_id), _butter(session.cart, second.cart_dish_id)
    assert a.variant_id == b.variant_id and a.priced and not b.priced and b.shared_from_line_id == a.line_id
    service.remove_line(session, a.line_id, store)
    b = _butter(session.cart, second.cart_dish_id)
    assert b.priced and b.shared_from_line_id is None


def test_t053_dish_totals_and_subtotal(session, store):
    service.add_dish(session, "D06", "text", CTX, store)
    service.add_dish(session, "D40", "text", CTX, store)
    v = view(session.cart, store)
    for d in v.dishes:
        assert d.dish_total_inr == sum(ln.price_inr for ln in d.lines if ln.priced)
    assert v.subtotal_inr == sum(d.dish_total_inr for d in v.dishes) > 0
    assert v.item_count == sum(len(d.lines) for d in v.dishes)


def test_t055_remove_line_then_dish_removes_only_the_target(session, store):
    keep = service.add_dish(session, "D01", "text", CTX, store)
    target = service.add_dish(session, "D40", "text", CTX, store)
    before = view(session.cart, store)
    line = target.lines[0]
    service.remove_line(session, line.line_id, store)
    after = view(session.cart, store)
    assert [ln.line_id for ln in after.dishes[1].lines] == [ln.line_id for ln in before.dishes[1].lines][1:]
    assert after.dishes[0] == before.dishes[0]
    assert after.subtotal_inr == before.subtotal_inr - before.dishes[1].lines[0].price_inr
    service.remove_dish(session, target.cart_dish_id, store)
    assert [d.cart_dish_id for d in session.cart.dishes] == [keep.cart_dish_id]
    with pytest.raises(CartRuleError):
        service.remove_dish(session, target.cart_dish_id, store)


def test_quantity_multiplies_owned_packs_and_shared_lines_refuse(session, store):
    first = service.add_dish(session, "D06", "text", CTX, store)
    second = service.add_dish(session, "D40", "text", CTX, store)
    a = _butter(session.cart, first.cart_dish_id)
    single = view(session.cart, store).subtotal_inr
    unit = sum(store.price(store.sku(p.sku_id)) * p.count for p in a.packs)
    service.set_quantity(session, a.line_id, 3, store)
    assert view(session.cart, store).subtotal_inr == single + 2 * unit
    assert [p.count for p in _butter(session.cart, first.cart_dish_id).packs] == [3 * p.count for p in a.packs]
    with pytest.raises(CartRuleError) as e:
        service.set_quantity(session, _butter(session.cart, second.cart_dish_id).line_id, 2, store)
    assert e.value.code == "SHARED_LINE"


def test_switch_variant_only_to_an_eligible_variant_of_the_same_ingredient(session, store):
    cd = service.add_dish(session, "D06", "text", CTX, store)
    paneer = next(ln for ln in cd.lines if ln.ingredient_name == "paneer")
    other = next(v for v in store.variants_for("paneer") if v.variant_id != paneer.variant_id)
    service.switch_variant(session, paneer.line_id, other.variant_id, CTX, store)
    assert next(ln for ln in session.cart.lines() if ln.line_id == paneer.line_id).variant_id == other.variant_id
    butter = store.variants_for("butter")[0]
    with pytest.raises(CartRuleError):
        service.switch_variant(session, paneer.line_id, butter.variant_id, CTX, store)
    gone = next(v for v in store.variants_for("paneer") if v.variant_id not in (other.variant_id,))
    empty = store.with_stock({s.sku_id: 0 for s in store.skus_for(gone.variant_id)})
    with pytest.raises(CartRuleError):  # out of stock with the stock filter on: not eligible
        service.switch_variant(session, paneer.line_id, gone.variant_id, CTX, empty)
