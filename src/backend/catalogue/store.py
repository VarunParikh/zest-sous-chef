"""Catalogue service: the only source of products, prices and stock (Constitution; FR-112).

Loads the generated variants and SKUs and resolves a recipe ingredient term to its
candidate variants. Resolution is tiered so a recipe asking for `milk` gets milk,
not kulfi or milk powder:
  1. plain products: the base term itself, no product form, no extra ingredients;
  2. same base product, with extra ingredients;
  3. other products built on the term (a product form such as `milk powder`);
  4. products that contain the term as an extra (`yeast` -> dry yeast), preferring
     ones whose name mentions it.
The first non-empty tier is returned. Retrieval (block 1.4) ranks within it.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from functools import cached_property
from pathlib import Path

from backend.catalogue.generator import product_form
from backend.catalogue.models import Pairing, Sku, Variant
from backend.catalogue.seed import DishRecord, Lexicon, load_dishes, load_lexicon, load_pairings, load_synonyms, load_taxonomy

GENERATED = Path(__file__).resolve().parents[3] / "mock-data" / "generated"


@dataclass(frozen=True)
class Store:
    variants: list[Variant]
    skus: list[Sku]
    dishes: list[DishRecord]
    lexicon: Lexicon
    forms: dict[str, str | None] = field(default_factory=dict)  # base_id -> product form, if any
    pairings: list[Pairing] = field(default_factory=list)
    synonyms: list[dict] = field(default_factory=list)
    stock_override: dict[str, int] = field(default_factory=dict)
    price_override: dict[str, int] = field(default_factory=dict)

    @cached_property
    def _by_id(self) -> dict[str, Variant]:
        return {v.variant_id: v for v in self.variants}

    @cached_property
    def _skus_by_variant(self) -> dict[str, list[Sku]]:
        out: dict[str, list[Sku]] = {}
        for s in self.skus:
            out.setdefault(s.variant_id, []).append(s)
        for v in out.values():
            v.sort(key=lambda s: s.pack.qty)
        return out

    @cached_property
    def _dish_by_id(self) -> dict[str, DishRecord]:
        return {d.dish.dish_id: d for d in self.dishes}

    @cached_property
    def _tiers(self) -> dict[str, list[list[Variant]]]:
        tiers: dict[str, list[list[Variant]]] = {}
        for v in self.variants:
            term = self.lexicon.canonical(v.ingredient_list[0])
            pure = len(v.ingredient_list) == 1
            form = self.forms.get(v.base_id)
            plain = form is None or self.lexicon.canonical(form) == term  # `Tea` is an alias of `tea leaves`
            tier = (0 if pure else 1) if plain else 2
            tiers.setdefault(term, [[], [], [], []])[tier].append(v)
            for extra in v.ingredient_list[1:]:
                t = self.lexicon.canonical(extra)
                if t and t != term:
                    tiers.setdefault(t, [[], [], [], []])[3].append(v)
        return tiers

    def variant(self, variant_id: str) -> Variant:
        return self._by_id[variant_id]

    def dish(self, dish_id: str) -> DishRecord:
        return self._dish_by_id[dish_id]

    def skus_for(self, variant_id: str) -> list[Sku]:
        return self._skus_by_variant.get(variant_id, [])

    def stock(self, sku: Sku) -> int:
        return self.stock_override.get(sku.sku_id, sku.stock_count)

    def price(self, sku: Sku) -> int:
        return self.price_override.get(sku.sku_id, sku.price_inr)

    def sku(self, sku_id: str) -> Sku:
        return self._sku_by_id[sku_id]

    @cached_property
    def _sku_by_id(self) -> dict[str, Sku]:
        return {s.sku_id: s for s in self.skus}

    def in_stock(self, variant_id: str) -> bool:
        return any(self.stock(s) > 0 and s.dark_store_ok for s in self.skus_for(variant_id))

    def variants_for(self, item: str) -> list[Variant]:
        term = self.lexicon.canonical(item)
        word = item.strip().lower()
        for i, tier in enumerate(self._tiers.get(term, [])):
            if not tier:
                continue
            if word != term:  # an alias naming a specific kind (`jowar` for the group term `millet`)
                named = [v for v in tier if word in v.name.lower() or word in v.ingredient_list[0]]
                if named:
                    return named
            if i == 3:
                named = [v for v in tier if term in v.name.lower()]
                return named or list(tier)
            return list(tier)
        return []

    def with_dishes(self, dishes: list[DishRecord]) -> "Store":
        return replace(self, dishes=dishes)

    def with_stock(self, overrides: dict[str, int]) -> "Store":
        """A copy with scripted stock levels (stock scenarios, tests)."""
        new = replace(self, stock_override={**self.stock_override, **overrides})
        return new

    def with_prices(self, overrides: dict[str, int]) -> "Store":
        """A copy with scripted prices (price-change scenarios, tests)."""
        return replace(self, price_override={**self.price_override, **overrides})


def load_store(generated_dir: Path = GENERATED) -> Store:
    lexicon, taxonomy = load_lexicon(), load_taxonomy()
    return Store(
        variants=[Variant.model_validate(r) for r in json.loads((generated_dir / "variants.json").read_text())],
        skus=[Sku.model_validate(r) for r in json.loads((generated_dir / "skus.json").read_text())],
        dishes=load_dishes(lexicon=lexicon, taxonomy=taxonomy),
        lexicon=lexicon,
        forms={b.base_id: product_form(b) for b in taxonomy},
        pairings=load_pairings(),
        synonyms=load_synonyms(),
    )
