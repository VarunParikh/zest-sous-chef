"""Seed files: dishes, pairings and the add-on pool (Data Model §5; ADR-004 v2)."""
import pytest

from backend.catalogue.seed import load_dishes, load_pairings

COMPANION = {"side", "beverage", "dessert"}


@pytest.fixture(scope="module")
def dishes():
    return load_dishes()


def test_dish_ids_unique_and_sequential(dishes):
    ids = [d.dish.dish_id for d in dishes]
    assert ids == [f"D{i:02d}" for i in range(1, len(ids) + 1)]


def test_every_dish_has_text_for_embedding(dishes):
    for d in dishes:
        assert d.dish.description.strip(), d.dish.dish_id
        assert d.dish.flavour, d.dish.dish_id
        assert d.dish.mood_tags, d.dish.dish_id


def test_ingredient_lines_parse(dishes):
    for d in dishes:
        assert d.ingredients, d.dish.dish_id
        for line in d.ingredients:
            assert line.qty > 0 and line.unit.value in {"g", "kg", "ml", "l", "piece", "bunch"}


def test_optional_marker_parsed(dishes):
    optional = [line for d in dishes for line in d.ingredients if not line.essential]
    assert optional, "expected at least one optional (garnish) line"


def test_add_on_pool_growing(dishes):
    companions = [d for d in dishes if d.dish.course in COMPANION]
    assert len(companions) >= 30  # 8 in the original seed plus tranche 1


def test_pairings_reference_dishes(dishes):
    ids = {d.dish.dish_id for d in dishes}
    pairs = load_pairings()
    seen = set()
    for p in pairs:
        assert p.dish_a in ids and p.dish_b in ids and p.dish_a != p.dish_b
        assert 0 <= p.strength <= 1
        assert (p.dish_a, p.dish_b) not in seen
        seen.add((p.dish_a, p.dish_b))


def test_some_dishes_left_for_the_vector_arm(dishes):
    pairs = load_pairings()
    with_pair = {p.dish_a for p in pairs}
    as_companion = {p.dish_b for p in pairs}
    assert "D35" not in with_pair | as_companion  # sushi uncovered by design
    mains_without = [d for d in dishes if d.dish.course not in COMPANION and d.dish.dish_id not in with_pair]
    companions_unused = [d for d in dishes if d.dish.course in COMPANION and d.dish.dish_id not in as_companion]
    assert len(mains_without) >= 3 and len(companions_unused) >= 3
