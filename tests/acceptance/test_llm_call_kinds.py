"""Each flow labels its model calls (Data Model v0.5 §11, C61): the E11 breakdown reads these from the trace."""
from tests.acceptance.chat_harness import extraction, image_bytes, intent, line, say, start, trace, upload

MOOD = "I am feeling indulgent"
RECIPE = "dal: 150 g toor dal, 1 tsp turmeric, salt"


def _kinds(app, sid):
    return [e["data"]["call"] for e in trace(app) if e["event"] == "llm_call" and e["session_id"] == sid]


def test_mood_turn_traces_guard_intent_and_reason(chat_app, fake):
    app, client = chat_app
    fake.intents[MOOD] = intent("mood_intent", mood_tags=["indulgent"])
    sid = start(client)
    assert say(client, sid, MOOD).status_code == 200
    kinds = _kinds(app, sid)
    assert kinds[:2] == ["guard", "intent"] and "reason" in kinds
    assert all(e["data"]["outcome"] == "ok" for e in trace(app) if e["event"] == "llm_call")


def test_text_recipe_turn_traces_extract(chat_app, fake):
    app, client = chat_app
    fake.intents[RECIPE] = intent("recipe_text")
    fake.extractions["toor dal"] = extraction("Dal", line("toor dal", 150, "g"), line("turmeric", 1, "tsp"))
    sid = start(client)
    assert say(client, sid, RECIPE).status_code == 200
    assert "extract" in _kinds(app, sid)


def test_photo_upload_traces_vision(chat_app, fake):
    app, client = chat_app
    app.state.settings = app.state.settings.model_copy(update={"vision_provider": "ollama"})
    sid = start(client)
    assert upload(client, sid, image_bytes()).status_code == 200
    assert "vision" in _kinds(app, sid)
