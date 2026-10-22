"""Input lock and stale taps (FR-102, AC-27; API Spec §4.3; T-093, T-094)."""
from tests.acceptance.chat_harness import intent, say, start, find

MOOD = "I am feeling indulgent"


def test_t093_a_second_message_while_one_is_processing_is_session_busy(chat_app, fake):
    app, client = chat_app
    sid = start(client)
    with app.state.sessions.get(sid).busy():  # the first message still holds the lock
        r = say(client, sid, "hi")
        act = client.post(f"/api/v1/sessions/{sid}/action", json={"type": "undo", "payload": {"suggestion_id": "sg_1"}})
    assert r.status_code == 409 and r.json()["error"]["code"] == "SESSION_BUSY" and r.json()["error"]["retryable"]
    assert act.json()["error"]["code"] == "SESSION_BUSY"
    assert [m.role for m in app.state.sessions.get(sid).messages] == ["assistant"]  # the busy message was not taken


def test_t094_a_tap_from_an_earlier_turn_after_the_cart_changed_is_stale(chat_app, fake):
    _, client = chat_app
    fake.intents[MOOD] = intent("mood_intent", mood_tags=["indulgent"])
    sid = start(client)
    cards = {c["type"]: c for c in find(say(client, sid, MOOD).json(), "MSG-MOOD-ADD")["cards"]}
    sg = cards["undo"]["suggestion_id"]
    alt = cards["swap_options"]["options"][0]["dish_id"]
    assert client.post(f"/api/v1/sessions/{sid}/action", json={"type": "undo", "payload": {"suggestion_id": sg}}).status_code == 200
    # The same Undo tapped again is stale. (A swap after Undo is no longer stale: it asks to add instead, FR-127, T-129.)
    stale = client.post(f"/api/v1/sessions/{sid}/action", json={"type": "undo", "payload": {"suggestion_id": sg}})
    assert stale.status_code == 409 and stale.json()["error"]["code"] == "STALE_ACTION"
    swap = client.post(f"/api/v1/sessions/{sid}/action", json={"type": "swap", "payload": {"suggestion_id": sg, "alt_dish_id": alt}})
    assert swap.status_code == 200 and swap.json()["cart"]["item_count"] == 0  # asks; nothing is swapped
