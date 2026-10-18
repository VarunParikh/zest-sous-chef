"""Every suggestion carries "Why this?" (FR-63, US-18; AC-20): a reason, and the score breakdown where there is a score."""
from tests.acceptance.chat_harness import find, intent, say, start

MOOD = "I am feeling indulgent"


def _why(msg):
    return next(c for c in msg["cards"] if c["type"] == "why_this")["breakdown"]


def _sums(b):
    assert abs(sum(b["contributions"].values()) - b["final"]) < 1e-9


def test_mood_pick_explains_reason_drivers_and_runners_up(chat_app, fake):
    _, client = chat_app
    fake.intents[MOOD] = intent("mood_intent", mood_tags=["indulgent"])
    turn = say(client, start(client), MOOD).json()
    b = _why(find(turn, "MSG-MOOD-ADD"))
    assert b["kind"] == "dish" and b["reason"] and b["drivers"] and len(b["alternatives"]) == 2
    assert all({"dish_id", "name", "final"} <= set(a) for a in b["alternatives"])
    _sums(b)


def test_addon_explains_why(chat_app, fake):
    _, client = chat_app
    fake.intents[MOOD] = intent("mood_intent", mood_tags=["indulgent"])
    turn = say(client, start(client), MOOD).json()
    b = _why(find(turn, "MSG-ADDON"))
    assert b["kind"] == "addon" and b["reason"].startswith("Chosen for") and b["anchor"]
    assert {"curated_strength", "vector_rank", "fused_rank"} <= set(b["retrieval"])
    _sums(b)


def test_photo_pick_explains_why(chat_app, fake):
    _, client = chat_app
    sid = start(client)
    card = client.post(f"/api/v1/sessions/{sid}/chat", json={"text": "", "sample_photo_id": "RF03"}).json()["messages"][0]["cards"][0]
    ok = client.post(f"/api/v1/sessions/{sid}/action", json={"type": "confirm", "payload": {"confirm_id": card["confirm_id"], "choice": "yes"}}).json()
    b = _why(find(ok, "MSG-PHOTO-OK"))
    assert b["kind"] == "photo" and "of the items you have" in b["reason"] and len(b["alternatives"]) == 2
    _sums(b)


def test_persona_block_explains_the_alternative(chat_app, fake):
    _, client = chat_app
    fake.intents["I want to make pasta"] = intent("named_dish", dish_name="pasta")
    jain = {"diet": "Jain (No Root Veggies / Pure Veg)", "faith": "Jain (Strict Root-Free)"}
    b = _why(find(say(client, start(client, jain), "I want to make pasta").json(), "MSG-PERSONA-BLOCK"))
    assert b["kind"] == "alternative" and "Jain" in b["reason"] and b["alternatives"]
    _sums(b)


def test_unknown_dish_chips_explain_the_ranking(chat_app, fake):
    _, client = chat_app
    fake.intents["I want to cook ratatouille"] = intent("named_dish", dish_name="ratatouille")
    b = _why(find(say(client, start(client), "I want to cook ratatouille").json(), "MSG-TXT-UNKNOWN"))
    assert b["kind"] == "nearest" and len(b["alternatives"]) == 3 and b["reason"]
