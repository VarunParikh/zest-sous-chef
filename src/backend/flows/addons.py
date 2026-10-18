"""Add-on suggestions after a dish is carted (US-19; FR-62, 64, 117 to 119; MSG-ADDON).

One companion, the top pick: candidates from curated pairs plus vector neighbours of the
anchor dish (ADR-004 v2), eligibility and the add-on price cap in code (C18), ranked by the
snapshot levers. Suggest only: nothing enters the cart without the user's tap (FR-64).
"""
from __future__ import annotations

from backend.engine.eligibility import check_dish
from backend.engine.recommend import recommend_addons
from backend.flows.cards import AddonItem, AddonSuggestion
from backend.flows.why import why_card

DRIVERS = {"s_h": "your purchase history", "s_t": "the current trend", "s_g": "your gourmet and organic settings",
           "s_p": "how well it pairs"}


def _anchor(cart_dish, deps) -> str | None:
    """The stored dish to pair with: the cart dish itself, a stored dish of the same name, or the nearest stored dish."""
    from backend.flows.text import stored_dish

    if cart_dish.dish_id:
        return cart_dish.dish_id
    rec = stored_dish(deps.store, cart_dish.name)
    if rec is not None:
        return rec.dish.dish_id
    hits = deps.retriever_factory().dishes(cart_dish.name).hits
    return hits[0].id if hits else None


def _reason(contributions: dict[str, float]) -> str:
    top = [DRIVERS[k] for k, v in sorted(contributions.items(), key=lambda kv: -kv[1]) if v > 0][:2]
    return f"Chosen for {' and '.join(top)}" if top else "Pairs well with your dish"


def offer_addon(session, cart_dish, deps, out) -> None:
    from backend.flows.chat import say

    anchor = _anchor(cart_dish, deps)
    if anchor is None:
        return
    lines = session.cart.lines()
    terms = frozenset(ln.ingredient_name for ln in lines)
    in_cart = tuple(d.dish_id for d in session.cart.dishes if d.dish_id)
    rec = recommend_addons(anchor, session.snapshot, deps.ctx, deps.store, deps.retriever_factory(), deps.tracer,
                           session.session_id, cart_dish_ids=in_cart, cart_terms=terms, display=8)
    if rec.fallback_used and "vector" not in out.fallbacks:
        out.fallbacks.append("vector")
    session.last_addon = {"anchor": anchor, "rec": rec}
    fresh = [s for s in rec.shown if s.candidate_id not in session.suggested]  # no repeats in a session (C45)
    if not fresh:
        return
    top = fresh[0]
    session.suggested.add(top.candidate_id)
    companion = deps.store.dish(top.candidate_id)
    price = check_dish(companion, session.snapshot, deps.store, kind="addon", cart_terms=terms).basket_cost_inr or 0
    sid = session.next_id("sg")
    session.pending[sid] = {"kind": "addon", "dish_id": top.candidate_id, "source": cart_dish.source}
    card = AddonSuggestion(suggestion_id=sid, item=AddonItem(name=companion.dish.name, price_inr=price),
                           reason=_reason(top.breakdown.contributions))
    hit = next(h for h in rec.pool if h.id == top.candidate_id)
    retrieval = {"curated_strength": hit.curated_strength, "curated_rank": hit.curated_rank, "vector_rank": hit.vector_rank,
                 "fused_rank": hit.fused_rank}
    source = ("a curated pairing" if hit.curated_rank else "") + (" and " if hit.curated_rank and hit.vector_rank else "") + \
             ("a close match by flavour and style" if hit.vector_rank else "")
    why = why_card(sid, "addon", f"{card.reason}. It is {source or 'a companion'} for {deps.store.dish(anchor).dish.name}, "
                                 f"and fits your settings and the add-on price cap.", top, fresh[1:3], deps.store,
                   anchor=deps.store.dish(anchor).dish.name, retrieval=retrieval)
    out.messages.append(say(session, "MSG-ADDON", cards=[card, why], companion=companion.dish.name, dish=cart_dish.name))
    deps.tracer.emit("suggestion_shown", session.session_id, suggestion_id=sid, candidate_id=top.candidate_id,
                     kind="addon", anchor=anchor, final=round(top.breakdown.final, 4))
