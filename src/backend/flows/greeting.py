"""Session-start turn (Conversation Design MSG-GREET; API Spec §4.1; FR-08)."""
from __future__ import annotations

from backend.engine.scoring import effective_weights
from backend.flows.cards import Message, Notice, StarterChips, TurnResponse
from backend.flows.templates import STARTER_CHIPS, TEMPLATES
from backend.session.levers import LeverSet
from backend.session.store import Session


def snapshot_notices(levers: LeverSet) -> list[Notice]:
    notices = []
    if effective_weights(levers.weights)[1]:  # all four weights 0: defaults restored (FR-08, C30)
        notices.append(Notice(level="info", template_id="MSG-WEIGHTS-DEFAULT", text=TEMPLATES["MSG-WEIGHTS-DEFAULT"]))
    return notices


def greeting_turn(session: Session) -> TurnResponse:
    msg = Message(message_id=session.next_message_id(), role="assistant", template_id="MSG-GREET",
                  text=TEMPLATES["MSG-GREET"], cards=[StarterChips(chips=list(STARTER_CHIPS))])
    session.messages.append(msg)
    return TurnResponse(turn_id=session.next_turn_id(), messages=[msg], notices=snapshot_notices(session.snapshot))
