"""Code routing before the intent model (C54; Agent Design v0.4 §6.1). Examples are not E2 test rows."""
import pytest

from backend.catalogue.store import load_store
from backend.intent.routing import route

STORE = load_store()


@pytest.mark.parametrize("text,dish", [
    ("I want to cook palak paneer", "Palak Paneer"),
    ("can you help me make Chole tonight", "Chole"),
    ("let's try dal bhaat", "Dal Chawal"),  # an alias
    ("I'd like to prepare masala dosa, please", "Masala Dosa"),
])
def test_cooking_verb_plus_stored_dish_is_named_dish(text, dish):
    r = route(text, STORE)
    assert r is not None and r.intent == "named_dish" and r.dish_name == dish and r.confidence == 1.0


@pytest.mark.parametrize("text", [
    "make palak paneer with 200 g spinach",  # digits: a recipe, not a name
    "Palak paneer: spinach, paneer, cream, garlic",  # a list
    "I love palak paneer",  # no cooking verb
    "I want to cook something cooling",  # no stored dish
])
def test_other_messages_go_to_the_model(text):
    assert route(text, STORE) is None


@pytest.mark.parametrize("text", ["clear my cart", "please empty the basket", "start over with my cart", "cart: reset it"])
def test_clearing_the_cart_is_routed(text):
    r = route(text, STORE)
    assert r is not None and r.intent == "cart_clear_or_replace"


def test_a_cart_edit_is_not_a_clear():
    assert route("remove the oil from my cart", STORE) is None
