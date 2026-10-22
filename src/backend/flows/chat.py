"""One chat turn (Architecture §4): guard, then intent, then a flow. Code decides; the model only labels."""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.cart import service
from backend.flows.cards import Message, SuggestionRef
from backend.flows.templates import render
from backend.flows.text import CLOSE_WORDS, named_dish_turn, recipe_text_turn
from backend.flows.youtube import youtube_turn
from backend.intent.classify import classify
from backend.intent.routing import route
from backend.transcripts.source import find_url
from backend.llm.client import LLMInvalid

REDIRECT_INTENTS = {"off_topic": "MSG-REDIRECT", "unsafe": "MSG-REDIRECT"}
TEMPLATE_INTENTS = {"smalltalk": "MSG-THANKS", "unsupported": "MSG-UNSUPPORTED", "declare_allergy": "MSG-ALLERGY"}
# Flows built in block 2.4; until then the honest reply is MSG-UNSUPPORTED.
LATER_INTENTS = {"cart_edit", "staples_answer", "variant_request", "question_cooking"}


@dataclass
class Outcome:
    messages: list[Message] = field(default_factory=list)
    cart_changed: bool = False
    suggestions: list[SuggestionRef] = field(default_factory=list)
    fallbacks: list[str] = field(default_factory=list)
    known_prices: dict[str, int] | None = None


@dataclass
class Deps:
    guard: object  # InputGuard
    llm: object  # OllamaClient for this session
    store: object
    retriever_factory: object  # callable returning (Retriever, fallback_used)
    ctx: object
    tracer: object
    settings: object
    transcripts: object = None  # TranscriptChain
    vision_transport: object = None  # None: real providers; tests pass a fake


def say(session, template_id: str, cards=None, **values) -> Message:
    msg = Message(message_id=session.next_message_id(), role="assistant", template_id=template_id,
                  text=render(template_id, **values), cards=cards or [])
    session.messages.append(msg)
    return msg


def handle(session, text: str, deps: Deps) -> Outcome:
    verdict = deps.guard.check(text, source="user", session_id=session.session_id)
    out = Outcome(fallbacks=["guard_classifier"] if verdict.fallback else [])
    if verdict.blocked:
        deps.tracer.emit("intent_classified", session.session_id, intent=verdict.label, layer=verdict.layer)
        out.messages.append(say(session, verdict.template_id))
        return out
    if find_url(text):  # FR-24: links are routed by code, never by the model
        youtube_turn(session, text, deps, out)
        return out
    if text.strip().lower() in CLOSE_WORDS:  # FR-30: closes the open dish; rules, no model call
        session.open_dish_id = None
        out.messages.append(say(session, "MSG-THANKS"))
        return out
    result = route(text, deps.store)  # C54: named dishes and cart clears are routed in code
    if result is not None:
        deps.tracer.emit("intent_classified", session.session_id, intent=result.intent, confidence=1.0, layer="rules")
    else:
        try:
            result = classify(deps.llm, text)
        except LLMInvalid:
            out.messages.append(say(session, "MSG-REPHRASE"))
            return out
        deps.tracer.emit("intent_classified", session.session_id, intent=result.intent, confidence=result.confidence,
                         layer="model")
    if result.confidence < deps.settings.intent_confidence_min:
        out.messages.append(say(session, "MSG-REPHRASE"))
        return out
    if result.intent in REDIRECT_INTENTS:
        out.messages.append(say(session, REDIRECT_INTENTS[result.intent]))
    elif result.intent in TEMPLATE_INTENTS:
        out.messages.append(say(session, TEMPLATE_INTENTS[result.intent]))
    elif result.intent == "help":  # FR-123: code-routed, no intent-model call
        from backend.flows.greeting import help_card

        out.messages.append(say(session, "MSG-HELP", cards=[help_card()]))
    elif result.intent == "cart_clear_or_replace":
        if session.cart.is_empty:
            out.messages.append(say(session, "MSG-EMPTY-CART"))
        else:
            card = service.offer_replace(session, None, "text")
            out.messages.append(say(session, "MSG-CLEAR-CONFIRM", cards=[card], dish=_cart_label(session)))
    elif result.intent == "recipe_text":
        recipe_text_turn(session, text, deps, out)
    elif result.intent == "named_dish":
        named_dish_turn(session, result.dish_name, deps, out)
    elif result.intent == "mood_intent":
        from backend.flows.mood import mood_turn

        mood_turn(session, text, result, deps, out)
    else:  # LATER_INTENTS
        out.messages.append(say(session, "MSG-UNSUPPORTED"))
    return out


def _cart_label(session) -> str:
    names = [d.name for d in session.cart.dishes]
    return names[0] if len(names) == 1 else "current"
