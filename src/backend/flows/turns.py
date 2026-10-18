"""Turn assembly (API Spec v0.3 §4.4; FR-03; C31).

The request may carry the lever panel's current values. They are only compared
with the session snapshot to set the banner flag; they are never stored and
never used for ranking (FR-02).
"""
from __future__ import annotations

from backend.flows.cards import Message, Notice, TurnResponse
from backend.flows.prices import correct_prices
from backend.session.levers import LeverSet, snapshot_hash
from backend.session.store import Session


def levers_changed(session: Session, current: LeverSet | None) -> bool:
    return current is not None and snapshot_hash(current) != session.snapshot_hash


def build_turn(session: Session, messages: list[Message], current_levers: LeverSet | None = None,
               notices: list[Notice] | None = None, known_prices: dict[str, int] | None = None, **fields) -> TurnResponse:
    """`known_prices` (item name -> catalogue price) runs the FR-79 reply gate on every assistant message."""
    if known_prices is not None:
        for m in messages:
            if m.role == "assistant":
                m.text = correct_prices(m.text, known_prices)[0]
    return TurnResponse(turn_id=session.next_turn_id(), messages=messages, notices=notices or [],
                        levers_changed_since_snapshot=levers_changed(session, current_levers), **fields)
