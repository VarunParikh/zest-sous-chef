"""T-129 (FR-127, AC-62; Zest 2.0, from the owner's session log): a swap tapped after Undo asks whether to add that
dish instead, and adding it offers the dish's add-on; nothing returns an error."""
from tests.acceptance.chat_harness import find, intent, say, start

MOOD = "I am feeling indulgent"


def _undone(chat_app, fake):
    app, client = chat_app
    fake.intents[MOOD] = intent("mood_intent", mood_tags=["indulgent"])
    sid = start(client)
    turn = say(client, sid, MOOD).json()
    cards = {c["type"]: c for c in find(turn, "MSG-MOOD-ADD")["cards"]}
    sg, alt = cards["dish_added"]["suggestion_id"], cards["swap_options"]["options"][0]
    act = lambda t, **p: client.post(f"/api/v1/sessions/{sid}/action", json={"type": t, "payload": p})  # noqa: E731
    assert act("undo", suggestion_id=sg).json()["cart"]["item_count"] == 0
    return app, act, sg, alt, cards["dish_added"]["dish_name"]


def test_t129_swap_after_undo_asks_to_add_instead_then_offers_the_add_on(chat_app, fake):
    app, act, sg, alt, undone_name = _undone(chat_app, fake)
    r = act("swap", suggestion_id=sg, alt_dish_id=alt["dish_id"])
    assert r.status_code == 200  # was 409 "That swap is no longer available"
    msg = r.json()["messages"][-1]
    assert msg["template_id"] == "MSG-SWAP-GONE" and undone_name in msg["text"] and alt["name"].split(" (")[0] in msg["text"]
    confirm = next(c for c in msg["cards"] if c["type"] == "confirm")
    assert [o["value"] for o in confirm["options"]] == ["add", "no"]
    assert r.json()["cart"]["item_count"] == 0  # asking changes nothing

    added = act("confirm", confirm_id=confirm["confirm_id"], choice="add").json()
    assert [d["dish_id"] for d in added["cart"]["dishes"]] == [alt["dish_id"]]
    ids = [m["template_id"] for m in added["messages"]]
    assert ids[0] == "MSG-EDIT-OK" and "MSG-ADDON" in ids  # the add-on linked to the dish is suggested too
    new_sg = next(c for c in added["messages"][0]["cards"] if c["type"] == "undo")["suggestion_id"]
    assert act("undo", suggestion_id=new_sg).json()["cart"]["item_count"] == 0  # the added dish can be undone


def test_t129_no_thanks_changes_nothing(chat_app, fake):
    app, act, sg, alt, _ = _undone(chat_app, fake)
    confirm = next(c for c in act("swap", suggestion_id=sg, alt_dish_id=alt["dish_id"]).json()["messages"][-1]["cards"]
                   if c["type"] == "confirm")
    r = act("confirm", confirm_id=confirm["confirm_id"], choice="no").json()
    assert r["messages"][-1]["template_id"] == "MSG-SWAP-GONE-NO" and r["cart"]["item_count"] == 0
    assert act("confirm", confirm_id=confirm["confirm_id"], choice="add").status_code == 409  # answered once only


def test_t129_unknown_or_foreign_swaps_are_still_refused(chat_app, fake):
    app, act, sg, alt, _ = _undone(chat_app, fake)
    assert act("swap", suggestion_id="sg_999", alt_dish_id=alt["dish_id"]).status_code == 409
    assert act("swap", suggestion_id=sg, alt_dish_id="D01").status_code == 409  # not one of its alternatives
