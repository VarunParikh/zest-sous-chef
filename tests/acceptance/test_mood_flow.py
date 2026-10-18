"""Mood flow end to end with a fake Ollama (US-13; FR-40, 41, 42, 63; AC-09, 29, 30; T-085, T-086)."""
import pytest

from backend.engine.context import build_context
from backend.flows.templates import TEMPLATES
from backend.retrieval.retriever import Retriever
from backend.session.levers import LeverSet
from tests.acceptance.chat_harness import intent, say, start, trace, find

MOOD = "I am feeling indulgent"


def _setup(fake):
    fake.intents[MOOD] = intent("mood_intent", mood_tags=["indulgent"])


def _cards(msg):
    return {c["type"]: c for c in msg["cards"]}


def test_t085_top_dish_carted_two_swaps_and_undo(chat_app, fake):
    app, client = chat_app
    _setup(fake)
    sid = start(client)
    r = say(client, sid, MOOD)
    assert r.status_code == 200
    turn = r.json()
    msg = find(turn, "MSG-MOOD-ADD")
    cards = _cards(msg)
    added = cards["dish_added"]
    assert turn["messages"][-1]["template_id"] == "MSG-ADDON"  # US-19: one add-on follows the main reply
    assert msg["text"] == (f"Feeling indulgent? Let's go with {added['dish_name']}: Rich, creamy and a weekend favourite. "
                           "I've added the ingredients. ✅")
    assert turn["cart_changed"] is True and [d["dish_id"] for d in turn["cart"]["dishes"]] == [added["dish_id"]]
    assert added["line_count"] == turn["cart"]["item_count"] and added["dish_total_inr"] == turn["cart"]["subtotal_inr"]
    assert len(cards["swap_options"]["options"]) == 2 and cards["undo"]["suggestion_id"] == added["suggestion_id"]
    assert turn["suggestions"] == [{"suggestion_id": added["suggestion_id"], "type": "dish",
                                    "candidate_id": added["dish_id"], "rank": 1}]
    # The engine chose it: the top eligible dish for this snapshot, with its two runners-up as swaps.
    session = app.state.sessions.get(sid)
    rec = session.recommend_dishes(f"{MOOD} indulgent", build_context(settings=app.state.settings), app.state.store,
                                   app.state.retriever)
    assert [s.candidate_id for s in rec.shown] == [added["dish_id"], *[o["dish_id"] for o in cards["swap_options"]["options"]]]
    # "Why this?" carries the breakdown; contributions sum to the final score (AC-20).
    why = cards["why_this"]["breakdown"]
    assert abs(sum(why["contributions"].values()) - why["final"]) < 1e-9 and set(why["weights_effective"]) == {"s_p", "s_h", "s_t", "s_g"}
    # Swap, then Undo returns the cart to its prior (empty) state (AC-30).
    alt = cards["swap_options"]["options"][0]["dish_id"]
    act = lambda t, **p: client.post(f"/api/v1/sessions/{sid}/action", json={"type": t, "payload": p}).json()
    swapped = act("swap", suggestion_id=added["suggestion_id"], alt_dish_id=alt)
    assert [d["dish_id"] for d in swapped["cart"]["dishes"]] == [alt]
    undone = act("undo", suggestion_id=added["suggestion_id"])
    assert undone["cart"]["item_count"] == 0
    events = [e["event"] for e in trace(app)]
    assert {"retrieval_candidates", "suggestion_shown", "cart_mutated", "intent_classified"} <= set(events)


def test_mood_add_keeps_earlier_items(chat_app, fake):
    app, client = chat_app
    _setup(fake)
    sid = start(client)
    from backend.cart import service
    from tests.acceptance.test_cart_api import CTX

    service.add_dish(app.state.sessions.get(sid), "D01", "text", CTX, app.state.store)
    turn = say(client, sid, MOOD).json()
    assert turn["cart"]["dishes"][0]["dish_id"] == "D01" and len(turn["cart"]["dishes"]) == 2


def test_t086_no_eligible_dish_adds_nothing_and_says_why(chat_app, fake):
    app, client = chat_app
    _setup(fake)
    # Lexical pool on purpose: the test hash embedder's neighbours are arbitrary (pickles, chutneys) and some pass
    # Keto plus Vegan, so a hybrid pool here would not be a "no eligible dish" case. The fallback is reported.
    # The pool stays at 15 here: this test is about the no-eligible reply, and the wider default pool (25, C53)
    # reaches lexical matches that pass Keto plus Vegan, so it would no longer be a "no eligible dish" case.
    app.state.settings = app.state.settings.model_copy(update={"dish_pool": 15})
    app.state.retriever = Retriever(app.state.store, None, app.state.settings, app.state.tracer)
    sid = start(client, {"specialized_diets": ["Keto Diet", "Vegan"]})
    turn = say(client, sid, MOOD).json()
    rec = app.state.sessions.get(sid).last_recommendation
    assert rec.scored and not any(s.breakdown.eligible for s in rec.scored)  # every pooled dish was filtered in code
    assert turn["fallbacks_used"] == ["vector"]
    msg = turn["messages"][-1]
    assert msg["template_id"] == "MSG-MOOD-NONE" and msg["cards"] == []
    assert msg["text"] == TEMPLATES["MSG-MOOD-NONE"].format(constraint="Keto Diet and Vegan")
    assert turn["cart"]["item_count"] == 0 and turn["cart_changed"] is False and turn["suggestions"] == []
    assert "reason" not in fake.calls


def test_invalid_reason_line_falls_back_to_the_template(chat_app, fake):
    _, client = chat_app
    _setup(fake)
    fake.reason = {"reason": "Only ₹99 today, grab it before stock runs out"}
    msg = find(say(client, start(client), MOOD).json(), "MSG-MOOD-ADD")
    assert "Matches your mood and fits your settings" in msg["text"] and "99" not in msg["text"]
    assert _cards(msg)["dish_added"]["reason"] == "Matches your mood and fits your settings"


def test_fr02_levers_sent_mid_session_flag_the_banner_but_do_not_change_the_dish(chat_app, fake):
    # Two sessions with the same snapshot and history; only one sends edited levers on its second turn. The second
    # pick must match (FR-02). Comparing within one session would see the no-repeat rule (ADR-004 v3, C45) instead.
    _, client = chat_app
    _setup(fake)
    edited = LeverSet(diet="Pure Veg (Strict)", gourmet_affinity=1.0).model_dump(mode="json")
    a, b = start(client), start(client)
    first = say(client, a, MOOD).json()
    say(client, b, MOOD)
    with_edit = say(client, a, MOOD, levers=edited).json()
    without = say(client, b, MOOD).json()
    pick = lambda t: _cards(find(t, "MSG-MOOD-ADD"))["dish_added"]["dish_id"]
    assert pick(with_edit) == pick(without)
    assert with_edit["levers_changed_since_snapshot"] is True and first["levers_changed_since_snapshot"] is False


@pytest.mark.parametrize("line", ["Fresh, tangy and healthy for tonight", "Boosts immunity on a cold day",
                                  "A nutritious pick for the week", "Light and low-calorie comfort"])
def test_c54_health_claim_words_fail_the_reason_validator(line):
    """C54 (Agent Design v0.4 §6.3): the C50 claim words make the template reason show instead."""
    from backend.flows.mood import valid_reason

    assert not valid_reason(line, "Suggestion: Garden Salad | Tags: fresh, healthy, light | Drivers: x")
    assert valid_reason("Fresh, tangy and light for tonight", "Suggestion: Garden Salad | Tags: fresh, light | Drivers: x")
