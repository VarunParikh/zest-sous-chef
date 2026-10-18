"""Text recipe flow (US-11; FR-30, 31, 33, 13; NFR-10; T-083, T-084, T-090, T-012 text part)."""
from tests.acceptance.chat_harness import extraction, intent, line, say, start, find


def _msg(r):
    return r.json()["messages"][-1]


def _recipe(fake, text, dish, *lines):
    fake.intents[text] = intent("recipe_text", dish_name=dish)
    fake.extractions[text] = extraction(dish, *lines)


def _dishes(r):
    return r.json()["cart"]["dishes"]


def test_t083_three_messages_cart_immediately_under_one_open_dish(chat_app, fake):
    _, client = chat_app
    sid = start(client)
    _recipe(fake, "Kadai paneer: 250 g paneer", "kadai paneer", line("paneer", 250, "g"))
    _recipe(fake, "then 2 capsicum and one onion", None, line("capsicum", 2, "piece"), line("onion", 1, "piece"))
    _recipe(fake, "a tbsp of garam masala and salt", None, line("garam masala", 1, "tbsp"), line("salt", None, "pinch", True))
    r1 = say(client, sid, "Kadai paneer: 250 g paneer")
    assert find(r1.json(), "MSG-TXT-DRAFT") and len(_dishes(r1)) == 1 and r1.json()["cart_changed"]
    assert find(r1.json(), "MSG-TXT-DRAFT")["text"] == "Got it. Adding 1 ingredients for Kadai Paneer. Say 'new dish' when you start another. ✅"
    r2 = say(client, sid, "then 2 capsicum and one onion")
    r3 = say(client, sid, "a tbsp of garam masala and salt")
    (dish,) = _dishes(r3)
    assert [ln["ingredient_name"] for ln in dish["lines"]] == ["paneer", "capsicum", "onion", "garam masala", "salt"]
    assert len(_dishes(r2)[0]["lines"]) == 3  # carted message by message (FR-30)
    salt = dish["lines"][-1]
    assert salt["estimated"] is True  # a pinch: an estimate (FR-14)
    # "new dish" closes the open dish; the next recipe starts a second one.
    assert _msg(say(client, sid, "new dish"))["template_id"] == "MSG-THANKS"
    _recipe(fake, "Jeera rice with 200 g rice", "jeera rice", line("rice", 200, "g"))
    r = say(client, sid, "Jeera rice with 200 g rice")
    assert [d["name"] for d in _dishes(r)] == ["Kadai Paneer", "Jeera Rice"]


def test_plural_names_resolve_to_the_singular_term(chat_app, fake):
    _, client = chat_app
    sid = start(client)
    _recipe(fake, "3 tomatoes", "salad", line("tomatoes", 3, "piece"))
    (dish,) = _dishes(say(client, sid, "3 tomatoes"))
    assert dish["lines"][0]["ingredient_name"] == "tomato"


def test_fr31_named_dish_uses_the_stored_recipe(chat_app, fake):
    app, client = chat_app
    sid = start(client)
    fake.intents["I want to make dal chawal"] = intent("named_dish", dish_name="dal chawal")
    r = say(client, sid, "I want to make dal chawal")
    msg = find(r.json(), "MSG-TXT-STORED")
    assert msg["template_id"] == "MSG-TXT-STORED"
    assert msg["text"] == "I'll use my standard Dal Chawal recipe for 2. Tell me if you cook it differently."
    assert [d["dish_id"] for d in _dishes(r)] == ["D01"] and any(c["type"] == "undo" for c in msg["cards"])
    assert "extract" not in fake.calls


def test_t084_unknown_dish_offers_nearest_dishes_then_carts_the_choice(chat_app, fake):
    _, client = chat_app
    sid = start(client)
    fake.intents["I want to cook ratatouille"] = intent("named_dish", dish_name="ratatouille")
    r = say(client, sid, "I want to cook ratatouille")
    msg = _msg(r)
    assert msg["template_id"] == "MSG-TXT-UNKNOWN" and r.json()["cart"]["item_count"] == 0
    (card,) = msg["cards"]
    assert card["type"] == "clarify" and len(card["options"]) == 3
    choice = card["options"][0]
    r = client.post(f"/api/v1/sessions/{sid}/action",
                    json={"type": "answer", "payload": {"question_id": card["question_id"], "choice": choice["value"]}})
    assert [d["dish_id"] for d in r.json()["cart"]["dishes"]] == [choice["value"]]
    assert r.json()["messages"][0]["template_id"] == "MSG-TXT-STORED"


def test_ambiguous_item_asks_then_the_answer_carts_it(chat_app, fake):
    _, client = chat_app
    sid = start(client)
    _recipe(fake, "aloo methi with 300 g potato and a bunch of methi", "aloo methi",
            line("potato", 300, "g"), line("methi", 1, "bunch"))
    r = say(client, sid, "aloo methi with 300 g potato and a bunch of methi")
    (dish,) = _dishes(r)
    assert [ln["ingredient_name"] for ln in dish["lines"]] == ["potato"]  # methi waits for the answer
    ask = next(m for m in r.json()["messages"] if m["template_id"] == "MSG-AMBIG")
    card = ask["cards"][0]
    assert {o["value"] for o in card["options"]} == {"fenugreek leaves", "fenugreek seeds"}
    r = client.post(f"/api/v1/sessions/{sid}/action",
                    json={"type": "answer", "payload": {"question_id": card["question_id"], "choice": "fenugreek leaves"}})
    (dish,) = r.json()["cart"]["dishes"]
    assert [ln["ingredient_name"] for ln in dish["lines"]] == ["potato", "fenugreek leaves"]


def test_unknown_ingredient_is_never_carted_and_asked_about(chat_app, fake):
    _, client = chat_app
    sid = start(client)
    _recipe(fake, "200 g paneer and some unobtainium", "mystery", line("paneer", 200, "g"), line("unobtainium"))
    r = say(client, sid, "200 g paneer and some unobtainium")
    names = [ln["ingredient_name"] for d in _dishes(r) for ln in d["lines"]]
    assert names == ["paneer"]
    unclear = next(m for m in r.json()["messages"] if m["template_id"] == "MSG-EDIT-UNCLEAR")
    assert "unobtainium" in unclear["text"]


def test_t012_text_part_blocked_item_carts_nothing_and_offers_an_alternative(chat_app, fake):
    _, client = chat_app
    sid = start(client, {"diet": "Pure Veg (Strict)"})
    _recipe(fake, "chicken curry with 500 g chicken and 2 onions", "chicken curry",
            line("chicken", 500, "g"), line("onions", 2, "piece"))
    r = say(client, sid, "chicken curry with 500 g chicken and 2 onions")
    msg = _msg(r)
    assert msg["template_id"] == "MSG-PERSONA-BLOCK" and r.json()["cart"]["item_count"] == 0
    assert "chicken" in msg["text"].lower() and "Pure Veg (Strict)" in msg["text"]
    (chip,) = msg["cards"]
    assert chip["type"] == "clarify" and len(chip["options"]) == 1
    r = client.post(f"/api/v1/sessions/{sid}/action",
                    json={"type": "answer", "payload": {"question_id": chip["question_id"], "choice": chip["options"][0]["value"]}})
    assert r.json()["cart"]["item_count"] > 0  # the veg alternative, carted only on the tap


def test_t090_invalid_extraction_is_retried_once_then_rephrase(chat_app, fake):
    _, client = chat_app
    sid = start(client)
    fake.intents["paneer 200 g, capsicum"] = intent("recipe_text")
    fake.extractions["paneer 200 g, capsicum"] = "this is not json"
    r = say(client, sid, "paneer 200 g, capsicum")
    assert _msg(r)["template_id"] == "MSG-REPHRASE" and r.json()["cart"]["item_count"] == 0
    assert fake.calls.count("extract") == 2
