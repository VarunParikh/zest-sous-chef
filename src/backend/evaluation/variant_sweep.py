"""E12 variant scoring gate (Evaluation Plan §4 E12; ADR-008).

For one β0, each ingredient records the chosen variant at the two ends of a lever:
organic 0 vs 1, gourmet 0 vs 1, and value term off (β0 = 0) vs on, at gourmet 0 where β is
largest. An effect is visible when the two choices differ. Gate: every effect visible on at
least 4 of 6 ingredients. A β0 is rejected when, at organic 1 and gourmet 0, price picks a
non-organic variant for every ingredient that has an eligible organic one.
"""
from __future__ import annotations

from dataclasses import dataclass

MIN_VISIBLE = 4


@dataclass(frozen=True)
class IngredientSweep:
    name: str
    organic: tuple[str, str]  # chosen variant at organic 0, organic 1
    gourmet: tuple[str, str]  # gourmet 0, gourmet 1
    price: tuple[str, str]  # gourmet 0 with β0 = 0, gourmet 0 with this β0
    organic_at_max_beta: bool  # organic 1, gourmet 0: the chosen variant is organic
    has_organic: bool  # an eligible organic variant exists
    cheapest_at_g0: bool
    premium_at_g1: bool


def e12_gate(rows: list[IngredientSweep]) -> dict:
    out = {}
    for effect in ("organic", "gourmet", "price"):
        k = sum(getattr(r, effect)[0] != getattr(r, effect)[1] for r in rows)
        out[effect] = {"k": k, "n": len(rows), "visible": k >= MIN_VISIBLE}
    with_organic = [r for r in rows if r.has_organic]
    out["price_overrides_organic"] = bool(with_organic) and not any(r.organic_at_max_beta for r in with_organic)
    out["cheapest_at_gourmet_0"] = {"k": sum(r.cheapest_at_g0 for r in rows), "n": len(rows)}
    out["premium_at_gourmet_1"] = {"k": sum(r.premium_at_g1 for r in rows), "n": len(rows)}
    ok = all(out[e]["visible"] for e in ("organic", "gourmet", "price")) and not out["price_overrides_organic"]
    out["status"] = "PASS" if ok else "FAIL"
    return out
