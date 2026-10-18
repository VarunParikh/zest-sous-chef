"""Hunger and "suggest something" requests run the mood flow with the persona levers (FR-40; C43).
The intent model's labels are faked here; the real model is checked live with intent_classify_v2."""
from backend.llm import prompts
from tests.acceptance.chat_harness import find, intent, say, start


def _dish(app, turn):
    added = next(c for c in find(turn, "MSG-MOOD-ADD")["cards"] if c["type"] == "dish_added")
    return app.state.store.dish(added["dish_id"]).dish


def test_intent_prompt_v2_names_hunger_and_suggestions():
    text = prompts.text("intent_classify")
    assert prompts.version("intent_classify") == "intent_classify_v2"
    for example in ("I am hungry", "surprise me", "what should I have for dinner", "you suggest"):
        assert example in text


def test_generic_hunger_in_the_evening_carts_a_main_course(chat_app, fake):
    app, client = chat_app  # CONTEXT_NOW is 19:30: dinner time
    fake.intents["I am hungry"] = intent("mood_intent", mood_tags=[])
    turn = say(client, start(client), "I am hungry").json()
    msg = find(turn, "MSG-MOOD-ADD")
    assert msg["text"].startswith("Feeling hungry? Let's go with")
    assert _dish(app, turn).course == "main"


def test_meal_word_steers_the_course(chat_app, fake):
    app, client = chat_app
    text = "help me pick what to have for breakfast"
    fake.intents[text] = intent("mood_intent", mood_tags=[])
    assert _dish(app, say(client, start(client), text).json()).course == "breakfast"


def test_surprise_me_reaches_the_mood_flow(chat_app, fake):
    app, client = chat_app
    fake.intents["surprise me"] = intent("mood_intent", mood_tags=[])
    turn = say(client, start(client), "surprise me").json()
    assert find(turn, "MSG-MOOD-ADD") and turn["cart"]["item_count"] > 0


def test_a_stated_mood_is_not_forced_to_a_main(chat_app, fake):
    app, client = chat_app
    fake.intents["I want to eat something sweet"] = intent("mood_intent", mood_tags=["sweet"])
    turn = say(client, start(client), "I want to eat something sweet").json()
    assert find(turn, "MSG-MOOD-ADD")["text"].startswith("Feeling sweet?")
    assert _dish(app, turn).course in {"dessert", "beverage", "side", "main", "breakfast"}  # ranked by mood, not by meal


def test_off_topic_suggestion_still_redirected_by_the_model(chat_app, fake):
    _, client = chat_app
    fake.intents["suggest a movie for tonight"] = intent("off_topic")
    assert find(say(client, start(client), "suggest a movie for tonight").json(), "MSG-REDIRECT")


def test_tonight_means_dinner(chat_app, fake):
    from backend.flows.mood import meal_for

    class Afternoon:
        part_of_day = "afternoon"

    assert meal_for("what should I cook tonight", [], Afternoon()) == "dinner"
    assert meal_for("I am hungry", [], Afternoon()) == "snack"
    assert meal_for("something sweet", ["sweet"], Afternoon()) is None
