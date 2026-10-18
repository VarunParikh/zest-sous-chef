"""Cart routes (API Spec v0.4 §3 endpoints 7 to 10, §4.6; FR-72, 74, 102, 114). Every mutation takes the session lock."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.api.errors import ApiError
from backend.cart import service
from backend.cart.service import CartRuleError
from backend.engine.context import build_context
from backend.flows.cards import CartView

router = APIRouter(prefix="/api/v1/sessions/{session_id}")


class LinePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quantity: Optional[int] = Field(None, ge=1, le=9)
    variant_id: Optional[str] = None

    @model_validator(mode="after")
    def _exactly_one(self):
        if (self.quantity is None) == (self.variant_id is None):
            raise ValueError("send exactly one of quantity or variant_id")
        return self


def rule_error(e: CartRuleError) -> ApiError:
    if e.code == "STALE":
        return ApiError(409, "STALE_ACTION", e.message)
    return ApiError(400, "BAD_REQUEST", e.message, details={"reason": e.code, **e.details})


def context(request: Request):
    return build_context(settings=request.app.state.settings)


def _view(request: Request, session) -> CartView:
    return service.view(session.cart, request.app.state.store)


@router.get("/cart")
def get_cart(session_id: str, request: Request) -> CartView:
    return _view(request, request.app.state.sessions.get(session_id))


def _mutate(request: Request, session_id: str, fn) -> CartView:
    session = request.app.state.sessions.get(session_id)
    with session.busy():
        try:
            fn(session)
        except CartRuleError as e:
            raise rule_error(e) from None
        request.app.state.tracer.emit("cart_mutated", session_id, item_count=len(session.cart.lines()))
        return _view(request, session)


@router.patch("/cart/lines/{line_id}")
def patch_line(session_id: str, line_id: str, body: LinePatch, request: Request) -> CartView:
    store = request.app.state.store
    if body.quantity is not None:
        return _mutate(request, session_id, lambda s: service.set_quantity(s, line_id, body.quantity, store))
    return _mutate(request, session_id, lambda s: service.switch_variant(s, line_id, body.variant_id, context(request), store))


@router.delete("/cart/lines/{line_id}")
def delete_line(session_id: str, line_id: str, request: Request) -> CartView:
    return _mutate(request, session_id, lambda s: service.remove_line(s, line_id, request.app.state.store))


@router.delete("/cart/dishes/{cart_dish_id}")
def delete_dish(session_id: str, cart_dish_id: str, request: Request) -> CartView:
    return _mutate(request, session_id, lambda s: service.remove_dish(s, cart_dish_id, request.app.state.store))
