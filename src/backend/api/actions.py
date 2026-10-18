"""Button taps (API Spec §4.3): deterministic, never through the model or the guard."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from backend.api.cart import context, rule_error
from backend.cart import service
from backend.cart.service import CartRuleError
from backend.flows.cards import Message, TurnResponse
from backend.flows.templates import render
from backend.flows.turns import build_turn
from backend.session.levers import LeverSet

router = APIRouter(prefix="/api/v1/sessions/{session_id}")


class ActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["swap", "undo", "answer", "confirm", "add_on", "substitute", "consent_photo"]
    ref_message_id: Optional[str] = None
    payload: dict = {}
    levers: Optional[LeverSet] = None  # API Spec v0.3, C31: compared only


def reply(session, template_id: str, **values) -> Message:
    msg = Message(message_id=session.next_message_id(), role="assistant", template_id=template_id,
                  text=render(template_id, **values))
    session.messages.append(msg)
    return msg


def _substitute(session, p: dict, request: Request) -> tuple[list[Message], bool]:
    store = request.app.state.store
    pending = session.pending.get(p.get("substitution_id"))
    changed = service.answer_substitution(session, p.get("substitution_id", ""), p.get("choice", ""), context(request), store)
    if not changed:
        return [], False
    line = next(ln for ln in session.cart.lines() if ln.line_id == pending["line_id"])
    return [reply(session, "MSG-EDIT-OK", change=f"Swapped to {store.variant(line.variant_id).name}")], True


HANDLERS = {"substitute": _substitute}


@router.post("/action")
def action(session_id: str, body: ActionRequest, request: Request) -> TurnResponse:
    session = request.app.state.sessions.get(session_id)
    handler = HANDLERS.get(body.type)
    with session.busy():
        if handler is None:
            raise rule_error(CartRuleError("STALE", "That button isn't available yet."))
        try:
            messages, changed = handler(session, body.payload, request)
        except CartRuleError as e:
            raise rule_error(e) from None
        if changed:
            request.app.state.tracer.emit("cart_mutated", session_id, action=body.type)
        return build_turn(session, messages, current_levers=body.levers, cart_changed=changed,
                          cart=service.view(session.cart, request.app.state.store))
