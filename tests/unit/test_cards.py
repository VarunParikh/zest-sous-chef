"""Typed cards and TurnResponse (API Spec §4.4, §4.5)."""
import pytest
from pydantic import TypeAdapter, ValidationError

from backend.flows.cards import Card, TurnResponse

EXAMPLES = [
    {"type": "starter_chips", "chips": ["YouTube link", "Upload photo"]},
    {"type": "dish_added", "suggestion_id": "sg_1", "dish_id": "D01", "dish_name": "Butter Chicken",
     "reason": "Rich", "line_count": 9, "dish_total_inr": 412},
    {"type": "swap_options", "suggestion_id": "sg_1", "options": [{"dish_id": "D02", "name": "Shahi Paneer"}]},
    {"type": "undo", "suggestion_id": "sg_1"},
    {"type": "why_this", "suggestion_id": "sg_1", "breakdown": None},
    {"type": "clarify", "question_id": "q_1", "prompt": "Which methi?",
     "options": [{"value": "leaves", "label": "Fenugreek leaves"}]},
    {"type": "confirm", "confirm_id": "c_1", "prompt": "Continue?",
     "options": [{"value": "yes", "label": "Clear"}, {"value": "cancel", "label": "Cancel"}]},
    {"type": "addon_suggestion", "suggestion_id": "sg_2",
     "item": {"name": "Jeera Rice", "variant": None, "price_inr": 95}, "reason": "Goes well"},
    {"type": "substitution", "substitution_id": "sb_1", "from_item": "Cream", "to_item": "Cashew paste",
     "price_delta_inr": -12, "flavour_note": "Slightly nutty"},
    {"type": "photo_consent", "notice": "Your photo is sent to Google."},
    {"type": "sample_photos", "photos": [{"id": "sp_01", "caption": "Fridge", "label": "Sample"}]},
    {"type": "notice", "level": "warning", "template_id": "MSG-PERSONA-WARN", "text": "Your settings overlap"},
    {"type": "cart_summary", "item_count": 3, "subtotal_inr": 120},
]
ADAPTER = TypeAdapter(Card)


def test_all_thirteen_card_types_round_trip():
    assert len({e["type"] for e in EXAMPLES}) == 13
    for e in EXAMPLES:
        assert ADAPTER.validate_python(e).model_dump(mode="json") == e


def test_unknown_card_type_and_three_swaps_rejected():
    with pytest.raises(ValidationError):
        ADAPTER.validate_python({"type": "bogus"})
    three = [{"dish_id": f"D0{i}", "name": "x"} for i in range(3)]
    with pytest.raises(ValidationError):
        ADAPTER.validate_python({"type": "swap_options", "suggestion_id": "sg", "options": three})


def test_turn_response_defaults():
    t = TurnResponse(turn_id="t_0001", messages=[])
    body = t.model_dump(mode="json")
    assert body["cart"] == {"dishes": [], "item_count": 0, "subtotal_inr": 0}
    assert body["cart_changed"] is False and body["pending"] is None
    assert body["suggestions"] == [] and body["notices"] == [] and body["fallbacks_used"] == []
