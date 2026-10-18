"""Add-on suggestions after carting (US-19; FR-62, 64, 117 to 119; AC-43 to AC-45; MSG-ADDON)."""
from backend.engine.eligibility import check_dish
from backend.retrieval.retriever import Retriever
from backend.session.levers import LeverSet
from backend.transcripts.source import default_chain
from tests.acceptance.chat_harness import extraction, intent, line, say, start, trace
from tests.unit.retrieval.conftest import BrokenVector

MOOD = "I am feeling indulgent"
RASAM_URL = "https://www.youtube.com/watch?v=6YVx0i_hrZ0"


def _msgs(turn):
    return {m["template_id"]: m for m in turn["messages"]}


def _addon(turn):
    msg = _msgs(turn).get("MSG-ADDON")
    return msg, (msg["cards"][0] if msg else None)


def test_mood_cart_offers_one_addon_and_nothing_is_added_without_a_tap(chat_app, fake):
    app, client = chat_app
    fake.intents[MOOD] = intent("mood_intent", mood_tags=["indulgent"])
    sid = start(client)
    turn = say(client, sid, MOOD).json()
    msg, card = _addon(turn)
    assert card is not None and card["type"] == "addon_suggestion"
    dish = turn["cart"]["dishes"][0]["name"]
    assert msg["text"] == f"{card['item']['name']} goes well with {dish}. Add it?"
    # C18: the price excludes ingredients already in the cart, so a companion made only from them costs ₹0 extra.
    assert card["reason"].startswith("Chosen for") and card["item"]["price_inr"] >= 0
    assert len(turn["cart"]["dishes"]) == 1  # FR-64: suggest only
    assert [m["template_id"] for m in turn["messages"]][-1] == "MSG-ADDON"  # after the main reply

    act = lambda choice: client.post(f"/api/v1/sessions/{sid}/action",
                                     json={"type": "add_on", "payload": {"suggestion_id": card["suggestion_id"], "choice": choice}})
    added = act("add").json()
    assert [d["name"] for d in added["cart"]["dishes"]] == [dish, card["item"]["name"]]
    reply = added["messages"][0]
    assert reply["template_id"] == "MSG-EDIT-OK" and any(c["type"] == "undo" for c in reply["cards"])
    assert act("add").status_code == 409  # used once
    undo = next(c for c in reply["cards"] if c["type"] == "undo")
    back = client.post(f"/api/v1/sessions/{sid}/action", json={"type": "undo", "payload": {"suggestion_id": undo["suggestion_id"]}}).json()
    assert [d["name"] for d in back["cart"]["dishes"]] == [dish]


def test_decline_changes_nothing(chat_app, fake):
    _, client = chat_app
    fake.intents[MOOD] = intent("mood_intent", mood_tags=["indulgent"])
    sid = start(client)
    turn = say(client, sid, MOOD).json()
    _, card = _addon(turn)
    r = client.post(f"/api/v1/sessions/{sid}/action", json={"type": "add_on", "payload": {"suggestion_id": card["suggestion_id"], "choice": "decline"}}).json()
    assert r["messages"][0]["template_id"] == "MSG-ADDON-DECLINED" and r["cart"] == turn["cart"] and r["cart_changed"] is False


def test_youtube_text_and_named_dish_carts_offer_an_addon(chat_app, fake):
    _, client = chat_app
    fake.extractions["Mysore rasam"] = extraction("Mysore Rasam", line("toor dal", 60, "g"), line("tomato", 150, "g"))
    sid = start(client)
    assert _addon(say(client, sid, RASAM_URL).json())[1] is not None
    fake.intents["I want to make dal chawal"] = intent("named_dish", dish_name="dal chawal")
    assert _addon(say(client, sid, "I want to make dal chawal").json())[1] is not None
    fake.intents["Kadai paneer: 250 g paneer"] = intent("recipe_text", dish_name="kadai paneer")
    fake.extractions["Kadai paneer: 250 g paneer"] = extraction("kadai paneer", line("paneer", 250, "g"))
    say(client, sid, "new dish")
    assert _addon(say(client, sid, "Kadai paneer: 250 g paneer").json())[1] is not None


def test_photo_cart_offers_an_addon(chat_app, fake):
    _, client = chat_app
    sid = start(client)
    card = client.post(f"/api/v1/sessions/{sid}/chat", json={"text": "", "sample_photo_id": "RF03"}).json()["messages"][0]["cards"][0]
    ok = client.post(f"/api/v1/sessions/{sid}/action", json={"type": "confirm", "payload": {"confirm_id": card["confirm_id"], "choice": "yes"}}).json()
    assert _addon(ok)[1] is not None


def test_no_addon_after_a_swap(chat_app, fake):
    _, client = chat_app
    fake.intents[MOOD] = intent("mood_intent", mood_tags=["indulgent"])
    sid = start(client)
    turn = say(client, sid, MOOD).json()
    swaps = next(c for m in turn["messages"] for c in m["cards"] if c["type"] == "swap_options")
    r = client.post(f"/api/v1/sessions/{sid}/action",
                    json={"type": "swap", "payload": {"suggestion_id": swaps["suggestion_id"], "alt_dish_id": swaps["options"][0]["dish_id"]}}).json()
    assert "MSG-ADDON" not in _msgs(r)


def test_addon_never_breaks_the_persona(chat_app, fake):
    app, client = chat_app
    jain = {"diet": "Jain (No Root Veggies / Pure Veg)", "faith": "Jain (Strict Root-Free)"}
    fake.intents["I want to make jain pav bhaji"] = intent("named_dish", dish_name="jain pav bhaji")
    sid = start(client, jain)
    turn = say(client, sid, "I want to make jain pav bhaji").json()
    _, card = _addon(turn)
    if card is not None:  # when one is offered it must pass the Jain masks (FR-119)
        rec = next(d for d in app.state.store.dishes if d.dish.name == card["item"]["name"])
        assert check_dish(rec, LeverSet.model_validate(jain), app.state.store, kind="addon").eligible
    assert any(e["event"] == "retrieval_candidates" and e["data"].get("kind") == "addon" for e in trace(app))


def test_vector_store_down_still_offers_curated_addons(chat_app, fake):
    app, client = chat_app
    app.state.retriever = Retriever(app.state.store, BrokenVector(), app.state.settings, app.state.tracer)
    fake.intents["I want to make dal chawal"] = intent("named_dish", dish_name="dal chawal")
    sid = start(client)
    turn = say(client, sid, "I want to make dal chawal").json()
    assert _addon(turn)[1] is not None and "vector" in turn["fallbacks_used"]


def test_inspector_shows_the_addon_pool(chat_app, fake):
    _, client = chat_app
    fake.intents[MOOD] = intent("mood_intent", mood_tags=["indulgent"])
    sid = start(client)
    say(client, sid, MOOD)
    addon = client.get(f"/api/v1/sessions/{sid}/inspector").json()["addon"]
    assert addon["anchor"] and addon["rows"]
    assert {"curated_rank", "curated_strength", "vector_rank", "fused_rank", "eligible", "final", "name"} <= set(addon["rows"][0])
