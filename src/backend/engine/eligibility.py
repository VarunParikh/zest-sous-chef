"""Eligibility mask M_elig: hard guardrails in code, after retrieval (FR-60, 90, 91, 112, 116; G9).

Each check recomputes tags from the variant's ingredient list with the lexicon and
combines them with the stored tags, taking the stricter value. A mis-tagged or
tampered variant therefore cannot slip through on its tags (T-019). Masks intersect
(FR-09). Rules are simplified for demonstration and are not medical or religious advice.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from backend.catalogue.models import Variant
from backend.catalogue.seed import DishRecord, Lexicon
from backend.catalogue.store import Store
from backend.catalogue.tags import DIET_RANK, UnknownIngredient, derive
from backend.session.levers import LeverSet

PURE_VEG = "Pure Veg (Strict)"
JAIN_DIET = "Jain (No Root Veggies / Pure Veg)"
JAIN_FAITH = "Jain (Strict Root-Free)"
SHRAVAN = "Hindu (Shravan Month / Fasting Active)"
HALAL = "Muslim (Strict Halal Only)"
KETO_CATEGORIES = {"grains", "pulses", "bakery", "sweeteners", "breakfast", "snacks", "ready", "frozen"}  # C25
KETO_MAX_CARBS = 10.0
UNIT_FACTOR = {"g": ("g", 1), "kg": ("g", 1000), "ml": ("ml", 1), "l": ("ml", 1000), "piece": ("piece", 1), "bunch": ("bunch", 1)}


@dataclass(frozen=True)
class Effective:
    diet_class: str
    flags: frozenset[str]
    allergens: frozenset[str]
    terms: frozenset[str]
    vegan: bool
    jain_ok: bool
    satvik_ok: bool
    gluten_free: bool
    halal_bad: bool


_CACHE: dict[tuple[int, tuple[str, ...]], tuple | None] = {}


def _derived(items: tuple[str, ...], lexicon: Lexicon) -> tuple | None:
    key = (id(lexicon), items)
    if key not in _CACHE:
        try:
            t = derive(list(items), lexicon, base_term_first=True)
            _CACHE[key] = (t, frozenset(lexicon.canonical(i) for i in items))
        except UnknownIngredient:
            _CACHE[key] = None
    return _CACHE[key]


def effective_tags(v: Variant, lexicon: Lexicon) -> Effective:
    got = _derived(tuple(v.ingredient_list), lexicon)
    if got is None:  # unknown ingredient: treat as the strictest possible item
        return Effective("non_veg", frozenset({"meat"}), frozenset(), frozenset(), False, False, False, False, True)
    t, terms = got
    diet = max(v.diet_class, t.diet_class, key=DIET_RANK.__getitem__)
    flags = frozenset(v.flags) | frozenset(t.flags)
    return Effective(
        diet_class=diet,
        flags=flags,
        allergens=frozenset(v.allergens) | frozenset(t.allergens),
        terms=terms,
        vegan=v.vegan and t.vegan,
        jain_ok=v.jain_ok and t.jain_ok,
        satvik_ok=v.satvik_ok and t.satvik_ok,
        gluten_free=v.gluten_free and t.gluten_free,
        halal_bad=v.halal_status == "not_halal" or bool(terms & {"pork", "gelatin"}) or "alcohol" in flags,
    )


@dataclass(frozen=True)
class Mask:
    eligible: bool
    failed: tuple[str, ...] = ()
    flags: tuple[str, ...] = ()


def check_variant(v: Variant, levers: LeverSet, store: Store, declared_allergens: tuple[str, ...] = ()) -> Mask:
    e = effective_tags(v, store.lexicon)
    veg = e.diet_class in {"vegan", "vegetarian"}
    failed, flags = [], []
    if levers.diet == PURE_VEG and not veg:
        failed.append("diet:pure_veg")
    if levers.diet == JAIN_DIET and not e.jain_ok:
        failed.append("diet:jain")
    if levers.faith == JAIN_FAITH and not e.jain_ok:
        failed.append("faith:jain")
    if levers.faith == SHRAVAN and not e.satvik_ok:
        failed.append("faith:shravan")
    if levers.faith == HALAL and e.halal_bad:
        failed.append("faith:halal")
    diets = set(levers.specialized_diets)
    if "Keto Diet" in diets and v.category in KETO_CATEGORIES and v.nutrition.carbs_g > KETO_MAX_CARBS:
        failed.append("special:keto")
    if "Intermittent Fasting / Low-GI" in diets and v.gi_label not in {"low", "not_applicable"}:
        failed.append("special:low_gi")
    if "Vegan" in diets and not e.vegan:
        failed.append("special:vegan")
    if "Gluten-Free" in diets and not e.gluten_free:
        failed.append("special:gluten_free")
    for a in declared_allergens:
        if a in e.allergens:
            failed.append(f"allergen:{a}")
    if not store.in_stock(v.variant_id):
        (failed if levers.business.stock_filter else flags).append("stock" if levers.business.stock_filter else "out_of_stock")
    return Mask(not failed, tuple(failed), tuple(flags))


@dataclass
class DishMask:
    eligible: bool
    failed: tuple[str, ...]
    blocked: dict[str, tuple[str, ...]] = field(default_factory=dict)  # essential term -> rules that removed every variant
    dropped_optional: tuple[str, ...] = ()
    chosen_pool: dict[str, list[Variant]] = field(default_factory=dict)  # essential term -> eligible variants
    basket_cost_inr: int | None = None


def _packs_cost(need_qty: float, need_unit: str, v: Variant, store: Store, stock_filter: bool) -> int | None:
    best = None
    unit, factor = UNIT_FACTOR[need_unit]
    need = need_qty * factor
    for s in store.skus_for(v.variant_id):
        if stock_filter and not (store.stock(s) > 0 and s.dark_store_ok):
            continue
        pack_unit, pack_factor = UNIT_FACTOR[s.pack.unit.value]
        packs = math.ceil(need / (s.pack.qty * pack_factor)) if pack_unit == unit else 1
        cost = s.price_inr * max(1, packs)
        best = cost if best is None or cost < best else best
    return best


def check_dish(
    rec: DishRecord,
    levers: LeverSet,
    store: Store,
    kind: str = "dish",
    cart_terms: set[str] | frozenset[str] = frozenset(),
    declared_allergens: tuple[str, ...] = (),
) -> DishMask:
    """A dish is eligible when every essential ingredient has at least one eligible variant.
    Optional lines without an eligible variant are dropped, never carted. For add-ons the
    price cap applies to the basket cost of the dish (C18): the cheapest eligible, in-stock
    packs covering each essential ingredient not already in the cart."""
    blocked, dropped, pool = {}, [], {}
    cost, priced = 0, True
    for line in rec.ingredients:
        term = store.lexicon.canonical(line.ingredient_name) or line.ingredient_name
        variants = store.variants_for(line.ingredient_name)
        masks = [(v, check_variant(v, levers, store, declared_allergens)) for v in variants]
        ok = [v for v, m in masks if m.eligible]
        if not ok:
            if line.essential:
                rules = sorted({r for _, m in masks for r in m.failed}) or ["not_in_catalogue"]
                blocked[term] = tuple(rules)
            else:
                dropped.append(term)
            continue
        if line.essential:
            pool[term] = ok
            if kind == "addon" and term not in cart_terms:
                costs = [c for v in ok if (c := _packs_cost(line.qty, line.unit.value, v, store, levers.business.stock_filter)) is not None]
                if costs:
                    cost += min(costs)
                else:
                    priced = False
    failed = sorted({r for rules in blocked.values() for r in rules})
    basket = cost if kind == "addon" and priced else None
    if kind == "addon" and basket is not None and basket > levers.business.price_cap_inr:
        failed.append("price_cap")
    return DishMask(not failed, tuple(failed), blocked, tuple(dropped), pool, basket)
