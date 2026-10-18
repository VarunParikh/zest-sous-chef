"""Seeded catalogue generator (Data Model §4; Mock Data Plan §3a; NFR-08, 12, 13).

Every output is a pure function of the taxonomy, the lexicon and the seed. Each
variant draws from its own `random.Random` keyed by seed, base and variant, so
adding a row does not reshuffle the others. Prices, nutrition and stock are
invented mock values; brands are generic `MockMart` names.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path

from backend.catalogue.models import Nutrition, Pack, Sku, Unit, Variant
from backend.catalogue.seed import BaseProduct, Lexicon, VariantSpec
from backend.catalogue.tags import derive

SEED = 20261017
NON_FOOD = "non-food item"
UNIT = {"g": Unit.g, "ml": Unit.ml, "pc": Unit.piece}
UNIT_BASE = {"g": 100.0, "ml": 100.0, "pc": 1.0}

# Illustrative nutrition per 100 g or ml: (carbs, sugar, protein, fat). Not nutritional data.
NUTRITION_BY_CATEGORY = {
    "vegetables": (6, 3, 2, 0.3), "fruits": (14, 10, 1, 0.3), "dairy": (5, 5, 3.5, 3.5),
    "bakery": (50, 5, 9, 4), "grains": (72, 1, 10, 2), "pulses": (58, 2, 22, 1.5),
    "spices": (45, 3, 10, 10), "oils": (0, 0, 0, 100), "sweeteners": (98, 95, 0, 0),
    "meat": (0, 0, 22, 8), "protein": (8, 2, 40, 6), "beverages": (10, 9, 0.5, 0.5),
    "breakfast": (65, 15, 10, 10), "snacks": (55, 10, 10, 25), "sauces": (20, 15, 2, 5),
    "nuts": (20, 5, 20, 50), "frozen": (25, 10, 5, 10), "ready": (20, 4, 6, 6), "household": (0, 0, 0, 0),
}
NUTRITION_BY_TERM = {
    "paneer": (3, 3, 18, 20), "cheese": (2, 1, 24, 30), "parmesan": (3, 0, 35, 28), "butter": (0.5, 0.5, 0.8, 81),
    "ghee": (0, 0, 0, 99), "cream": (3, 3, 2, 35), "khoya": (25, 20, 15, 25), "egg": (1, 1, 13, 10),
    "tofu": (2, 1, 12, 6), "soy chunks": (33, 1, 52, 0.5), "whey protein": (8, 4, 75, 5), "milk": (5, 5, 3.3, 3),
    "curd": (4.5, 4.5, 3.5, 3), "buttermilk": (4, 4, 3, 1), "coconut": (15, 6, 3, 33), "avocado": (9, 0.7, 2, 15),
    "salt": (0, 0, 0, 0), "black salt": (0, 0, 0, 0), "water": (0, 0, 0, 0), "stevia": (0, 0, 0, 0),
    "honey": (82, 82, 0.3, 0), "jaggery": (95, 85, 0.4, 0.1), "fish": (0, 0, 20, 5), "prawns": (0, 0, 24, 1),
    "chicken": (0, 0, 24, 9), "mutton": (0, 0, 25, 20), "pork": (0, 0, 26, 14), "cocoa": (58, 2, 20, 14),
    "mushroom": (3, 2, 3, 0.3), "lettuce": (3, 1, 1, 0.2), "spinach": (4, 0.4, 3, 0.4), "broccoli": (7, 2, 3, 0.4),
    "cauliflower": (5, 2, 2, 0.3), "cucumber": (4, 2, 1, 0.1), "cabbage": (6, 3, 1, 0.1), "capsicum": (6, 4, 1, 0.3),
    "tomato": (4, 3, 1, 0.2), "almond": (22, 4, 21, 50), "walnut": (14, 3, 15, 65), "cashew": (30, 6, 18, 44),
    "peanut": (16, 4, 26, 49), "makhana": (77, 0, 9, 0.1), "quinoa": (64, 0, 14, 6), "oats": (66, 1, 17, 7),
    "potato": (17, 1, 2, 0.1), "sweet potato": (20, 4, 1.6, 0.1), "tea leaves": (0, 0, 0, 0), "coffee": (0, 0, 0, 0),
    "zucchini": (3, 2, 1, 0.3), "celery": (3, 1, 0.7, 0.2),
}
LOW_FAT = ("skimmed", "low fat", "toned")
HIGH_FAT = ("full fat", "full cream", "malai")
WHOLE_GRAIN = ("whole", "brown", "multigrain", "millet", "ragi", "bajra", "jowar", "oats", "steel", "dalia", "red", "unpolished")
DESSERT_WORDS = ("ice cream", "kulfi", "shrikhand", "mithai", "chocolate", "cake", "cookie", "brownie", "muffin", "jamun", "sweet")
SALAD_WORDS = ("salad", "lettuce", "rocket", "microgreen", "sprout")


@dataclass
class Catalogue:
    variants: list[Variant]
    skus: list[Sku]


def _rng(seed: int, *parts: object) -> random.Random:
    return random.Random(":".join(str(p) for p in (seed, *parts)))


def product_form(base: BaseProduct) -> str | None:
    """The base product's form when it differs from its lexicon term (`Milk powder` for `milk`).
    It is the first qualifier, so milk and milk powder never share an ingredient list."""
    form = re.sub(r"\s*\(.*?\)", "", base.name).strip().lower()
    return form if form and form not in {base.term, base.term + "s", base.term + "es"} else None


def _ingredient_list(base: BaseProduct, spec: VariantSpec, replica: int) -> list[str]:
    form = product_form(base)
    quals = ([form] if form else []) + list(spec.qualifiers) + (["organic"] if spec.organic else []) + ([f"line {replica + 1}"] if replica else [])
    if base.term == "-":
        return [f"{NON_FOOD} ({base.name.lower()}, {spec.name.lower()}{', line ' + str(replica + 1) if replica else ''})"]
    term = spec.replaces or base.term  # C68: a replacing variant names its own first ingredient
    head = f"{term} ({', '.join(quals)})" if quals else term
    return [head, *spec.extras]


def _nutrition(base: BaseProduct, spec: VariantSpec, lexicon: Lexicon, rng: random.Random) -> Nutrition:
    term = lexicon.canonical(spec.replaces or base.term) or spec.replaces or base.term
    carbs, sugar, protein, fat = NUTRITION_BY_TERM.get(term, NUTRITION_BY_CATEGORY[base.category])
    words = " ".join(spec.qualifiers + (spec.name.lower(),))
    if any(w in words for w in LOW_FAT):
        fat *= 0.3 if "skimmed" in words else 0.7
    if any(w in words for w in HIGH_FAT):
        fat *= 1.4
    if "protein" in words:
        protein *= 1.5
    if "sugar" in spec.extras and not any(w in words for w in ("no sugar", "nosugar", "zero")):
        carbs, sugar = carbs + 10, sugar + 10
    if any(w in words for w in ("no sugar", "nosugar", "zero sugar", "sugar free", "sugar-free", "low sugar")):
        sugar *= 0.2
    j = lambda x: round(x * rng.uniform(0.95, 1.05), 1)  # noqa: E731
    return Nutrition(carbs_g=j(carbs), sugar_g=j(min(sugar, carbs)), protein_g=j(protein), fat_g=j(fat))


GI_NOT_APPLICABLE = {"spices", "oils", "sauces", "household"}  # condiment amounts (C25)
GRAIN_EXTRAS = {"rice", "basmati rice", "semolina", "wheat flour", "refined flour"}


def _gi(n: Nutrition, base: BaseProduct, spec: VariantSpec) -> str:
    if n.carbs_g < 2 or base.category in GI_NOT_APPLICABLE:
        return "not_applicable"
    words = " ".join(spec.qualifiers + (spec.name.lower(), base.term) + spec.extras)
    if n.sugar_g >= 40:
        return "high"
    if base.category == "pulses" and not set(spec.extras) & GRAIN_EXTRAS:
        return "low"  # pulses are generally low-GI (simplified, not dietary advice)
    if n.carbs_g >= 60:
        return "medium" if any(w in words for w in WHOLE_GRAIN) else "high"
    if n.carbs_g >= 25:
        return "medium"
    return "low"


def _history_bucket(base: BaseProduct, spec: VariantSpec) -> str | None:
    text = f"{base.name} {spec.name}".lower()
    if any(w in text for w in DESSERT_WORDS):
        return "desserts"
    if any(w in text for w in SALAD_WORDS):
        return "salads"
    return {"bakery": "bakery", "dairy": "dairy", "meat": "kebabs"}.get(base.category)


def _halal(flags: list[str], items: list[str], lexicon: Lexicon, rng: random.Random) -> str:
    if not {"meat", "fish"} & set(flags):
        return "not_applicable"
    terms = {lexicon.canonical(i) for i in items}
    if terms & {"pork", "gelatin"} or "alcohol" in flags:
        return "not_halal"
    if terms & {"chicken", "mutton"}:
        return "halal" if rng.random() < 0.7 else "not_halal"
    return "halal"  # fish and prawns (simplified)


def _brand(spec: VariantSpec, rng: random.Random) -> str:
    if spec.organic:
        return "MockMart Organic"
    if spec.gourmet:
        return rng.choice(["MockMart Reserve", "MockMart Gourmet"])
    return rng.choice(["MockMart Basics", "MockMart Select", "MockMart Daily"])


def _attribute_phrase(spec: VariantSpec) -> str:
    words = list(spec.qualifiers) + (["organic"] if spec.organic else []) + (["premium"] if spec.gourmet else [])
    return ", ".join(words) if words else "regular"


def embedding_text(name: str, category: str, spec: VariantSpec, items: list[str], also: list[str]) -> str:
    """Data Model §7.2 variant template. Price, stock, pack, brand and diet tags are excluded."""
    text = f"{name}. Category: {category}. {_attribute_phrase(spec)}. Ingredients: {', '.join(items)}."
    if also:
        text += f" Also called: {', '.join(also)}."
    return text


def _variant(base: BaseProduct, spec: VariantSpec, replica: int, lexicon: Lexicon, seed: int) -> Variant:
    rng = _rng(seed, base.base_id, spec.name, replica)
    items = _ingredient_list(base, spec, replica)
    tags = derive(items, lexicon, base_term_first=True)
    name = f"{base.name} ({spec.name})" + (f" Line {replica + 1}" if replica else "")
    vid_hash = hashlib.sha1("|".join([base.base_id, spec.name, *items]).encode()).hexdigest()[:8]
    nutrition = _nutrition(base, spec, lexicon, rng)
    term = lexicon.canonical(spec.replaces or base.term)
    also = [base.name] + (lexicon.entries[term].aliases if term else [])
    attributes = {
        "variant": spec.name,
        "qualifiers": ",".join(spec.qualifiers) or "none",
        "organic": "yes" if spec.organic else "no",
        "premium": "yes" if spec.gourmet else "no",
    }
    if replica:
        attributes["line"] = str(replica + 1)
    gourmet = rng.uniform(0.7, 0.95) if spec.gourmet else min(0.6, max(0.0, 0.1 + 0.2 * (spec.mult - 1)) + rng.uniform(0, 0.1))
    organic = rng.uniform(0.8, 0.95) if spec.organic else rng.uniform(0.05, 0.3)
    return Variant(
        variant_id=f"{base.base_id.lower()}-{vid_hash}",
        base_id=base.base_id,
        name=name,
        category=base.category,
        history_bucket=_history_bucket(base, spec),
        attributes=attributes,
        ingredient_list=items,
        brand=_brand(spec, rng),
        price_per_unit_inr=round(base.ppu * spec.mult * rng.uniform(0.97, 1.03), 2),
        gourmet_score=round(gourmet, 3),
        organic_score=round(organic, 3),
        diet_class=tags.diet_class,
        flags=tags.flags,
        allergens=tags.allergens,
        halal_status=_halal(tags.flags, items, lexicon, rng),
        gluten_free=tags.gluten_free,
        vegan=tags.vegan,
        jain_ok=tags.jain_ok,
        satvik_ok=tags.satvik_ok,
        nutrition=nutrition,
        gi_label=_gi(nutrition, base, spec),
        icon=base.category,
        embedding_text=embedding_text(name, base.category, spec, items, also),
    )


def _fmt_qty(q: float) -> str:
    return (f"{q:g}").replace(".", "p")


def _skus(base: BaseProduct, variant: Variant, seed: int) -> list[Sku]:
    rng = _rng(seed, variant.variant_id, "sku")
    out, prev_unit_price = [], None
    for i, qty in enumerate(base.packs):  # ascending
        raw = variant.price_per_unit_inr * qty / UNIT_BASE[base.unit] * (1 - 0.04 * i)
        price = max(1, round(raw))
        if prev_unit_price is not None:
            price = max(1, min(price, int(prev_unit_price * qty)))  # larger pack never dearer per unit
        prev_unit_price = price / qty
        out.append(Sku(
            sku_id=f"{variant.variant_id}-{_fmt_qty(qty)}{base.unit}",
            variant_id=variant.variant_id,
            pack=Pack(qty=qty, unit=UNIT[base.unit]),
            price_inr=price,
            stock_count=0 if rng.random() < 0.05 else rng.randint(3, 60),
            dark_store_ok=rng.random() < 0.96,
        ))
    return out


def build_catalogue(taxonomy: list[BaseProduct], lexicon: Lexicon, seed: int = SEED, scale: int = 1) -> Catalogue:
    variants, skus = [], []
    for replica in range(scale):
        for base in taxonomy:
            for spec in base.variants:
                v = _variant(base, spec, replica, lexicon, seed)
                variants.append(v)
                skus.extend(_skus(base, v, seed))
    return Catalogue(variants, skus)


def _dump(rows: list) -> bytes:
    return (json.dumps([r.model_dump(mode="json") for r in rows], indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode()


def catalogue_bytes(cat: Catalogue) -> bytes:
    data = {"variants": [v.model_dump(mode="json") for v in cat.variants], "skus": [s.model_dump(mode="json") for s in cat.skus]}
    return json.dumps(data, sort_keys=True, ensure_ascii=False).encode()


def write_catalogue(cat: Catalogue, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = [out_dir / "variants.json", out_dir / "skus.json"]
    paths[0].write_bytes(_dump(cat.variants))
    paths[1].write_bytes(_dump(cat.skus))
    return paths
