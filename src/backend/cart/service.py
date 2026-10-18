"""Cart operations and the cart view (FR-70 to 79). Pure code: prices, packs and stock come from the catalogue."""
from __future__ import annotations

from backend.cart.models import Cart, CartLine
from backend.catalogue.store import Store
from backend.flows.cards import CartDishView, CartLineView, CartView, PackView


def _pack_label(store: Store, sku_id: str) -> str:
    p = store.sku(sku_id).pack
    qty = int(p.qty) if float(p.qty).is_integer() else p.qty
    return f"{qty} {p.unit.value}"


def line_price(ln: CartLine, store: Store) -> int:
    return sum(store.price(store.sku(p.sku_id)) * p.count for p in ln.packs) if ln.priced else 0


def view(cart: Cart, store: Store) -> CartView:
    """The client's cart (API Spec §4.6), priced from the catalogue at render time (FR-79)."""
    dishes = []
    for d in cart.dishes:
        lines = [CartLineView(
            line_id=ln.line_id, ingredient_name=ln.ingredient_name, variant_id=ln.variant_id,
            variant_name=store.variant(ln.variant_id).name,
            packs=[PackView(sku_id=p.sku_id, count=p.count, pack=_pack_label(store, p.sku_id)) for p in ln.packs],
            price_inr=line_price(ln, store), priced=ln.priced, shared_from_line_id=ln.shared_from_line_id,
            estimated=ln.estimated, reason=ln.reason, alternative_variant_ids=ln.alternative_variant_ids,
            in_stock=ln.in_stock, quantity=ln.quantity) for ln in d.lines]
        dishes.append(CartDishView(cart_dish_id=d.cart_dish_id, dish_id=d.dish_id, name=d.name,
                                   dish_total_inr=sum(x.price_inr for x in lines), lines=lines))
    return CartView(dishes=dishes, item_count=sum(len(d.lines) for d in dishes),
                    subtotal_inr=sum(d.dish_total_inr for d in dishes))
