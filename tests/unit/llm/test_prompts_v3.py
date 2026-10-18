"""C54 (Agent Design v0.4 §6.1): A2 uses intent_classify_v3; its examples are new phrasings, never E2 rows."""
import json
import re

from backend.llm import prompts


def test_intent_prompt_is_v3():
    assert prompts.version("intent_classify") == "intent_classify_v3"


def test_v3_separates_the_confused_intents():
    text = prompts.text("intent_classify")
    for rule in ("named_dish", "recipe_text", "variant_request", "cart_edit", "unsafe", "unsupported"):
        assert rule in text
    assert "not cart_edit" in text  # an instruction change is unsafe even when it also asks to add items


def test_v3_examples_are_not_e2_utterances():
    examples = {m.strip().lower() for m in re.findall(r"^Message: (.*)$", prompts.text("intent_classify"), re.M)}
    rows = {json.loads(l)["text"].strip().lower() for l in open("eval/datasets/utterances_v1.jsonl")}
    assert examples and not (examples & rows)  # v2 shared one dev row (U15); v3 shares none
