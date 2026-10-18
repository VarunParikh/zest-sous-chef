"""Catalogue generator (Data Model §4, Mock Data Plan §3a; NFR-08, NFR-12, NFR-13)."""
import json
import re

import pytest

from backend.catalogue.generator import SEED, build_catalogue, catalogue_bytes
from backend.catalogue.seed import load_lexicon, load_taxonomy


@pytest.fixture(scope="module")
def seed_data():
    return load_taxonomy(), load_lexicon()


@pytest.fixture(scope="module")
def cat(seed_data):
    return build_catalogue(*seed_data)


def test_counts(cat, seed_data):
    taxonomy, _ = seed_data
    assert len(cat.variants) == sum(len(b.variants) for b in taxonomy) >= 1000
    assert len(cat.skus) >= len(cat.variants)


def test_ids_unique(cat):
    assert len({v.variant_id for v in cat.variants}) == len(cat.variants)
    assert len({s.sku_id for s in cat.skus}) == len(cat.skus)


def test_ingredient_lists_unique(cat):
    lists = [tuple(sorted(v.ingredient_list)) for v in cat.variants]
    assert len(set(lists)) == len(lists)


def test_deterministic_for_same_seed(seed_data):
    assert catalogue_bytes(build_catalogue(*seed_data)) == catalogue_bytes(build_catalogue(*seed_data))


def test_different_seed_changes_output(seed_data):
    assert catalogue_bytes(build_catalogue(*seed_data, seed=SEED + 1)) != catalogue_bytes(build_catalogue(*seed_data))


def test_scale_set_reaches_5000_unique(seed_data):
    big = build_catalogue(*seed_data, scale=5)
    assert len(big.variants) >= 5000
    lists = [tuple(sorted(v.ingredient_list)) for v in big.variants]
    assert len(set(lists)) == len(lists)


def test_brands_are_clearly_mock(cat):
    assert all(v.brand.startswith("MockMart") for v in cat.variants)


def test_milk_variants_differ_where_levers_act(cat):
    milk = {v.attributes["variant"]: v for v in cat.variants if v.base_id == "B051"}
    assert milk["Skimmed"].nutrition.fat_g < milk["Full cream"].nutrition.fat_g
    assert milk["Organic"].organic_score > milk["Toned"].organic_score
    assert milk["A2 cow"].gourmet_score > milk["Toned"].gourmet_score


def test_halal_status(cat):
    for v in cat.variants:
        meat = {"meat", "fish"} & set(v.flags)
        if not meat:
            assert v.halal_status == "not_applicable"
        elif any(i.startswith("pork") for i in v.ingredient_list):
            assert v.halal_status == "not_halal"
        else:
            assert v.halal_status in {"halal", "not_halal"}
    chicken = [v for v in cat.variants if v.ingredient_list[0].startswith("chicken")]
    assert any(v.halal_status == "halal" for v in chicken)


def test_sku_prices_and_per_unit_order(cat):
    by_variant = {}
    for s in cat.skus:
        assert isinstance(s.price_inr, int) and s.price_inr > 0
        by_variant.setdefault(s.variant_id, []).append(s)
    for skus in by_variant.values():
        skus.sort(key=lambda s: s.pack.qty)
        per_unit = [s.price_inr / s.pack.qty for s in skus]
        assert per_unit == sorted(per_unit, reverse=True)


def test_embedding_text_has_no_price_or_stock(cat):
    bad = re.compile(r"₹|\binr\b|\brs\.?\s?\d|price|\b(in|out of) stock\b|\bstock (count|level)|\d+\s?(g|kg|ml|l)\b", re.I)
    for v in cat.variants:
        assert v.embedding_text and not bad.search(v.embedding_text), v.embedding_text


def test_catalogue_bytes_is_json(cat):
    data = json.loads(catalogue_bytes(cat))
    assert set(data) == {"variants", "skus"}


# Reviewed: soy milk is in these variants' declared extras, so the soy allergen is correct.
REVIEWED_NAME_TAGS = {"Plant protein shakes (Almond)", "Plant protein shakes (Oat)"}


def test_variant_names_agree_with_derived_tags(cat):
    """A name that promises veg, gluten-free, chicken or a non-soy plant milk must not
    derive the opposite from its ingredient list (taxonomy rule: base term + extras)."""
    bad = []
    for v in cat.variants:
        n = v.name.lower()
        if v.name in REVIEWED_NAME_TAGS:
            continue
        if re.search(r"\bveg\b|vegetarian|eggless|vegan|plant|dairy-free", n) and v.diet_class not in {"vegan", "vegetarian"}:
            bad.append(f"{v.name}: {v.diet_class}")
        if re.search(r"gluten[- ]free", n) and not v.gluten_free:
            bad.append(f"{v.name}: not gluten_free")
        if "chicken" in n and any(i.startswith("pork") for i in v.ingredient_list):
            bad.append(f"{v.name}: lists pork")
        if re.search(r"\((almond|oat|coconut)\)", n) and "soy" in v.allergens and "soy" not in n:
            bad.append(f"{v.name}: soy allergen")
    assert not bad, bad


def test_c68_replace_marker_puts_the_named_term_first():
    """C68: `!term` in a variant's extras replaces the base term as the first ingredient."""
    from backend.catalogue.generator import _ingredient_list
    from backend.catalogue.seed import BaseProduct, _parse_variant

    spec = _parse_variant("Corn tortilla~!corn,sunflower oil~1.2~-")
    assert spec.replaces == "corn" and spec.extras == ("sunflower oil",)
    base = BaseProduct("B999", "bakery", "Tortilla and wraps", "wheat flour", "pc", (4.0,), 10.0, (spec,))
    assert _ingredient_list(base, spec, 0) == ["corn (tortilla and wraps)", "sunflower oil"]
    plain = _parse_variant("Plain~sunflower oil~1.0~-")
    assert plain.replaces is None and _ingredient_list(base, plain, 0)[0] == "wheat flour (tortilla and wraps)"


def test_c68_carrier_marker_is_parsed(tmp_path):
    from backend.catalogue.seed import load_taxonomy as load

    (tmp_path / "01_x.txt").write_text("B001|dairy|Flavoured yoghurt|curd|g|100|10|Mango~mango~1.0~-|carrier\n"
                                       "B002|vegetables|Onion|onion|g|500|4|Red~=red~1.0~-\n")
    a, b = load(tmp_path)
    assert a.carrier is True and b.carrier is False
