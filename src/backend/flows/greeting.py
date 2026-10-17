"""Session-start turn (Conversation Design MSG-GREET; API Spec §4.1)."""
from __future__ import annotations

from backend.flows.cards import Message, StarterChips, TurnResponse
from backend.flows.templates import STARTER_CHIPS, TEMPLATES
from backend.session.store import Session


def greeting_turn(session: Session) -> TurnResponse:
    msg = Message(message_id=session.next_message_id(), role="assistant", template_id="MSG-GREET",
                  text=TEMPLATES["MSG-GREET"], cards=[StarterChips(chips=list(STARTER_CHIPS))])
    session.messages.append(msg)
    return TurnResponse(turn_id=session.next_turn_id(), messages=[msg])
