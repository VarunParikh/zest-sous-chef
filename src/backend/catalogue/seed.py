"""Loaders for the curated seed files in `mock-data/` (Data Model §2, §4.4, §5)."""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

from backend.catalogue.models import Dish, Pairing, RecipeIngredient, Unit
from backend.config import REPO_ROOT

MOCK = REPO_ROOT / "mock-data"
UNIT_ALIASES = {"unit": "piece", "pc": "piece"}
GARNISH = {"coriander leaves", "mint", "curry leaves", "parsley", "basil", "spring onion"}
LIQUID = {"water", "milk", "buttermilk", "vegetable stock", "soy milk", "coconut"}
OIL = {"ghee", "butter"}
STAPLE_CATEGORIES = {"grains", "pulses", "bakery"}


def _split(value: str, sep: str = "|") -> list[str]:
    return [part.strip() for part in (value or "").split(sep) if part.strip()]


def strip_qualifier(item: str) -> str:
    """`milk (skimmed, organic)` -> `milk`."""
    return item.split(" (", 1)[0].strip().lower()


@dataclass
class LexEntry:
    term: str
    aliases: list[str]
    flags: list[str]
    allergens: list[str]
    diet_floor: str
    notes: str

    @property
    def variants_decide(self) -> bool:
        return "variants decide" in self.notes


@dataclass
class Lexicon:
    entries: dict[str, LexEntry]

    def alias_map(self) -> dict[str, str]:
        return {a: e.term for e in self.entries.values() for a in e.aliases}

    def canonical(self, item: str) -> str | None:
        name = strip_qualifier(item)
        if name in self.entries:
            return name
        return self.alias_map().get(name)


def load_lexicon(path: Path = MOCK / "ingredient_lexicon.csv") -> Lexicon:
    entries = {}
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            entries[r["term"]] = LexEntry(
                term=r["term"],
                aliases=_split(r["aliases"]),
                flags=_split(r["flags"]),
                allergens=_split(r["allergens"]),
                diet_floor=r["diet_class_floor"],
                notes=r["notes"] or "",
            )
    return Lexicon(entries)


@dataclass(frozen=True)
class VariantSpec:
    name: str
    extras: tuple[str, ...]
    qualifiers: tuple[str, ...]
    mult: float
    gourmet: bool
    organic: bool


@dataclass(frozen=True)
class BaseProduct:
    base_id: str
    category: str
    name: str
    term: str
    unit: str  # g, ml, pc
    packs: tuple[float, ...]
    ppu: float  # per 100 g, 100 ml or per piece
    variants: tuple[VariantSpec, ...]

    @property
    def price_range(self) -> tuple[float, float]:
        mults = [v.mult for v in self.variants]
        return self.ppu * min(mults) * 0.95, self.ppu * max(mults) * 1.05


def _parse_variant(text: str) -> VariantSpec:
    name, extras, mult, flags = text.split("~")
    items = [e.strip() for e in extras.split(",") if e.strip()]
    return VariantSpec(
        name=name.strip(),
        extras=tuple(e for e in items if not e.startswith("=")),
        qualifiers=tuple(e[1:].strip() for e in items if e.startswith("=")),
        mult=float(mult),
        gourmet="g" in flags,
        organic="o" in flags,
    )


def load_taxonomy(folder: Path = MOCK / "taxonomy") -> list[BaseProduct]:
    out = []
    for path in sorted(folder.glob("0*.txt")):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            bid, cat, name, term, unit, packs, ppu, variants = line.strip().split("|")
            out.append(
                BaseProduct(
                    base_id=bid,
                    category=cat,
                    name=name,
                    term=term,
                    unit=unit,
                    packs=tuple(sorted(float(p) for p in packs.split("/"))),
                    ppu=float(ppu),
                    variants=tuple(_parse_variant(v) for v in variants.split(";")),
                )
            )
    return out


@dataclass
class DishRecord:
    dish: Dish
    ingredients: list[RecipeIngredient] = field(default_factory=list)


def scale_class(term: str, unit: str, category: str | None) -> str:
    if term in {"salt", "black salt"}:
        return "salt"
    if term in OIL or term.endswith(" oil"):
        return "oil"
    if term in GARNISH:
        return "garnish"
    if unit == "ml" or term in LIQUID and unit != "piece":
        return "liquid"
    if category == "spices":
        return "spice"
    if category in STAPLE_CATEGORIES:
        return "staple"
    return "vegetable"


def _term_categories(taxonomy: list[BaseProduct], lexicon: Lexicon) -> dict[str, str]:
    cats: dict[str, str] = {}
    for b in taxonomy:
        cats.setdefault(lexicon.canonical(b.term) or b.term, b.category)
    return cats


def parse_ingredients(dish_id: str, text: str, lexicon: Lexicon, categories: dict[str, str]) -> list[RecipeIngredient]:
    lines = []
    for n, item in enumerate(text.split(";"), start=1):
        parts = item.strip().split(":")
        name, qty, unit = parts[0].strip(), float(parts[1]), UNIT_ALIASES.get(parts[2], parts[2])
        optional = len(parts) > 3 and parts[3] == "opt"
        canonical = lexicon.canonical(name) or name
        lines.append(
            RecipeIngredient(
                dish_id=dish_id,
                line_no=n,
                ingredient_name=name,
                qty=qty,
                unit=Unit(unit),
                scale_class=scale_class(canonical, unit, categories.get(canonical)),
                essential=not optional,
            )
        )
    return lines


def load_dishes(
    path: Path = MOCK / "dishes.csv", lexicon: Lexicon | None = None, taxonomy: list[BaseProduct] | None = None
) -> list[DishRecord]:
    lexicon = lexicon or load_lexicon()
    categories = _term_categories(taxonomy or load_taxonomy(), lexicon)
    out = []
    with open(path, newline="") as fh:
        for r in csv.DictReader(fh):
            dish = Dish(
                dish_id=r["dish_id"],
                name=r["name"],
                aliases=_split(r.get("aliases", "")),
                course=r["course"],
                cuisine=r["cuisine"],
                base_servings=int(r["serves"]),
                mood_tags=_split(r["moods"]),
                flavour=_split(r.get("flavour", "")),
                description=r.get("description", ""),
                diet_class=r["claimed_diet"],
                edge_case="international" in r["name"].lower() and r["dish_id"] in {"D34", "D35"},
            )
            out.append(DishRecord(dish, parse_ingredients(dish.dish_id, r["ingredients"], lexicon, categories)))
    return out


def load_pairings(path: Path = MOCK / "pairings.csv") -> list[Pairing]:
    with open(path, newline="") as fh:
        return [Pairing(dish_a=r["dish_a"], dish_b=r["dish_b"], strength=float(r["strength"]), note=r["note"])
                for r in csv.DictReader(fh)]


def load_synonyms(path: Path = MOCK / "synonyms.csv") -> list[dict]:
    with open(path, newline="") as fh:
        return [dict(r) for r in csv.DictReader(fh)]


def load_personas(path: Path = MOCK / "personas.json") -> dict:
    return json.loads(path.read_text())
