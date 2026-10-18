"""Input guard, rules arm (ADR-006; FR-10, 12; Agent Design §7.1).

Runs in code on user text and fetched text before any model sees it. Order: injection,
then hazard, then off-topic. Cooking verbs that sound violent ("attack the onions",
"kill the bitterness") are ordinary language: hazard needs a harmful object, not a verb.
Off-topic means no food, cooking or grocery signal at all. The optional classifier
arm (Llama Guard) is measured in E4 before it is adopted.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

from backend.retrieval.text import doc_tokens

INJECTION = [
    r"\b(ignore|disregard|forget|override|bypass)\b.{0,40}\b(instruction|instructions|rules?|guardrails?|filters?|prompt|policy|policies|system)\b",
    r"\b(you are now|from now on you|act as|pretend (you are|to be)|roleplay as)\b",
    r"\b(system|developer|admin)\s*(prompt|mode|override|message)\b",
    r"^\s*(system|assistant|developer)\s*:",
    r"[.!?]\s*(system|assistant|developer)\s*:",
    r"\b(reveal|print|show|repeat)\b.{0,30}\b(system prompt|hidden (prompt|instructions)|your instructions)\b",
    r"\b(jailbreak|dan mode|do anything now)\b",
    r"\b(turn off|disable|remove|switch off)\b.{0,30}\b(diet|halal|jain|filters?|guardrails?|restrictions?|safety)\b",
    r"\bnew rule\b",
    r"\b(approve|place)\b.{0,30}\b(any|every|all)\b.{0,20}\b(order|orders)\b",
    r"\bfor free\b",
    # C54 (ADR-006 v4): instructions aimed at the guardrails, within one sentence
    r"\b(disable|turn off|switch off|bypass|ignore|override|skip|remove|lift)\b[^.!?\n]{0,40}\b(guards?|guardrails?|filters?|"
    r"restrictions?|rules?|safety|allergy|allergens?|diet|dietary|faith|jain|halal|vegan|settings?)\b",
    r"\bpretend\b[^.!?\n]{0,60}\b(off|disabled|does not apply|doesn't apply)\b",
]
HAZARD = [
    r"\b(poison|poisonous|toxin|cyanide|arsenic)\b",
    r"\b(bomb|explosives?|detonat\w*|napalm|molotov)\b",
    r"\b(meth|cocaine|heroin)\b",
    r"\b(kill|hurt|harm|poison)\b.{0,20}\b(someone|somebody|person|people|him|her|my (wife|husband|neighbou?r|boss))\b",
    r"\b(weapon|gun|firearm)\b",
]
COOKING_WORDS = {
    "cook", "cooking", "recipe", "recipes", "dish", "dishes", "food", "meal", "meals", "dinner", "lunch", "breakfast",
    "snack", "snacks", "drink", "drinks", "dessert", "eat", "eating", "hungry", "hunger", "kitchen", "fry", "boil",
    "bake", "roast", "grill", "chop", "cart", "order", "buy", "grocery", "groceries", "pack", "packs", "add", "remove",
    "spicy", "sweet", "cooling", "indulgent", "veg", "vegan", "jain", "halal", "keto", "serves", "servings", "taste",
    "flavour", "flavor", "ingredient", "ingredients", "beat", "whip", "smash", "knead", "stir", "garnish", "bitterness",
    "curry", "salad", "chutney", "tea", "coffee", "juice", "cooler",
    # C43 (owner decision, 2026-10-18): hunger, suggestion and stove words. Real off-topic asks that use them
    # ("suggest a movie") are still redirected, by the intent model labelling them off_topic.
    "starving", "famished", "brunch", "craving", "cravings", "crave", "suggest", "suggestion", "suggestions",
    "recommend", "recommendation", "surprise", "pick", "tonight", "menu", "heat", "flame", "stove", "gas",
}
GREETINGS = {"hi", "hello", "hey", "thanks", "thank", "ok", "okay", "yes", "no", "namaste"}
YOUTUBE = re.compile(r"(youtube\.com/|youtu\.be/)", re.I)


@dataclass
class Screen:
    label: str  # ok | injection | hazard | off_topic
    message_id: str | None
    reasons: list[str] = field(default_factory=list)


class Guard:
    def __init__(self, vocabulary: set[str]):
        self.vocabulary = vocabulary | COOKING_WORDS
        self._inj = [re.compile(p, re.I) for p in INJECTION]
        self._haz = [re.compile(p, re.I) for p in HAZARD]

    def screen(self, text: str, source: str = "user") -> Screen:
        hits = [p.pattern for p in self._inj if p.search(text)]
        if hits:
            return Screen("injection", "MSG-INJECT-DATA" if source == "transcript" else "MSG-REDIRECT", hits)
        if source == "user":
            hits = [p.pattern for p in self._haz if p.search(text)]
            if hits:
                return Screen("hazard", "MSG-HAZARD", hits)
            if YOUTUBE.search(text):
                return Screen("ok", None)
            toks = doc_tokens(text)
            if toks and not _food_signal(toks, self.vocabulary):
                if len(toks) <= 2 and set(toks) <= GREETINGS:
                    return Screen("ok", None)
                return Screen("off_topic", "MSG-REDIRECT", ["no food, cooking or grocery word"])
        return Screen("ok", None)


def _food_signal(toks: list[str], vocab: set[str]) -> bool:
    """Any token (or its singular) or adjacent pair is a food, cooking or grocery word."""
    for t in toks:
        if t in vocab or t.rstrip("s") in vocab or (t.endswith("es") and t[:-2] in vocab):
            return True
    return any(f"{a} {b}" in vocab for a, b in zip(toks, toks[1:]))


@lru_cache(maxsize=1)
def default_guard() -> Guard:
    """Vocabulary from the seed: lexicon terms and aliases, synonyms, dish names, aliases and moods."""
    from backend.catalogue.seed import load_dishes, load_lexicon, load_synonyms

    lex = load_lexicon()
    words: set[str] = set()
    for e in lex.entries.values():
        for name in (e.term, *e.aliases):
            words.add(name)
            words.update(doc_tokens(name))
    for s in load_synonyms():
        words.update(doc_tokens(s["query_term"]))
    for rec in load_dishes(lexicon=lex):
        d = rec.dish
        for name in (d.name, *d.aliases, *d.mood_tags):
            words.update(doc_tokens(name))
    words -= {"of", "and", "the", "a", "in", "with", "style", "international", "case"}
    return Guard(words)
