"""Confirmed replace with Undo (US-25; FR-77; T-060 cart part). The chat trigger ("do something else") is block 2.3."""
from datetime import datetime

import pytest

from backend.cart import service
from backend.cart.service import CartRuleError
from backend.engine.context import build_context
from backend.session.levers import LeverSet
from backend.session.store import SessionStore

CTX = build_context(now=datetime(2026, 10, 17, 19, 30), weather="cool")


@pytest.fixture
def session(store):
    s = SessionStore().create(LeverSet())
    service.add_dish(s, "D06", "text", CTX, store)
    return s


def test_t060_replace_or_add_is_asked_and_nothing_cleared_before_confirm(session, store):
    before = session.cart.model_copy(deep=True)
    card = service.offer_replace(session, "D01", "mood")
    assert card.type == "confirm" and card.prompt == "Replace the Paneer Butter Masala cart, or add to it?"
    assert [o.value for o in card.options] == ["replace", "add", "cancel"]
    assert session.cart == before


def test_t060_cancel_changes_nothing(session, store):
    before = session.cart.model_copy(deep=True)
    card = service.offer_replace(session, "D01", "mood")
    assert service.answer_confirm(session, card.confirm_id, "cancel", CTX, store) is None
    assert session.cart == before and card.confirm_id not in session.pending


def test_t060_replace_then_undo_restores_the_cart(session, store):
    before = session.cart.model_copy(deep=True)
    card = service.offer_replace(session, "D01", "mood")
    added = service.answer_confirm(session, card.confirm_id, "replace", CTX, store)
    assert [d.dish_id for d in session.cart.dishes] == ["D01"] and added.added_by_suggestion_id
    name = service.undo(session, added.added_by_suggestion_id, store)
    assert name == "Dal Chawal" and session.cart == before
    with pytest.raises(CartRuleError):
        service.undo(session, added.added_by_suggestion_id, store)


def test_add_keeps_the_cart_and_undo_removes_only_the_new_dish(session, store):
    before = session.cart.model_copy(deep=True)
    card = service.offer_replace(session, "D01", "mood")
    added = service.answer_confirm(session, card.confirm_id, "add", CTX, store)
    assert [d.dish_id for d in session.cart.dishes] == ["D06", "D01"]
    service.undo(session, added.added_by_suggestion_id, store)
    assert session.cart == before


def test_stale_confirm_rejected(session, store):
    with pytest.raises(CartRuleError):
        service.answer_confirm(session, "c_99", "replace", CTX, store)
