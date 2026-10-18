"""Open requests follow the levers; no repeats in a session (ADR-004 v3, C45). CONTEXT_NOW is 19:30: dinner."""
from tests.acceptance.chat_harness import find, intent, say, start

GOURMET = {"weights": {"culinary_pairing": 0, "purchase_history": 0, "market_trend": 0, "persona_gourmet": 1},
           "gourmet_affinity": 1.0, "artisanal_organic": 1.0}


def _open(fake, text):
    fake.intents[text] = intent("mood_intent", mood_tags=[])


def _pick(turn):
    return next(c for c in find(turn, "MSG-MOOD-ADD")["cards"] if c["type"] == "dish_added")["dish_id"]


def _addon_name(turn):
    m = next((m for m in turn["messages"] if m["template_id"] == "MSG-ADDON"), None)
    return m["cards"][0]["item"]["name"] if m else None


def test_open_dinner_request_ranks_every_main_course(chat_app, fake):
    app, client = chat_app
    _open(fake, "I am hungry")
    sid = start(client)
    say(client, sid, "I am hungry")
    rows = client.get(f"/api/v1/sessions/{sid}/inspector").json()["rows"]
    mains = [d for d in app.state.store.dishes if d.dish.course == "main"]
    assert len(rows) == len(mains) and all(r["lexical_rank"] is None and r["vector_rank"] is None for r in rows)
    assert {app.state.store.dish(r["candidate_id"]).dish.course for r in rows} == {"main"}


def test_levers_change_the_open_pick(chat_app, fake):
    _, client = chat_app
    _open(fake, "surprise me")
    plain = _pick(say(client, start(client), "surprise me").json())
    gourmet = _pick(say(client, start(client, GOURMET), "surprise me").json())
    assert plain != gourmet


def test_personas_change_the_open_pick(chat_app, fake):
    app, client = chat_app
    _open(fake, "what's for dinner")
    presets = {p.name if hasattr(p, "name") else n: p for n, p in app.state.presets.items()}
    karan = _pick(say(client, start(client, presets["Karan Malhotra"].model_dump(mode="json")), "what's for dinner").json())
    meera = _pick(say(client, start(client, presets["Meera Shah"].model_dump(mode="json")), "what's for dinner").json())
    assert karan != meera


def test_no_dish_repeats_within_a_session(chat_app, fake):
    _, client = chat_app
    _open(fake, "surprise me")
    sid = start(client)
    first = say(client, sid, "surprise me").json()
    second = say(client, sid, "surprise me").json()
    assert _pick(first) != _pick(second)
    assert _addon_name(first) is None or _addon_name(first) != _addon_name(second)


def test_a_stated_mood_keeps_hybrid_retrieval(chat_app, fake):
    _, client = chat_app
    fake.intents["I want to eat something sweet"] = intent("mood_intent", mood_tags=["sweet"])
    sid = start(client)
    say(client, sid, "I want to eat something sweet")
    rows = client.get(f"/api/v1/sessions/{sid}/inspector").json()["rows"]
    assert any(r["lexical_rank"] is not None or r["vector_rank"] is not None for r in rows) and len(rows) <= 25  # DISH_POOL since C53 (was 15)
