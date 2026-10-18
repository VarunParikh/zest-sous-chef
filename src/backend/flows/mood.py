"""Mood flow (Architecture §4.1; FR-40, 41, 42, 63; C11 direct add).

Retrieve a wide pool, guard in code, rank with the snapshot levers (all inside
`Session.recommend_dishes`), cart the top eligible dish, offer the next two as
swaps, plus Undo and "Why this?". The only model-written words are the reason line
(A4), validated; anything that fails the validator becomes the template reason.
"""
from __future__ import annotations

import re

from backend.cart import service
from backend.flows.addons import offer_addon
from backend.cart.service import CartRuleError
from backend.flows.cards import DishAdded, SuggestionRef, SwapOption, SwapOptions, Undo, WhyThis
from backend.llm import prompts
from backend.llm.client import LLMError
from backend.llm.schemas import ReasonResult
from backend.session.levers import LeverSet

TEMPLATE_REASON = "Matches your mood and fits your settings"
BANNED = re.compile(r"\d|₹|\b(rs|price|prices|rupees?|stock|sku|cost|cheap|discount)\b", re.I)
DRIVERS = {"s_p": "strong match for the mood", "s_h": "purchase history preference high",
           "s_t": "trend high right now", "s_g": "gourmet and organic match"}
DEFAULTS = LeverSet()


MEAL_WORDS = {"breakfast": "breakfast", "brunch": "breakfast", "lunch": "lunch", "dinner": "dinner", "supper": "dinner",
              "tonight": "dinner", "snack": "snack", "snacks": "snack"}
MEAL_COURSES = {"breakfast": {"breakfast"}, "lunch": {"main"}, "dinner": {"main"}, "snack": {"side", "snack"}}
PART_OF_DAY_MEAL = {"morning": "breakfast", "lunch": "lunch", "afternoon": "snack", "evening": "dinner", "night": "dinner"}
GENERIC = {"hungry", "hunger", "starving", "food", "anything"}


def meal_for(text: str, mood_tags: list[str], ctx) -> str | None:
    """A meal named in the message steers the course; plain hunger with no mood uses the time of day (C43)."""
    words = set(re.findall(r"[a-z]+", text.lower()))
    for w, meal in MEAL_WORDS.items():
        if w in words:
            return meal
    if not set(t.lower() for t in mood_tags) - GENERIC:
        return PART_OF_DAY_MEAL.get(ctx.part_of_day)
    return None


def steer(shown, meal: str | None, store):
    """Keep the levers' order, but put dishes of the meal's course first when the pool has any."""
    if meal is None:
        return list(shown)
    courses = MEAL_COURSES[meal]
    fit = [s for s in shown if store.dish(s.candidate_id).dish.course in courses]
    return fit + [s for s in shown if s not in fit] if fit else list(shown)


def _constraint(levers: LeverSet) -> str:
    parts = [v for v, d in ((levers.diet, DEFAULTS.diet), (levers.faith, DEFAULTS.faith)) if v != d]
    parts += [x for x in levers.specialized_diets if x not in DEFAULTS.specialized_diets]
    return " and ".join(parts) or "current"


def valid_reason(reason: str, allowed_text: str) -> bool:
    """Agent Design §6.3: 3 to 18 words, no digits, currency or banned words, no names not in the input."""
    words = reason.split()
    if not 3 <= len(words) <= 18 or BANNED.search(reason):
        return False
    allowed = allowed_text.lower()
    names = [w.strip(".,!?;:'\"") for w in words[1:] if w[:1].isupper()]
    return all(n.lower() in allowed for n in names if n)


def reason_line(deps, dish, drivers: list[str]) -> str:
    tags = [*dish.flavour, *dish.mood_tags][:5]
    facts = f"Suggestion: {dish.name} | Tags: {', '.join(tags)} | Drivers: {', '.join(drivers)}"
    try:
        out = deps.llm.generate(prompts.text("reason_line"), facts, ReasonResult)
    except LLMError:  # A4 has no retry budget beyond the client's; the template reason is the fallback
        return TEMPLATE_REASON
    reason = out.reason.strip().rstrip(".")
    return reason if valid_reason(reason, facts) else TEMPLATE_REASON


def mood_turn(session, text: str, result, deps, out) -> None:
    from backend.flows.chat import say

    retriever = deps.retriever_factory()
    meal = meal_for(text, result.mood_tags, deps.ctx)
    query = " ".join([text, *result.mood_tags, *([meal] if meal else [])])
    rec = session.recommend_dishes(query, deps.ctx, deps.store, retriever, deps.tracer, display=15)
    if rec.fallback_used:
        out.fallbacks.append("vector")
    rec.shown = steer(rec.shown, meal, deps.store)[:3]
    session.last_recommendation = rec
    shown = list(rec.shown)
    top, added = None, None
    while shown and added is None:  # the engine already checked eligibility; the cart checks again
        top = shown.pop(0)
        alts = [s.candidate_id for s in shown[:2]]
        try:
            sid, added = service.add_suggested(session, top.candidate_id, alts, "mood", deps.ctx, deps.store)
        except CartRuleError:
            added = None
    if added is None:
        out.messages.append(say(session, "MSG-MOOD-NONE", constraint=_constraint(session.snapshot)))
        return
    dish = deps.store.dish(top.candidate_id).dish
    b = top.breakdown
    drivers = [DRIVERS[k] for k, v in sorted(b.contributions.items(), key=lambda kv: -kv[1]) if v > 0][:3]
    reason = reason_line(deps, dish, drivers)
    view = service.view(session.cart, deps.store)
    dish_view = next(d for d in view.dishes if d.cart_dish_id == added.cart_dish_id)
    alternatives = session.suggestions[sid]["alternatives"]
    cards = [
        DishAdded(suggestion_id=sid, dish_id=dish.dish_id, dish_name=dish.name, reason=reason,
                  line_count=len(dish_view.lines), dish_total_inr=dish_view.dish_total_inr),
        SwapOptions(suggestion_id=sid, options=[SwapOption(dish_id=a, name=deps.store.dish(a).dish.name) for a in alternatives]),
        Undo(suggestion_id=sid),
        WhyThis(suggestion_id=sid, breakdown={
            "components": {"s_p": b.s_p, "s_h": b.s_h, "s_t": b.s_t, "s_g": b.s_g},
            "contributions": dict(b.contributions), "weights_effective": dict(b.weights_effective), "final": b.final}),
    ]
    tags = [t for t in result.mood_tags if t.lower() not in GENERIC]
    mood = tags[0] if tags else "hungry"
    out.messages.append(say(session, "MSG-MOOD-ADD", cards=cards, mood=mood, dish=dish.name, reason=reason))
    out.cart_changed = True
    out.suggestions.append(SuggestionRef(suggestion_id=sid, type="dish", candidate_id=dish.dish_id, rank=1))
    out.known_prices = {dish.name: dish_view.dish_total_inr, "total": view.subtotal_inr}
    deps.tracer.emit("suggestion_shown", session.session_id, suggestion_id=sid, candidate_id=dish.dish_id,
                     alternatives=alternatives, final=round(b.final, 4))
    deps.tracer.emit("cart_mutated", session.session_id, action="mood_add", item_count=len(session.cart.lines()))
    offer_addon(session, added, deps, out)
