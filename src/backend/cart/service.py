"""Cart operations and the cart view (FR-70 to 79). Pure code: prices, packs and stock come from the catalogue."""
from __future__ import annotations

from backend.cart.allocation import MAX_PACKS, allocate
from backend.cart.models import Cart, CartDish, CartLine
from backend.catalogue.store import Store
from backend.engine.eligibility import check_dish, check_variant
from backend.engine.variants import choose_variant
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


class CartRuleError(Exception):
    """A cart change the rules do not allow. `code`: STALE, NOT_ELIGIBLE, WRONG_INGREDIENT, SHARED_LINE, TOO_MANY_PACKS."""

    def __init__(self, code: str, message: str, **details):
        super().__init__(message)
        self.code, self.message, self.details = code, message, details


def _lines_for_dish(session, rec, cart_dish_id: str, ctx, store: Store) -> list[CartLine]:
    """Every variant is chosen and checked in code; the cart never holds an item the guardrails remove."""
    levers = session.snapshot
    mask = check_dish(rec, levers, store)
    if not mask.eligible:
        raise CartRuleError("NOT_ELIGIBLE", f"{rec.dish.name} isn't available with your settings.", rules=list(mask.failed))
    lines = []
    for ing in rec.ingredients:
        required = tuple(ing.attribute_hint.values()) if ing.attribute_hint else ()
        choice = choose_variant(ing.ingredient_name, levers, ctx, store, required=required)
        if choice.chosen is None or not check_variant(choice.chosen, levers, store).eligible:
            if ing.essential:
                raise CartRuleError("NOT_ELIGIBLE", f"{rec.dish.name} isn't available with your settings.",
                                    ingredient=ing.ingredient_name)
            continue  # optional line without an eligible variant: dropped, never carted
        lines.append(CartLine(
            line_id=session.next_id("l"), cart_dish_id=cart_dish_id, ingredient_name=ing.ingredient_name,
            need_qty=ing.qty, need_unit=ing.unit, variant_id=choice.chosen.variant_id, reason=choice.reason,
            alternative_variant_ids=[v.variant_id for v in choice.alternatives[:3]]))
    return lines


def add_dish(session, dish_id: str, source: str, ctx, store: Store, suggestion_id: str | None = None,
             index: int | None = None) -> CartDish:
    """Cart a stored dish at its stored servings (FR-31; FR-32 is cut). Returns the allocated dish."""
    rec = store.dish(dish_id)
    cd_id = session.next_id("cd")
    dish = CartDish(cart_dish_id=cd_id, dish_id=dish_id, name=rec.dish.name, source=source,
                    servings=rec.dish.base_servings, lines=_lines_for_dish(session, rec, cd_id, ctx, store),
                    added_by_suggestion_id=suggestion_id)
    cart = session.cart.model_copy(deep=True)
    cart.dishes.insert(len(cart.dishes) if index is None else index, dish)
    session.cart = allocate(cart, store)
    return next(d for d in session.cart.dishes if d.cart_dish_id == cd_id)


def _find_line(cart: Cart, line_id: str) -> CartLine:
    ln = next((ln for ln in cart.lines() if ln.line_id == line_id), None)
    if ln is None:
        raise CartRuleError("STALE", "That item is no longer in your cart.")
    return ln


def remove_line(session, line_id: str, store: Store) -> None:
    cart = session.cart.model_copy(deep=True)
    _find_line(cart, line_id)
    for d in cart.dishes:
        d.lines = [ln for ln in d.lines if ln.line_id != line_id]
    cart.dishes = [d for d in cart.dishes if d.lines]
    session.cart = allocate(cart, store)


def remove_dish(session, cart_dish_id: str, store: Store) -> None:
    cart = session.cart.model_copy(deep=True)
    if not any(d.cart_dish_id == cart_dish_id for d in cart.dishes):
        raise CartRuleError("STALE", "That dish is no longer in your cart.")
    cart.dishes = [d for d in cart.dishes if d.cart_dish_id != cart_dish_id]
    session.cart = allocate(cart, store)


def set_quantity(session, line_id: str, quantity: int, store: Store) -> None:
    """C35: quantity multiplies the packs a priced line owns; a shared line takes no quantity."""
    if not 1 <= quantity <= 9:
        raise CartRuleError("TOO_MANY_PACKS", "Quantity must be 1 to 9.")
    cart = session.cart.model_copy(deep=True)
    ln = _find_line(cart, line_id)
    if not ln.priced:
        raise CartRuleError("SHARED_LINE", "This item shares a pack with another dish. Change it on the active line.",
                            active_line_id=ln.shared_from_line_id)
    if any(p.count // ln.quantity * quantity > MAX_PACKS for p in ln.packs):
        raise CartRuleError("TOO_MANY_PACKS", f"At most {MAX_PACKS} packs per item.")
    ln.quantity = quantity
    session.cart = allocate(cart, store)


def switch_variant(session, line_id: str, variant_id: str, ctx, store: Store) -> None:
    """FR-114: only an eligible variant of the same ingredient."""
    cart = session.cart.model_copy(deep=True)
    ln = _find_line(cart, line_id)
    group = {v.variant_id: v for v in store.variants_for(ln.ingredient_name)}
    if variant_id not in group:
        raise CartRuleError("WRONG_INGREDIENT", f"That product isn't a kind of {ln.ingredient_name}.")
    if not check_variant(group[variant_id], session.snapshot, store).eligible:
        raise CartRuleError("NOT_ELIGIBLE", "That product isn't available with your settings.")
    if variant_id != ln.variant_id:
        old = ln.variant_id
        ln.variant_id, ln.reason, ln.quantity = variant_id, "Chosen by you", 1
        ln.alternative_variant_ids = [old, *[a for a in ln.alternative_variant_ids if a not in (old, variant_id)]][:3]
    session.cart = allocate(cart, store)


def _flavour_note(old, new) -> str:
    if old.base_id == new.base_id:
        return "Same product type, so the taste should be very close."
    return "A close alternative; the taste may differ slightly."


def propose_substitution(session, line_id: str, ctx, store: Store):
    """FR-76: the best in-stock, eligible alternative for a line. Offered only; the cart is unchanged."""
    from backend.flows.cards import Substitution

    ln = _find_line(session.cart, line_id)
    levers = session.snapshot
    levers.business.stock_filter = True  # a substitute must be in stock
    group = {v.variant_id: v for v in store.variants_for(ln.ingredient_name)}

    def ok(vid):
        return vid != ln.variant_id and vid in group and check_variant(group[vid], levers, store).eligible

    pick = next((vid for vid in ln.alternative_variant_ids if ok(vid)), None)
    if pick is None:
        choice = choose_variant(ln.ingredient_name, levers, ctx, store)
        pick = next((v.variant_id for v, _ in choice.scored if ok(v.variant_id)), None)
    if pick is None:
        return None
    trial = session.cart.model_copy(deep=True)
    _find_line(trial, line_id).variant_id = pick
    delta = view(allocate(trial, store), store).subtotal_inr - view(allocate(session.cart, store), store).subtotal_inr
    old, new = store.variant(ln.variant_id), store.variant(pick)
    sub_id = session.next_id("sb")
    session.pending[sub_id] = {"kind": "substitution", "line_id": line_id, "variant_id": pick}
    return Substitution(substitution_id=sub_id, from_item=old.name, to_item=new.name, price_delta_inr=delta,
                        flavour_note=_flavour_note(old, new))


def answer_substitution(session, substitution_id: str, choice: str, ctx, store: Store) -> bool:
    """Accept applies the swap; decline changes nothing. Returns True when the cart changed."""
    pending = session.pending.get(substitution_id)
    if not pending or pending["kind"] != "substitution":
        raise CartRuleError("STALE", "That swap is no longer available.")
    del session.pending[substitution_id]
    if choice != "accept":
        return False
    switch_variant(session, pending["line_id"], pending["variant_id"], ctx, store)
    return True
