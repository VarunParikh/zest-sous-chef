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


@router.post("/checkout")
def checkout(session_id: str, request: Request) -> dict:
    """API Spec v0.4 §4.7. Buy Now is the only way an order is placed (FR-80)."""
    from backend.cart.checkout import COLLAPSE_AFTER_S, CheckoutBlocked, place_order
    from backend.flows.templates import TEMPLATES, render

    session = request.app.state.sessions.get(session_id)
    store = request.app.state.store
    with session.busy():
        try:
            order = place_order(session, request.headers.get("Idempotency-Key"), context(request), store,
                                request.app.state.tracer)
        except CheckoutBlocked as e:
            if e.code == "BAD_REQUEST":
                raise ApiError(400, "BAD_REQUEST", "An Idempotency-Key header is required.") from None
            if e.code == "EMPTY_CART":
                raise ApiError(400, "EMPTY_CART", render("MSG-EMPTY-CART"), "MSG-EMPTY-CART") from None
            if e.code == "OUT_OF_STOCK":
                raise ApiError(409, "OUT_OF_STOCK", render("MSG-BLOCKED-ORDER", item=e.details["item"]), "MSG-BLOCKED-ORDER",
                               details={"line_ids": e.details["line_ids"],
                                        "substitutions": [c.model_dump(mode="json") for c in e.details["substitutions"]]}) from None
            raise ApiError(409, "PRICE_CHANGED", render("MSG-PRICE-CHANGED"), "MSG-PRICE-CHANGED",
                           details={"cart": _view(request, session).model_dump(mode="json")}) from None
    return {"order_id": order.order_id, "subtotal_inr": order.subtotal_inr, "placed_at": order.placed_at,
            "message": {"template_id": "MSG-ORDER", "text": TEMPLATES["MSG-ORDER"]}, "collapse_after_s": COLLAPSE_AFTER_S}
