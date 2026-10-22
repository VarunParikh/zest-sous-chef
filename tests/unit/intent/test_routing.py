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


# T-122 (FR-123, AC-54; Zest 2.0): help questions are routed in code; cooking requests that say "help" are not
@pytest.mark.parametrize("text", ["help", "Help!", "what can I say?", "What can you do", "how does this work?",
                                  "How do I start", "how to use Zest"])
def test_t122_help_questions_route_to_help(text):
    r = route(text, STORE)
    assert r is not None and r.intent == "help" and r.confidence == 1.0


@pytest.mark.parametrize("text,intent", [
    ("help me make paneer butter masala", "named_dish"),  # a cooking request, not a help question
    ("can you help me make Chole tonight", "named_dish"),
])
def test_t122_cooking_requests_mentioning_help_keep_their_route(text, intent):
    assert route(text, STORE).intent == intent


def test_t122_long_or_partial_messages_are_not_help():
    assert route("what can I say to get a quick dinner that is light and has no onions in it?", STORE) is None
    assert route("I need help choosing something cooling", STORE) is None
