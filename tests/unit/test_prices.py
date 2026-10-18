"""Prices in replies equal the catalogue (US-21; FR-79; AC-14; T-061)."""
from backend.flows.prices import correct_prices


def test_t061_wrong_price_corrected_and_right_one_kept():
    known = {"Salted Butter": 58, "Paneer (Full fat)": 68, "total": 126}
    text = "Salted Butter is ₹58 and Paneer (Full fat) costs ₹99. Your total is ₹157."
    out, fixes = correct_prices(text, known)
    assert out == "Salted Butter is ₹58 and Paneer (Full fat) costs ₹68. Your total is ₹126."
    assert fixes == [("Paneer (Full fat)", 99, 68), ("total", 157, 126)]


def test_rupee_amount_without_a_known_item_is_removed():
    out, fixes = correct_prices("Saffron is just Rs. 450 today!", {"Salted Butter": 58})
    assert "450" not in out and fixes == [(None, 450, None)]


def test_text_without_prices_is_unchanged():
    assert correct_prices("Feeling indulgent? ✅", {"total": 10}) == ("Feeling indulgent? ✅", [])


def test_build_turn_applies_the_gate_to_assistant_messages():
    from backend.flows.cards import Message
    from backend.flows.turns import build_turn
    from backend.session.levers import LeverSet
    from backend.session.store import SessionStore

    s = SessionStore().create(LeverSet())
    msg = Message(message_id="m_1", role="assistant", text="Your total is ₹999.")
    turn = build_turn(s, [msg], known_prices={"total": 412})
    assert turn.messages[0].text == "Your total is ₹412."
