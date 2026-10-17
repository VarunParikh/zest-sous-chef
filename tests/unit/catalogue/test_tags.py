"""Tag derivation from the ingredient lexicon (Data Model §1.3, §9; risk R22)."""
import pytest

from backend.catalogue.seed import load_lexicon
from backend.catalogue.tags import derive


@pytest.fixture(scope="module")
def lex():
    return load_lexicon()


def test_alias_resolves(lex):
    assert lex.canonical("kanda") == "onion"
    assert lex.canonical("milk (skimmed)") == "milk"
    assert lex.canonical("no-such-thing") is None


def test_onion_is_vegan_but_not_jain_or_satvik(lex):
    t = derive(["onion (red)"], lex)
    assert t.diet_class == "vegan" and t.vegan
    assert not t.jain_ok and not t.satvik_ok
    assert "onion_garlic" in t.flags


def test_paneer_is_vegetarian_with_milk(lex):
    t = derive(["paneer"], lex)
    assert t.diet_class == "vegetarian" and not t.vegan
    assert t.allergens == ["milk"]
    assert t.jain_ok and t.satvik_ok and t.gluten_free


def test_chicken_is_non_veg(lex):
    t = derive(["chicken (curry cut)", "salt"], lex)
    assert t.diet_class == "non_veg" and not t.jain_ok and not t.satvik_ok


def test_variants_decide_ignores_base_floor(lex):
    t = derive(["bread loaf", "wheat flour", "yeast", "salt"], lex, base_term_first=True)
    assert t.diet_class == "vegan"
    assert "gluten" in t.allergens and not t.gluten_free
    milk_bread = derive(["bread rolls", "refined flour", "milk"], lex, base_term_first=True)
    assert milk_bread.diet_class == "vegetarian"


def test_honey_not_vegan_but_jain_ok(lex):
    t = derive(["honey (raw)"], lex)
    assert t.diet_class == "vegetarian" and not t.vegan and t.jain_ok


def test_hidden_animal_ingredients(lex):
    assert derive(["gelatin"], lex).diet_class == "non_veg"
    assert derive(["parmesan (aged)"], lex).diet_class == "non_veg"


def test_mushroom_not_satvik(lex):
    t = derive(["mushroom (button)"], lex)
    assert not t.satvik_ok and t.jain_ok
