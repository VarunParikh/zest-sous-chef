"""Inspector endpoint (API Spec §4.8; FR-115; US-39; T-046 API part) and cart icons (API Spec v0.6 §4.6; C41)."""
from backend.cart import service
from tests.acceptance.chat_harness import intent, say, start
from tests.acceptance.test_cart_api import CTX

MOOD = "I am feeling indulgent"


def test_inspector_is_empty_before_any_suggestion(chat_app):
    _, client = chat_app
    sid = start(client)
    assert client.get(f"/api/v1/sessions/{sid}/inspector").json() == {"rows": [], "shown": [], "weights_effective": {}}


def test_inspector_lists_the_pool_after_a_mood_suggestion(chat_app, fake):
    _, client = chat_app
    fake.intents[MOOD] = intent("mood_intent", mood_tags=["indulgent"])
    sid = start(client)
    added = next(c for c in say(client, sid, MOOD).json()["messages"][-1]["cards"] if c["type"] == "dish_added")
    body = client.get(f"/api/v1/sessions/{sid}/inspector").json()
    assert len(body["rows"]) >= 15 and body["shown"][0] == added["dish_id"] and len(body["shown"]) == 3  # FR-111
    row = body["rows"][0]
    assert {"candidate_id", "name", "lexical_rank", "vector_rank", "vector_distance", "fused_rank", "eligible",
            "filtered_by", "components", "final"} <= set(row)
    assert set(body["weights_effective"]) == {"s_p", "s_h", "s_t", "s_g"}
    assert client.get("/api/v1/sessions/s_nope/inspector").status_code == 404


def test_cart_view_carries_category_icons_and_course(chat_app):
    app, client = chat_app
    sid = start(client)
    service.add_dish(app.state.sessions.get(sid), "D06", "text", CTX, app.state.store)
    (dish,) = client.get(f"/api/v1/sessions/{sid}/cart").json()["dishes"]
    assert dish["course"] == "main"
    paneer = next(ln for ln in dish["lines"] if ln["ingredient_name"] == "paneer")
    assert paneer["icon"] == app.state.store.variant(paneer["variant_id"]).icon == "dairy"
