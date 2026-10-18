"""Pack allocation with shared lines (FR-71, 73; Data Model v0.3 §8.4; C33, C35).

Pure code over catalogue data. For each variant the needs of all its lines are
added up in cart order, and one pack set covers the total: least quantity, then
fewest packs, then lowest price, within stock. Packs and needs are laid end to
end; a pack belongs to the line whose need covers the pack's starting point.
"""
from __future__ import annotations

import itertools
import math

from backend.cart.models import Cart, PackItem
from backend.catalogue.models import Sku
from backend.catalogue.store import Store
from backend.engine.eligibility import UNIT_FACTOR

MAX_PACKS = 9


def _base(qty: float, unit: str) -> tuple[str, float]:
    base, factor = UNIT_FACTOR[unit]
    return base, qty * factor


def _available(store: Store, sku: Sku) -> int:
    return store.stock(sku) if sku.dark_store_ok else 0


def smallest_pack_set(need: float, need_unit: str, skus: list[Sku], store: Store) -> tuple[list[tuple[Sku, int]], bool, bool]:
    """Returns (packs, in_stock, estimated). With no in-stock cover, the best unconstrained set and in_stock False."""
    if not skus:
        return [], False, False
    unit, amount = _base(need, need_unit)
    usable = [s for s in skus if _base(s.pack.qty, s.pack.unit.value)[0] == unit]
    if not usable:  # e.g. "2 piece" of something sold by weight: one smallest pack
        s = min(skus, key=lambda s: (s.pack.qty, store.price(s)))
        return [(s, 1)], _available(store, s) > 0, True

    def best(limit_by_stock: bool):
        sizes = [_base(s.pack.qty, s.pack.unit.value)[1] for s in usable]
        ranges = []
        for s, size in zip(usable, sizes):
            top = math.ceil(amount / size)
            if limit_by_stock:
                top = min(top, _available(store, s))
            ranges.append(range(0, top + 1))
        found = None
        for counts in itertools.product(*ranges):
            total = sum(c * size for c, size in zip(counts, sizes))
            if total + 1e-9 < amount or not any(counts):
                continue
            key = (round(total, 6), sum(counts), sum(c * store.price(s) for c, s in zip(counts, usable)))
            if found is None or key < found[0]:
                found = (key, counts)
        return None if found is None else [(s, c) for s, c in zip(usable, found[1]) if c]

    packs = best(limit_by_stock=True)
    if packs is not None:
        return packs, True, False
    return best(limit_by_stock=False) or [], False, False


def allocate(cart: Cart, store: Store) -> Cart:
    """A new cart with packs, ownership, prices and stock flags recomputed from the catalogue."""
    out = cart.model_copy(deep=True)
    groups: dict[str, list] = {}
    for ln in out.lines():
        groups.setdefault(ln.variant_id, []).append(ln)
    used: set[str] = set()
    for variant_id, group in groups.items():
        unit = _base(1, group[0].need_unit.value)[0]
        same = [ln for ln in group if _base(1, ln.need_unit.value)[0] == unit]
        needs = [_base(ln.need_qty, ln.need_unit.value)[1] for ln in same]
        packs, in_stock, estimated = smallest_pack_set(sum(needs), group[0].need_unit.value,
                                                       store.skus_for(variant_id), store)
        singles = sorted((s for s, n in packs for _ in range(n)), key=lambda s: -s.pack.qty)
        starts, pos = [], 0.0
        for s in singles:
            starts.append((pos, pos + _base(s.pack.qty, s.pack.unit.value)[1], s))
            pos = starts[-1][1]
        spans, pos = [], 0.0
        for ln, need in zip(same, needs):
            spans.append((ln, pos, pos + need))
            pos += need
        for ln, lo, hi in spans:
            owned: dict[str, int] = {}
            for p_lo, _, s in starts:
                if lo <= p_lo < hi:
                    owned[s.sku_id] = owned.get(s.sku_id, 0) + 1
            ln.in_stock, ln.estimated = in_stock, ln.estimated or estimated
            if owned:
                if any(n * ln.quantity > MAX_PACKS for n in owned.values()):
                    ln.quantity = 1
                ln.packs = [PackItem(sku_id=k, count=n * ln.quantity) for k, n in owned.items()]
                ln.priced, ln.shared_from_line_id = True, None
                used.update(owned)
            else:
                owner = next((o for o, o_lo, o_hi in spans if o is not ln and o.packs and
                              any(p_lo <= lo < p_hi and o_lo <= p_lo < o_hi for p_lo, p_hi, _ in starts)), None)
                ln.packs, ln.priced, ln.quantity = [], False, 1
                ln.shared_from_line_id = owner.line_id if owner else None
        for ln in group:
            if ln not in same:  # a different unit for the same variant: priced on its own
                p2, ok, _ = smallest_pack_set(ln.need_qty, ln.need_unit.value, store.skus_for(variant_id), store)
                ln.packs = [PackItem(sku_id=s.sku_id, count=n) for s, n in p2]
                ln.priced, ln.shared_from_line_id, ln.in_stock, ln.estimated = bool(p2), None, ok, True
                used.update(s.sku_id for s, _ in p2)
    out.quotes = {k: v for k, v in out.quotes.items() if k in used}
    for sku_id in used:
        out.quotes.setdefault(sku_id, store.price(store.sku(sku_id)))
    return out
