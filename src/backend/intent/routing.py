"""Code routing before the intent model (C54; Agent Design v0.4 §6.1; Architecture v0.8 §4).

Runs after the guard. Two deterministic routes; everything else goes to A2:
- a message with no digits and at most one comma, with a cooking verb and a stored dish
  name or alias as whole words, is `named_dish` with that dish;
- "clear", "empty", "reset" or "start over" within 15 characters of "cart" or "basket"
  is `cart_clear_or_replace` (the cart is never cleared without the confirmation, FR-77).
"""
from __future__ import annotations

import re

from backend.llm.schemas import IntentResult

VERBS = re.compile(r"\b(make|cook|prepare|want|try)\b", re.I)
CLEAR = re.compile(r"\b(clear|empty|reset|start over)\b.{0,15}\b(cart|basket)\b|\b(cart|basket)\b.{0,15}\b(clear|empty|reset)\b", re.I)


def _names(store) -> list[tuple[str, str]]:
    out = []
    for rec in store.dishes:
        name = rec.dish.name
        for n in (name, name.replace(" (international)", ""), *rec.dish.aliases):
            if n:
                out.append((n.lower(), name))
    return out


def route(text: str, store) -> IntentResult | None:
    if CLEAR.search(text):
        return IntentResult(intent="cart_clear_or_replace", confidence=1.0)
    if re.search(r"\d", text) or text.count(",") > 1 or not VERBS.search(text):
        return None
    low = text.lower()
    hits = [(len(n), -i, dish) for i, (n, dish) in enumerate(_names(store)) if re.search(rf"\b{re.escape(n)}\b", low)]
    if not hits:
        return None
    return IntentResult(intent="named_dish", confidence=1.0, dish_name=max(hits)[2])
