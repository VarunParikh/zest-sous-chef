"""Derive eligibility tags from an ingredient list (Data Model §1.3, §9; risk R22).

Tags are never typed by hand: they are the union of the lexicon entries of the
ingredients. Rules are simplified for demonstration and are not medical or
religious advice.
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.catalogue.seed import Lexicon

DIET_RANK = {"vegan": 0, "vegetarian": 1, "egg": 2, "non_veg": 3}
_BY_RANK = {v: k for k, v in DIET_RANK.items()}
NOT_JAIN = {"meat", "fish", "egg", "root_veg", "onion_garlic"}
NOT_SATVIK = {"onion_garlic", "non_satvik"}


@dataclass(frozen=True)
class Tags:
    diet_class: str
    flags: list[str]
    allergens: list[str]
    vegan: bool
    jain_ok: bool
    satvik_ok: bool
    gluten_free: bool


class UnknownIngredient(ValueError):
    pass


def derive(items: list[str], lexicon: Lexicon, base_term_first: bool = False) -> Tags:
    """`base_term_first`: items[0] is a taxonomy base term whose diet floor is ignored
    when the lexicon says "variants decide" (e.g. bread: the extras decide milk or egg)."""
    rank, flags, allergens = 0, set(), set()
    for i, item in enumerate(items):
        term = lexicon.canonical(item)
        if term is None:
            raise UnknownIngredient(item)
        entry = lexicon.entries[term]
        flags.update(entry.flags)
        allergens.update(entry.allergens)
        if base_term_first and i == 0 and entry.variants_decide:
            continue
        rank = max(rank, DIET_RANK[entry.diet_floor])
    diet = _BY_RANK[rank]
    veg = diet in {"vegan", "vegetarian"}
    return Tags(
        diet_class=diet,
        flags=sorted(flags),
        allergens=sorted(allergens),
        vegan=diet == "vegan" and not ({"honey", "dairy"} & flags),
        jain_ok=veg and not (NOT_JAIN & flags),
        satvik_ok=veg and not (NOT_SATVIK & flags),
        gluten_free="gluten" not in allergens and "gluten" not in flags,
    )
