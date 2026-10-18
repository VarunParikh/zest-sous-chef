"""One chat turn (Architecture §4): guard, then intent, then a flow. Code decides; the model only labels."""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.cart import service
from backend.flows.cards import Message, SuggestionRef
from backend.flows.templates import render
from backend.intent.classify import classify
from backend.llm.client import LLMInvalid

REDIRECT_INTENTS = {"off_topic": "MSG-REDIRECT", "unsafe": "MSG-REDIRECT"}
TEMPLATE_INTENTS = {"smalltalk": "MSG-THANKS", "unsupported": "MSG-UNSUPPORTED", "declare_allergy": "MSG-ALLERGY"}
# Flows built in block 2.4; until then the honest reply is MSG-UNSUPPORTED.
LATER_INTENTS = {"youtube_recipe", "recipe_text", "named_dish", "cart_edit", "staples_answer", "variant_request",
                 "question_cooking"}


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
    elif result.intent == "cart_clear_or_replace":
        if session.cart.is_empty:
            out.messages.append(say(session, "MSG-EMPTY-CART"))
        else:
            card = service.offer_replace(session, None, "text")
            out.messages.append(say(session, "MSG-CLEAR-CONFIRM", cards=[card], dish=_cart_label(session)))
    elif result.intent == "mood_intent":
        from backend.flows.mood import mood_turn

        mood_turn(session, text, result, deps, out)
    else:  # LATER_INTENTS
        out.messages.append(say(session, "MSG-UNSUPPORTED"))
    return out


def _cart_label(session) -> str:
    names = [d.name for d in session.cart.dishes]
    return names[0] if len(names) == 1 else "current"
