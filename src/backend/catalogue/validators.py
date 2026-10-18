"""Data validators V1 to V17 (Data Model §13; V15 to V17 added by C68). Any FAIL fails the build.

Statuses are real: PASS, FAIL or NOT RUN (a check whose input or dependency does
not exist yet). They run on the generated JSON as shipped, not on in-memory
objects, so V1 checks what a reader of `mock-data/generated/` actually gets.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from pydantic import ValidationError

from backend.catalogue.generator import SEED, build_catalogue, product_form, write_catalogue
from backend.catalogue.models import Sku, Variant
from backend.catalogue.seed import (
    MOCK, BaseProduct, DishRecord, Lexicon, load_dishes, load_lexicon, load_pairings, load_personas,
    load_synonyms, load_taxonomy, strip_qualifier,
)
from backend.catalogue.tags import UnknownIngredient, derive
from backend.config import REPO_ROOT
from backend.session.levers import LeverSet, merge_levers

GENERATED = MOCK / "generated"
UNAVAILABLE_BY_DESIGN = {"D35": {"sushi rice", "nori", "wasabi"}}
LEVER_TEST = {"milk": "milk", "bread": "bread loaf", "rice": "rice", "oil": "sunflower oil",
              "paneer": "paneer", "flour": "wheat flour"}
PRICE_OR_STOCK = re.compile(
    r"₹|\binr\b|\brs\.?\s?\d|price|\b(in|out of) stock\b|\bstock (count|level)|\d+\s?(g|kg|ml|l)\b", re.I
)
RETRIEVAL_SET = REPO_ROOT / "eval" / "datasets" / "retrieval_v1.jsonl"
STOCK_SCENARIOS = MOCK / "stock_scenarios.json"


@dataclass
class Result:
    vid: str
    title: str
    status: str
    errors: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class Context:
    lexicon: Lexicon
    taxonomy: list[BaseProduct]
    dishes: list[DishRecord]
    pairings: list
    synonyms: list[dict]
    personas: dict
    variants: list[dict]
    skus: list[dict]
    generated_dir: Path
    seed: int = SEED
    scale: int = 1


def load_context(generated_dir: Path = GENERATED, scale: int = 1) -> Context:
    lexicon, taxonomy = load_lexicon(), load_taxonomy()
    return Context(
        lexicon=lexicon,
        taxonomy=taxonomy,
        dishes=load_dishes(lexicon=lexicon, taxonomy=taxonomy),
        pairings=load_pairings(),
        synonyms=load_synonyms(),
        personas=load_personas(),
        variants=json.loads((generated_dir / "variants.json").read_text()),
        skus=json.loads((generated_dir / "skus.json").read_text()),
        generated_dir=generated_dir,
        scale=scale,
    )


def _result(vid: str, title: str, errors: list[str], note: str = "") -> Result:
    return Result(vid, title, "FAIL" if errors else "PASS", errors, note)


def v1(ctx: Context) -> Result:
    errors = []
    for model, rows, key in ((Variant, ctx.variants, "variant_id"), (Sku, ctx.skus, "sku_id")):
        for row in rows:
            try:
                model.model_validate(row)
            except ValidationError as e:
                errors.append(f"{row.get(key, '?')}: {e.errors()[0]['loc']} {e.errors()[0]['msg']}")
    return _result("V1", "Required fields and types", errors, f"{len(ctx.variants)} variants, {len(ctx.skus)} SKUs")


def v2(ctx: Context) -> Result:
    errors = [f"{v.get('variant_id')}: empty ingredient list" for v in ctx.variants if not v.get("ingredient_list")]
    seen: dict[tuple, str] = {}
    for v in ctx.variants:
        key = tuple(sorted(v.get("ingredient_list") or []))
        if key in seen:
            errors.append(f"{v['variant_id']} repeats the ingredient list of {seen[key]}")
        seen.setdefault(key, v.get("variant_id"))
    return _result("V2", "Ingredient lists unique and non-empty", errors)


def v3(ctx: Context) -> Result:
    errors = []
    fields = ("diet_class", "flags", "allergens", "vegan", "jain_ok", "satvik_ok", "gluten_free")
    for v in ctx.variants:
        try:
            t = derive(v["ingredient_list"], ctx.lexicon, base_term_first=True)
        except UnknownIngredient as e:
            errors.append(f"{v['variant_id']}: cannot derive, unknown {e}")
            continue
        for f in fields:
            if v.get(f) != getattr(t, f):
                errors.append(f"{v['variant_id']}: {f} is {v.get(f)!r}, lexicon gives {getattr(t, f)!r}")
    for rec in ctx.dishes:
        essential = [i.ingredient_name for i in rec.ingredients if i.essential]
        try:
            t = derive(essential, ctx.lexicon)
        except UnknownIngredient as e:
            errors.append(f"{rec.dish.dish_id}: cannot derive, unknown {e}")
            continue
        if rec.dish.diet_class != t.diet_class:
            errors.append(f"{rec.dish.dish_id}: claimed {rec.dish.diet_class}, essential ingredients give {t.diet_class}")
        try:
            full = derive([i.ingredient_name for i in rec.ingredients], ctx.lexicon)
        except UnknownIngredient:
            continue
        if full.diet_class != rec.dish.diet_class:
            errors.append(f"{rec.dish.dish_id}: an optional line makes it {full.diet_class}, claimed {rec.dish.diet_class}")
    return _result("V3", "Derived tags equal a recomputation from the lexicon", errors)


def v4(ctx: Context) -> Result:
    errors = [
        f"{v['variant_id']}: {item!r}"
        for v in ctx.variants for item in v["ingredient_list"] if ctx.lexicon.canonical(item) is None
    ]
    errors += [
        f"{rec.dish.dish_id}: {i.ingredient_name!r}"
        for rec in ctx.dishes for i in rec.ingredients if ctx.lexicon.canonical(i.ingredient_name) is None
    ]
    return _result("V4", "Every ingredient term exists in the lexicon", errors)


def v5(ctx: Context) -> Result:
    errors = []
    for v in ctx.variants:
        meat = bool({"meat", "fish"} & set(v["flags"]))
        ok = v["halal_status"] in {"halal", "not_halal"} if meat else v["halal_status"] == "not_applicable"
        if not ok:
            errors.append(f"{v['variant_id']}: halal_status {v['halal_status']} with flags {v['flags']}")
        if any(strip_qualifier(i) == "pork" for i in v["ingredient_list"]) and v["halal_status"] != "not_halal":
            errors.append(f"{v['variant_id']}: pork must be not_halal")
    return _result("V5", "Halal status set for meat and fish only", errors)


def v6(ctx: Context) -> Result:
    errors = []
    ranges = {b.base_id: b.price_range for b in ctx.taxonomy}
    for v in ctx.variants:
        lo, hi = ranges.get(v["base_id"], (0, 0))
        if not lo <= v["price_per_unit_inr"] <= hi:
            errors.append(f"{v['variant_id']}: price per unit {v['price_per_unit_inr']} outside [{lo:.2f}, {hi:.2f}]")
    by_variant = defaultdict(list)
    for s in ctx.skus:
        if not isinstance(s["price_inr"], int) or s["price_inr"] <= 0:
            errors.append(f"{s['sku_id']}: price {s['price_inr']!r} is not a positive integer")
        by_variant[s["variant_id"]].append(s)
    for vid, skus in by_variant.items():
        skus.sort(key=lambda s: s["pack"]["qty"])
        for small, big in zip(skus, skus[1:]):
            if big["price_inr"] / big["pack"]["qty"] > small["price_inr"] / small["pack"]["qty"]:
                errors.append(f"{vid}: {big['sku_id']} dearer per unit than {small['sku_id']}")
    return _result("V6", "Prices in range; larger packs not dearer per unit", errors)


def v7(ctx: Context) -> Result:
    errors = [f"{s['sku_id']}: stock {s['stock_count']}" for s in ctx.skus if s["stock_count"] < 0]
    note = "stock counts checked"
    if STOCK_SCENARIOS.exists():
        known = {v["variant_id"] for v in ctx.variants} | {s["sku_id"] for s in ctx.skus}
        for sc in json.loads(STOCK_SCENARIOS.read_text()):
            for ev in sc.get("events", []):
                if ev["variant_or_sku_id"] not in known:
                    errors.append(f"scenario {sc['scenario_id']}: unknown {ev['variant_or_sku_id']}")
    else:
        note += "; scenario references NOT RUN (no stock_scenarios.json yet, written with UJ10/UJ22)"
    return _result("V7", "Stock non-negative; scenario references exist", errors, note)


def _catalogue_terms(ctx: Context) -> tuple[set[str], Counter]:
    """Terms a dish ingredient can resolve to (base term or extra, as in check_seed.py),
    and the number of variants per base term (for the lever-test minimum)."""
    terms, per_base = set(), Counter()
    for v in ctx.variants:
        for i, item in enumerate(v["ingredient_list"]):
            term = ctx.lexicon.canonical(item)
            if term:
                terms.add(term)
                if i == 0:
                    per_base[term] += 1
    return terms, per_base


def v8(ctx: Context) -> Result:
    errors = []
    terms, per_base = _catalogue_terms(ctx)
    gaps = []
    for rec in ctx.dishes:
        allowed = UNAVAILABLE_BY_DESIGN.get(rec.dish.dish_id, set())
        for i in rec.ingredients:
            term = ctx.lexicon.canonical(i.ingredient_name) or i.ingredient_name
            if term in allowed:
                gaps.append(f"{rec.dish.dish_id}:{term}")
            elif i.essential and term not in terms:
                errors.append(f"{rec.dish.dish_id}: {term} has no catalogue variant")
    for label, term in LEVER_TEST.items():
        if per_base[term] < 4:
            errors.append(f"lever-test ingredient {label} ({term}) has {per_base[term]} variants, needs 4")
    return _result("V8", "Dish ingredients resolve; lever-test ingredients have 4+ variants", errors,
                   "by-design gaps: " + ", ".join(gaps))


COMPANION_COURSES = {"side", "beverage", "dessert"}


def v9(ctx: Context) -> Result:
    """Each persona (which encodes its Must journeys' constraints) can be served: at least 3
    eligible non-companion dishes (the displayed set), 1 eligible companion and 1 eligible SKU,
    using the real eligibility engine with the default stock filter."""
    from backend.catalogue.store import Store
    from backend.engine.eligibility import check_dish, check_variant

    store = Store(
        variants=[Variant.model_validate(v) for v in ctx.variants],
        skus=[Sku.model_validate(s) for s in ctx.skus],
        dishes=ctx.dishes,
        lexicon=ctx.lexicon,
        forms={b.base_id: product_form(b) for b in ctx.taxonomy},
    )
    defaults = ctx.personas["defaults"]
    errors, counts = [], []
    for p in [{"id": "defaults", "levers": {}}] + ctx.personas["personas"]:
        lev = LeverSet.model_validate(merge_levers(defaults, p["levers"]))
        ok = [r for r in store.dishes if check_dish(r, lev, store).eligible]
        mains = [r for r in ok if r.dish.course not in COMPANION_COURSES]
        companions = [r for r in ok if r.dish.course in COMPANION_COURSES]
        skus = sum(check_variant(v, lev, store).eligible for v in store.variants)
        counts.append(f"{p['id']} {len(mains)}/{len(companions)}/{skus}")
        if len(mains) < 3 or not companions or not skus:
            errors.append(f"{p['id']}: {len(mains)} dishes, {len(companions)} companions, {skus} variants eligible")
    return _result("V9", "Every Must journey and persona has an eligible dish and SKU", errors,
                   "dishes/companions/variants: " + ", ".join(counts))


def v10(ctx: Context) -> Result:
    errors = []
    owners = defaultdict(set)
    for e in ctx.lexicon.entries.values():
        owners[e.term].add(e.term)
        for a in e.aliases:
            owners[a].add(e.term)
    errors += [f"lexicon name {n!r} claimed by {sorted(t)}" for n, t in owners.items() if len(t) > 1]
    moods = {m for rec in ctx.dishes for m in rec.dish.mood_tags}
    dish_names = {rec.dish.name.lower() for rec in ctx.dishes} | {rec.dish.dish_id for rec in ctx.dishes}
    targets = defaultdict(set)
    for s in ctx.synonyms:
        q, to, kind = s["query_term"].lower(), s["maps_to"].lower(), s["type"]
        targets[q].add(to)
        if kind == "ingredient":
            canonical = ctx.lexicon.canonical(to)
            if canonical is None:
                errors.append(f"synonym {q!r} -> {to!r}: target not in lexicon")
            elif q in owners and canonical not in owners[q]:
                errors.append(f"synonym {q!r} -> {to!r} contradicts lexicon {sorted(owners[q])}")
        elif kind == "mood" and to not in moods:
            errors.append(f"synonym {q!r} -> mood {to!r}: no dish has this mood")
        elif kind == "dish" and to not in dish_names:
            errors.append(f"synonym {q!r} -> dish {to!r}: no such dish")
    errors += [f"synonym {q!r} maps to {sorted(t)}" for q, t in targets.items() if len(t) > 1]
    return _result("V10", "Synonym targets exist; no colliding canonical terms", errors)


def v11(ctx: Context) -> Result:
    from backend.retrieval.documents import dish_embedding_text

    errors = []
    for v in ctx.variants:
        t = v.get("embedding_text", "")
        if not t.strip() or PRICE_OR_STOCK.search(t):
            errors.append(f"{v['variant_id']}: {t[:80]!r}")
    for rec in ctx.dishes:
        t = dish_embedding_text(rec)
        if not rec.dish.description.strip() or PRICE_OR_STOCK.search(t):
            errors.append(f"{rec.dish.dish_id}: {t[:80]!r}")
    return _result("V11", "Embedding texts non-empty, no price or stock tokens", errors)


def v12(ctx: Context) -> Result:
    if not RETRIEVAL_SET.exists():
        return Result("V12", "Retrieval evaluation set expected IDs exist", "NOT RUN",
                      note=f"{RETRIEVAL_SET.relative_to(REPO_ROOT)} not written yet (block 1.4/1.5)")
    known = ({rec.dish.dish_id for rec in ctx.dishes} | {v["variant_id"] for v in ctx.variants}
             | {f"term:{t}" for t in ctx.lexicon.entries})
    errors = []
    for line in RETRIEVAL_SET.read_text().splitlines():
        q = json.loads(line)
        errors += [f"{q['query_id']}: unknown {i}" for i in q["expected_ids"] if i not in known]
    return _result("V12", "Retrieval evaluation set expected IDs exist", errors)


def v13(ctx: Context) -> Result:
    import tempfile

    errors = []
    a = build_catalogue(ctx.taxonomy, ctx.lexicon, seed=ctx.seed, scale=ctx.scale)
    b = build_catalogue(ctx.taxonomy, ctx.lexicon, seed=ctx.seed, scale=ctx.scale)
    with tempfile.TemporaryDirectory() as tmp:
        pa = write_catalogue(a, Path(tmp) / "a")
        pb = write_catalogue(b, Path(tmp) / "b")
        for x, y in zip(pa, pb):
            if x.read_bytes() != y.read_bytes():
                errors.append(f"two runs differ: {x.name}")
            committed = ctx.generated_dir / x.name
            if not committed.exists() or committed.read_bytes() != x.read_bytes():
                errors.append(f"{committed} is not the output for seed {ctx.seed}; run `make data`")
    return _result("V13", "Generated output byte-identical for the same seed", errors)


def v14(ctx: Context) -> Result:
    errors = []
    defaults = ctx.personas["defaults"]
    for p in [{"id": "defaults", "levers": {}}] + ctx.personas["personas"]:
        try:
            LeverSet.model_validate(merge_levers(defaults, p["levers"]))
        except ValidationError as e:
            errors.append(f"{p['id']}: {e.errors()[0]['loc']} {e.errors()[0]['msg']}")
    return _result("V14", "Persona lever values within Settings Panel ranges", errors,
                   f"{len(ctx.personas['personas'])} personas")


def _term_names(ctx: Context) -> dict[str, str]:
    """Every way a lexicon term is written: the term, its aliases and its ingredient synonyms."""
    names = {}
    for e in ctx.lexicon.entries.values():
        for n in (e.term, *e.aliases):
            names[n.lower()] = e.term
    for s in ctx.synonyms:
        if s.get("type") == "ingredient" and s["maps_to"] in ctx.lexicon.entries:
            names.setdefault(s["query_term"].lower(), s["maps_to"])
    return names


def _named(text: str, names: dict[str, str]) -> set[str]:
    t = text.lower()
    return {term for n, term in names.items() if re.search(rf"\b{re.escape(n)}\b", t)}


def v15(ctx: Context) -> Result:
    """A variant named after an ingredient lists it first, unless its base product is declared a carrier (C68)."""
    names, bases, errors = _term_names(ctx), {b.base_id: b for b in ctx.taxonomy}, []
    for v in ctx.variants:
        base = bases.get(v["base_id"])
        if base is None or base.term == "-" or base.carrier:
            continue
        spec_name = v["attributes"]["variant"]
        first = ctx.lexicon.canonical(v["ingredient_list"][0]) or strip_qualifier(v["ingredient_list"][0])
        rest = {ctx.lexicon.canonical(i) or strip_qualifier(i) for i in v["ingredient_list"][1:]}
        named = _named(spec_name, names) - {first}
        if named & rest and first not in _named(f"{base.name} {spec_name}", names):
            errors.append(f"{v['variant_id']} {v['name']}: named {sorted(named & rest)} but lists {first} first "
                          "(use !term, or mark the base a carrier)")
    return _result("V15", "Variant named after an ingredient lists it first (or its base is a carrier)", errors)


NEGATIONS = (
    (r"\begg alternatives?\b|\beggless\b|\begg[- ]free\b", "egg", lambda v: v["diet_class"] == "egg" or "egg" in v["allergens"]),
    (r"\bdairy[- ]free\b|\bnon[- ]dairy\b|\bvegan\b|\bplant[- ]based\b", "vegan", lambda v: not v["vegan"]),
    (r"\bgluten[- ]free\b", "gluten_free", lambda v: not v["gluten_free"]),
    (r"\bsugar[- ]free\b|\bzero sugar\b", "no sugar", lambda v: any(strip_qualifier(i) == "sugar" for i in v["ingredient_list"])),
)
SOLID_FORMS = re.compile(r"\bcubes?\b|\btablets?\b")
LIQUID_FORMS = re.compile(r"\bjuice\b|\bsyrups?\b|\bsquash\b|\bsharbat\b|\bkombucha\b")


def v16(ctx: Context) -> Result:
    """Names agree with tags and units (C68)."""
    units: dict[str, set] = defaultdict(set)
    for s in ctx.skus:
        units[s["variant_id"]].add(s["pack"]["unit"])
    errors = []
    for v in ctx.variants:
        name = v["name"].lower()
        for pattern, meaning, broken in NEGATIONS:
            if re.search(pattern, name) and broken(v):
                errors.append(f"{v['variant_id']} {v['name']}: name implies {meaning}, tags disagree")
        u = units.get(v["variant_id"], set())
        if SOLID_FORMS.search(name) and "ml" in u:
            errors.append(f"{v['variant_id']} {v['name']}: a cube or tablet sold in ml")
        if LIQUID_FORMS.search(name) and u - {"ml"}:
            errors.append(f"{v['variant_id']} {v['name']}: a liquid sold in {sorted(u - {'ml'})}")
    return _result("V16", "Names agree with tags and units", errors)


BULK_PIECES, MAX_PER_PIECE_INR = 10, 20


def v17(ctx: Context) -> Result:
    """A pack of 10 or more pieces costs at most ₹20 per piece (C68)."""
    errors = [f"{s['sku_id']}: ₹{s['price_inr']} for {s['pack']['qty']:g} pieces (₹{s['price_inr'] / s['pack']['qty']:.1f} each)"
              for s in ctx.skus if s["pack"]["unit"] == "piece" and s["pack"]["qty"] >= BULK_PIECES
              and s["price_inr"] / s["pack"]["qty"] > MAX_PER_PIECE_INR]
    return _result("V17", "Bulk packs at most ₹20 per piece", errors)


VALIDATORS: dict[str, Callable[[Context], Result]] = {
    "V1": v1, "V2": v2, "V3": v3, "V4": v4, "V5": v5, "V6": v6, "V7": v7,
    "V8": v8, "V9": v9, "V10": v10, "V11": v11, "V12": v12, "V13": v13, "V14": v14,
    "V15": v15, "V16": v16, "V17": v17,
}


def run_all(ctx: Context) -> dict[str, Result]:
    return {vid: fn(ctx) for vid, fn in VALIDATORS.items()}


