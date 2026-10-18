"""Text recipe and named-dish flows (US-11; FR-30, 31, 33; Conversation Design MSG-TXT-*)."""
from __future__ import annotations

import re

from backend.cart import service
from backend.cart.service import CartRuleError
from backend.engine.eligibility import check_dish
from backend.flows.addons import offer_addon
from backend.flows.cards import Undo
from backend.flows.recipe import DEFAULT_NAME, dish_choice, item_question, prepare, setting_label
from backend.llm import prompts
from backend.llm.schemas import ExtractionResult

CLOSE_WORDS = {"new dish", "done"}


def say(session, template_id, cards=None, **values):
    from backend.flows.chat import say as _say

    return _say(session, template_id, cards, **values)


def title(name: str | None) -> str:
    return " ".join(w.capitalize() for w in name.split()) if name else DEFAULT_NAME


def extract(deps, text: str) -> ExtractionResult:
    """A3 `recipe_extract` on spotlighted, capped text. Raises LLMInvalid after one retry, LLMError if unreachable."""
    system, user = prompts.render("recipe_extract", text[: deps.settings.max_recipe_chars])
    return deps.llm.generate(system, user, ExtractionResult)


def stored_dish(store, name: str | None):
    if not name:
        return None
    want = name.strip().lower()
    for rec in store.dishes:
        names = {rec.dish.name.lower(), rec.dish.name.lower().replace(" (international)", "")}
        if want in names | {a.lower() for a in rec.dish.aliases}:
            return rec
    return None


def _alternative(session, query: str, deps) -> tuple[str, str] | None:
    rec = session.recommend_dishes(query, deps.ctx, deps.store, deps.retriever_factory(), deps.tracer)
    return (rec.shown[0].candidate_id, deps.store.dish(rec.shown[0].candidate_id).dish.name) if rec.shown else None


def block(session, item: str, rules, query: str, deps, out) -> None:
    """Nothing from the recipe is carted; the top eligible similar dish is offered as one chip (FR-90)."""
    alt = _alternative(session, query, deps)
    cards = [dish_choice(session, [alt])] if alt else []
    out.messages.append(say(session, "MSG-PERSONA-BLOCK", cards=cards, item=item[:1].upper() + item[1:],
                            setting=setting_label(tuple(rules), session.snapshot),
                            alternative=alt[1] if alt else "another dish"))


def cart_recipe(session, dish_name: str | None, lines, source: str, deps, out, keep_open: bool, headline=None,
                offer: bool = True):
    """Prepare and cart extracted lines. `headline(dish, n)` returns (template_id, values) for the first message.
    Returns (dish or None, items carted), or None when a blocked item stopped the whole recipe."""
    prep = prepare(session, lines, deps)
    if prep.blocked:
        name, rules = prep.blocked[0]
        block(session, name, rules, dish_name or " ".join(ln.name for ln in lines), deps, out)
        return None
    target = None
    if keep_open and session.open_dish_id and any(d.cart_dish_id == session.open_dish_id for d in session.cart.dishes):
        open_dish = next(d for d in session.cart.dishes if d.cart_dish_id == session.open_dish_id)
        if not dish_name or title(dish_name) == open_dish.name:
            target = open_dish.cart_dish_id
    name = title(dish_name)
    dish = None
    if prep.items:
        dish = service.add_custom_dish(session, name, prep.items, source, deps.store, cart_dish_id=target)
        out.cart_changed = True
        deps.tracer.emit("cart_mutated", session.session_id, action=f"{source}_add", item_count=len(session.cart.lines()))
    if keep_open:
        session.open_dish_id = dish.cart_dish_id if dish else target
    if dish is not None and headline is not None:
        template_id, values = headline(dish, len(prep.items))
        out.messages.append(say(session, template_id, **values))
    new_dish = dish is not None and target is None
    pending = dish.cart_dish_id if dish else target
    for line, options in prep.ambiguous:
        card = item_question(session, line, options, pending, dish.name if dish else name)
        out.messages.append(say(session, "MSG-AMBIG", cards=[card], option_a=options[0], option_b=options[1]))
    if prep.unknown:
        out.messages.append(say(session, "MSG-EDIT-UNCLEAR", options=", ".join(f'"{n}"' for n in prep.unknown)))
    if new_dish and offer:  # one add-on per new dish, not per follow-up message (US-19)
        offer_addon(session, dish, deps, out)
    return dish, len(prep.items)


def recipe_text_turn(session, text: str, deps, out) -> None:
    from backend.llm.client import LLMInvalid

    try:
        ex = extract(deps, text)
    except LLMInvalid:
        out.messages.append(say(session, "MSG-REPHRASE"))
        return
    if not ex.ingredients:
        if ex.dish_name:
            named_dish_turn(session, ex.dish_name, deps, out)
        else:
            out.messages.append(say(session, "MSG-REPHRASE"))
        return
    cart_recipe(session, ex.dish_name, ex.ingredients, "text", deps, out, keep_open=True,
                headline=lambda dish, n: ("MSG-TXT-DRAFT", {"n": n, "dish": dish.name}))


def add_stored(session, dish_id: str, deps, out, source: str = "text") -> None:
    """FR-31: the stored recipe, with Undo. A guardrail block offers an alternative instead."""
    try:
        sid, added = service.add_suggested(session, dish_id, [], source, deps.ctx, deps.store)
    except CartRuleError as e:
        rec = deps.store.dish(dish_id).dish
        block(session, rec.name, e.details.get("rules", []), rec.name, deps, out)
        return
    session.open_dish_id = None
    out.cart_changed = True
    deps.tracer.emit("cart_mutated", session.session_id, action="named_dish", item_count=len(session.cart.lines()))
    out.messages.append(say(session, "MSG-TXT-STORED", cards=[Undo(suggestion_id=sid)], dish=added.name, servings=added.servings))
    offer_addon(session, added, deps, out)


def word_matches(store, name: str | None) -> list:
    """Stored dishes whose name contains every word asked for ("pasta" -> Creamy Pasta)."""
    words = set(re.findall(r"[a-z]+", (name or "").lower()))
    if not words:
        return []
    return [rec for rec in store.dishes
            if words <= set(re.findall(r"[a-z]+", rec.dish.name.lower().replace("(international)", "")))]


def named_dish_turn(session, dish_name: str | None, deps, out) -> None:
    rec = stored_dish(deps.store, dish_name)
    if rec is None:
        matches = word_matches(deps.store, dish_name)
        if len(matches) == 1:
            rec = matches[0]
    if rec is not None:
        mask = check_dish(rec, session.snapshot, deps.store)
        if not mask.eligible:  # FR-90: say which setting removed it, and offer an eligible alternative
            block(session, rec.dish.name, mask.failed, dish_name or rec.dish.name, deps, out)
            return
        add_stored(session, rec.dish.dish_id, deps, out)
        return
    query = dish_name or ""
    shown = session.recommend_dishes(query, deps.ctx, deps.store, deps.retriever_factory(), deps.tracer).shown[:3]
    options = [(s.candidate_id, deps.store.dish(s.candidate_id).dish.name) for s in shown]
    cards = [dish_choice(session, options)] if options else []
    out.messages.append(say(session, "MSG-TXT-UNKNOWN", cards=cards, dish=title(dish_name)))
