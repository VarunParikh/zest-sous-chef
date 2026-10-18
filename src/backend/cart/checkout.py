"""Buy Now (FR-80, 81, 83; API Spec v0.4 §4.7). Pure code: revalidate stock and price, then place one order per key."""
from __future__ import annotations

import secrets
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone

from backend.cart import service
from backend.cart.allocation import allocate
from backend.cart.models import Cart
from backend.catalogue.store import Store

COLLAPSE_AFTER_S = 10  # FR-81, C1


@dataclass(frozen=True)
class Order:
    order_id: str
    idempotency_key: str
    lines: tuple  # (line_id, sku_id, count, price_inr) for priced packs
    subtotal_inr: int
    placed_at: str


class CheckoutBlocked(Exception):
    def __init__(self, code: str, **details):
        super().__init__(code)
        self.code, self.details = code, details


def _quoted_total(cart: Cart) -> int:
    return sum(cart.quotes.get(p.sku_id, 0) * p.count for ln in cart.lines() if ln.priced for p in ln.packs)


def _out_of_stock(cart: Cart, store: Store) -> list[str]:
    need = Counter()
    for ln in cart.lines():
        for p in ln.packs:
            need[p.sku_id] += p.count
    short = {sku for sku, n in need.items() if store.stock(store.sku(sku)) < n or not store.sku(sku).dark_store_ok}
    blocked = [ln for ln in cart.lines() if not ln.in_stock or any(p.sku_id in short for p in ln.packs)]
    ids = {ln.line_id for ln in blocked}
    # A dimmed line sharing a blocked pack is blocked too.
    ids |= {ln.line_id for ln in cart.lines() if ln.shared_from_line_id in ids}
    return [ln.line_id for ln in cart.lines() if ln.line_id in ids]


def place_order(session, key: str | None, ctx, store: Store, tracer=None) -> Order:
    if not key:
        raise CheckoutBlocked("BAD_REQUEST")
    if key in session.orders:  # FR-80: a repeated key returns the same order
        return session.orders[key]
    if session.cart.is_empty:
        raise CheckoutBlocked("EMPTY_CART")
    fresh = allocate(session.cart, store)
    blocked = _out_of_stock(fresh, store)
    if blocked:
        session.cart = fresh
        subs = [c for lid in blocked if (c := service.propose_substitution(session, lid, ctx, store)) is not None]
        names = [store.variant(ln.variant_id).name for ln in fresh.lines() if ln.line_id in blocked]
        raise CheckoutBlocked("OUT_OF_STOCK", line_ids=blocked, substitutions=subs, item=names[0])
    shown, now = _quoted_total(session.cart), service.view(fresh, store).subtotal_inr
    changed = now != shown or any(store.price(store.sku(s)) != q for s, q in fresh.quotes.items())
    if changed:  # FR-83: show the new price before ordering; the next press orders at it
        fresh.quotes = {s: store.price(store.sku(s)) for s in fresh.quotes}
        session.cart = fresh
        raise CheckoutBlocked("PRICE_CHANGED")
    lines = tuple((ln.line_id, p.sku_id, p.count, store.price(store.sku(p.sku_id)) * p.count)
                  for ln in fresh.lines() if ln.priced for p in ln.packs)
    order = Order(order_id=f"o_{secrets.token_hex(4)}", idempotency_key=key, lines=lines, subtotal_inr=now,
                  placed_at=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"))
    session.orders[key] = order
    session.cart, session.undo_stack, session.pending = Cart(), [], {}
    if tracer is not None:
        tracer.emit("checkout_placed", session.session_id, order_id=order.order_id, subtotal_inr=now, packs=len(lines))
    return order
