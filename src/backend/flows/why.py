""""Why this?" for every suggestion (FR-63, US-18; AC-20). A plain reason, the lever drivers, the score breakdown
(contributions sum to the final score) and the runners-up. Code-written from the scores; no model call."""
from __future__ import annotations

from backend.flows.cards import WhyThis

DRIVERS = {"s_h": "your purchase history affinity", "s_t": "the current market trend", "s_g": "your gourmet and organic settings",
           "s_p": "how well it matches what you asked for"}


def drivers(breakdown) -> list[str]:
    return [DRIVERS[k] for k, v in sorted(breakdown.contributions.items(), key=lambda kv: -kv[1]) if v > 0][:3]


def scores(breakdown) -> dict:
    return {"components": {"s_p": breakdown.s_p, "s_h": breakdown.s_h, "s_t": breakdown.s_t, "s_g": breakdown.s_g},
            "contributions": dict(breakdown.contributions), "weights_effective": dict(breakdown.weights_effective),
            "final": breakdown.final}


def runners_up(scored_items, store) -> list[dict]:
    return [{"dish_id": s.candidate_id, "name": store.dish(s.candidate_id).dish.name, "final": round(s.breakdown.final, 4)}
            for s in scored_items]


def why_card(suggestion_id: str, kind: str, reason: str, top=None, alternatives=(), store=None, **extra) -> WhyThis:
    body = {"kind": kind, "reason": reason, "drivers": drivers(top.breakdown) if top else [],
            "alternatives": runners_up(alternatives, store) if store else [], **extra}
    if top is not None:
        body.update(scores(top.breakdown))
    return WhyThis(suggestion_id=suggestion_id, breakdown=body)
