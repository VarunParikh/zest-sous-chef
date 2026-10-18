"""E8 price and data integrity checks (Evaluation Plan §4 E8; FR-71, FR-79).

Written separately from `backend.cart`: packs are re-derived by brute force from the raw
catalogue, and prices are recomputed from `skus.json`, so a defect in the cart code shows
up as a mismatch instead of being repeated here.
"""
from __future__ import annotations

import itertools
import math
import re
from dataclasses import dataclass

AMOUNT = re.compile(r"(?:₹|\bRs\.?)\s?(\d[\d,]*)")


@dataclass(frozen=True)
class Pack:
    sku_id: str
    size: float  # in the base unit (g, ml, piece, bunch)
    price: int
    available: int


def optimal_packs(need: float, packs: list[Pack], limit_by_stock: bool = True) -> dict[str, int] | None:
    """FR-71: least total quantity covering the need, then fewest packs, then lowest price."""
    ranges = [range(0, (min(math.ceil(need / p.size), p.available) if limit_by_stock else math.ceil(need / p.size)) + 1)
              for p in packs]
    best = None
    for counts in itertools.product(*ranges):
        total = sum(c * p.size for c, p in zip(counts, packs))
        if not any(counts) or total + 1e-9 < need:
            continue
        key = (round(total, 6), sum(counts), sum(c * p.price for c, p in zip(counts, packs)))
        if best is None or key < best[0]:
            best = (key, counts)
    if best is None:
        return None
    return {p.sku_id: c for p, c in zip(packs, best[1]) if c}


def rupees(text: str) -> list[int]:
    return [int(m.group(1).replace(",", "")) for m in AMOUNT.finditer(text)]


def cart_mismatches(view: dict, prices: dict[str, int]) -> list[dict]:
    """Line prices, dish totals and the subtotal recomputed from catalogue prices (`sku_id -> price`)."""
    out, subtotal = [], 0
    for d in view["dishes"]:
        dish_total = 0
        for ln in d["lines"]:
            expected = sum(prices[p["sku_id"]] * p["count"] for p in ln["packs"]) if ln["priced"] else 0
            if ln["price_inr"] != expected:
                out.append({"kind": "line_price", "line_id": ln["line_id"], "shown": ln["price_inr"], "expected": expected})
            if not ln["priced"] and (ln["packs"] or not ln["shared_from_line_id"]):
                out.append({"kind": "unpriced_line_not_shared", "line_id": ln["line_id"]})
            dish_total += expected
        if d["dish_total_inr"] != dish_total:
            out.append({"kind": "dish_total", "cart_dish_id": d["cart_dish_id"], "shown": d["dish_total_inr"], "expected": dish_total})
        subtotal += dish_total
    if view["subtotal_inr"] != subtotal:
        out.append({"kind": "subtotal", "shown": view["subtotal_inr"], "expected": subtotal})
    return out
