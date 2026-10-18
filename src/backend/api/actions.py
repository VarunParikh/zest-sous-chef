"""Button taps (API Spec §4.3): deterministic, never through the model or the guard."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict

from backend.api.cart import context, rule_error
from backend.cart import service
from backend.cart.service import CartRuleError
from backend.flows.cards import Message, SwapOption, SwapOptions, TurnResponse, Undo
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


def _confirm(session, p: dict, request: Request) -> tuple[list[Message], bool]:
    pending = session.pending.get(p.get("confirm_id", ""))
    if pending and pending["kind"] in ("dup_video", "pantry"):
        from backend.flows.chat import Outcome
        from backend.flows.youtube import answer

        choices = {"dup_video": {"yes", "no"}, "pantry": {"have", "add"}}[pending["kind"]]
        if p.get("choice") not in choices:
            raise CartRuleError("STALE", "That question has expired.")
        del session.pending[p["confirm_id"]]
        out = Outcome()
        answer(session, pending, p["choice"], _deps(request, session.session_id), out)
        return out.messages, out.cart_changed
    added = service.answer_confirm(session, p.get("confirm_id", ""), p.get("choice", ""), context(request),
                                   request.app.state.store)
    if added is None:
        return [], False
    if isinstance(added, str):  # "do something else": the cart was cleared under this undo id
        msg = reply(session, "MSG-CLEAR-DONE")
        msg.cards = [Undo(suggestion_id=added)]
        return [msg], True
    if p.get("choice") == "replace":
        msg = reply(session, "MSG-CLEAR-DONE")
    else:
        msg = reply(session, "MSG-EDIT-OK", change=f"Added {added.name}")
    msg.cards = [Undo(suggestion_id=added.added_by_suggestion_id)]
    return [msg], True


def _undo(session, p: dict, request: Request) -> tuple[list[Message], bool]:
    name = service.undo(session, p.get("suggestion_id", ""), request.app.state.store)
    if name is None:
        return [reply(session, "MSG-EDIT-OK", change="Restored your cart")], True
    return [reply(session, "MSG-UNDO", dish=name)], True


def _swap(session, p: dict, request: Request) -> tuple[list[Message], bool]:
    store = request.app.state.store
    sid = p.get("suggestion_id", "")
    added = service.swap(session, sid, p.get("alt_dish_id", ""), context(request), store)
    msg = reply(session, "MSG-MOOD-SWAP", dish=added.name)
    options = [SwapOption(dish_id=d, name=store.dish(d).dish.name) for d in session.suggestions[sid]["alternatives"]]
    msg.cards = [SwapOptions(suggestion_id=sid, options=options), Undo(suggestion_id=sid)]
    return [msg], True


def _deps(request: Request, session_id: str):
    from backend.api.chat import chat_deps

    return chat_deps(request, session_id)


def _answer(session, p: dict, request: Request) -> tuple[list[Message], bool]:
    """A clarifying question: a dish chip (FR-33, FR-90 alternative) or an ambiguous ingredient (FR-13, FR-30)."""
    from backend.flows.chat import Outcome
    from backend.flows.recipe import Item, item_for
    from backend.flows.text import add_stored

    q = session.pending.get(p.get("question_id", ""))
    choice = p.get("choice", "")
    if not q or choice not in q["options"]:
        raise CartRuleError("STALE", "That question has expired.")
    del session.pending[p["question_id"]]
    deps, out = _deps(request, session.session_id), Outcome()
    if q["kind"] == "dish_choice":
        add_stored(session, choice, deps, out)
        return out.messages, out.cart_changed
    got = item_for(choice, q["qty"], q["unit"], q["estimated"], session.snapshot, deps.ctx, deps.store)
    if not isinstance(got, Item):
        raise CartRuleError("NOT_ELIGIBLE", f"{choice} isn't available with your settings.")
    dish = service.add_custom_dish(session, q["dish_name"], [got], "text", deps.store, cart_dish_id=q["cart_dish_id"])
    if session.open_dish_id is None and q["cart_dish_id"] is None:
        session.open_dish_id = dish.cart_dish_id
    return [reply(session, "MSG-EDIT-OK", change=f"Added {choice}")], True


HANDLERS = {"substitute": _substitute, "confirm": _confirm, "undo": _undo, "swap": _swap, "answer": _answer}


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
