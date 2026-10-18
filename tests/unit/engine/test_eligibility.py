"""Eligibility masks, guardrails in code (FR-60, 90, 91, 116; Data Model §9; T-010 to T-019)."""
import pytest

from backend.catalogue.seed import strip_qualifier
from backend.engine.eligibility import check_dish, check_variant
from tests.unit.engine.conftest import levers

PURE_VEG = "Pure Veg (Strict)"
JAIN = "Jain (No Root Veggies / Pure Veg)"


def _oracle(variant, lev, lexicon):
    """Independent rules from the lexicon and ingredient list only (T-010): never reads stored tags."""
    terms = [lexicon.canonical(i) for i in variant.ingredient_list]
    entries = [lexicon.entries[t] for t in terms]
    flags = {f for e in entries for f in e.flags}
    allergens = {a for e in entries for a in e.allergens}
    animal = flags & {"meat", "fish", "egg"} or any(e.diet_floor in {"egg", "non_veg"} for e in entries[1:]) \
        or (entries[0].diet_floor in {"egg", "non_veg"} and not entries[0].variants_decide)
    bad = []
    if lev.diet == PURE_VEG and animal:
        bad.append("pure_veg")
    if (lev.diet == JAIN or lev.faith == "Jain (Strict Root-Free)") and (animal or flags & {"root_veg", "onion_garlic", "fungi"}):
        bad.append("jain")
    if lev.faith.startswith("Hindu (Shravan") and (animal or flags & {"onion_garlic", "non_satvik"}):
        bad.append("shravan")
    if lev.faith == "Muslim (Strict Halal Only)" and ("alcohol" in flags or {"pork", "gelatin"} & set(terms)):
        bad.append("halal")
    if "Vegan" in lev.specialized_diets and (animal or flags & {"dairy", "honey"}):
        bad.append("vegan")
    if "Gluten-Free" in lev.specialized_diets and ("gluten" in allergens or "gluten" in flags):
        bad.append("gluten_free")
    return bad


@pytest.mark.parametrize("pid", ["defaults"] + [f"P{i}" for i in range(1, 12)])
def test_t010_no_ineligible_variant_passes_any_persona(store, personas, pid):
    lev = personas[pid]
    leaks = [v.name for v in store.variants
             if check_variant(v, lev, store).eligible and _oracle(v, lev, store.lexicon)]
    assert not leaks, leaks[:10]


@pytest.mark.parametrize("pid", ["defaults"] + [f"P{i}" for i in range(1, 12)])
def test_t010_eligible_dishes_have_only_eligible_essentials(store, personas, pid):
    lev = personas[pid]
    for rec in store.dishes:
        m = check_dish(rec, lev, store)
        if not m.eligible:
            continue
        for term, variant in m.chosen_pool.items():
            assert variant and all(check_variant(v, lev, store).eligible for v in variant), (rec.dish.dish_id, term)


def test_t011_jain_garlic_bread_blocked_with_alternative(store, personas):
    lev = personas["P1"]
    garlic_bread = store.dish("D32")
    m = check_dish(garlic_bread, lev, store)
    assert not m.eligible and "garlic" in m.blocked
    assert not any(check_variant(v, lev, store).eligible for v in store.variants_for("garlic"))
    alternatives = [r for r in store.dishes if r.dish.course == "side" and check_dish(r, lev, store).eligible]
    assert alternatives, "a compliant side must exist to offer instead"


def test_t012_engine_part_pure_veg_blocks_chicken_curry(store, personas):
    m = check_dish(store.dish("D03"), personas["P2"], store)  # dish of chicken video V2
    assert not m.eligible and "chicken" in m.blocked


def test_t013_halal_excludes_not_halal_and_alcohol(store, personas):
    lev = personas["P3"]
    for v in store.variants:
        ok = check_variant(v, lev, store).eligible
        if v.halal_status == "not_halal" or "alcohol" in v.flags:
            assert not ok, v.name
    assert any(check_variant(v, lev, store).eligible for v in store.variants if v.halal_status == "halal")


def test_t014_shravan_excludes_non_satvik(store, personas):
    lev = personas["P4"]
    assert not [v.name for v in store.variants if "non_satvik" in v.flags and check_variant(v, lev, store).eligible]


def test_t015_keto_filters_and_flags_carb_staples(store, personas):
    lev = personas["P5"]
    rice = store.variants_for("rice")[0]
    m = check_variant(rice, lev, store)
    assert not m.eligible and "special:keto" in m.failed
    paneer = store.variants_for("paneer")[0]
    assert check_variant(paneer, lev, store).eligible
    assert not check_dish(store.dish("D01"), lev, store).eligible  # dal chawal


def test_t016_vegan_gluten_free_low_gi_exact(store):
    for name, rule, forbidden in [
        ("Vegan", "special:vegan", lambda v: not v.vegan),
        ("Gluten-Free", "special:gluten_free", lambda v: not v.gluten_free),
        ("Intermittent Fasting / Low-GI", "special:low_gi", lambda v: v.gi_label not in {"low", "not_applicable"}),
    ]:
        lev = levers(specialized_diets=[name], business={"stock_filter": False})
        for v in store.variants:
            m = check_variant(v, lev, store)
            assert (rule in m.failed) == forbidden(v), (name, v.name)


def test_t017_stock_filter_on_and_off(store):
    milk = store.variants_for("milk")[0]
    empty = store.with_stock({s.sku_id: 0 for s in store.skus_for(milk.variant_id)})
    on = check_variant(milk, levers(), empty)
    off = check_variant(milk, levers(business={"stock_filter": False}), empty)
    assert not on.eligible and "stock" in on.failed
    assert off.eligible and "out_of_stock" in off.flags


def test_t018_price_cap_applies_to_add_ons_only(store):
    lev = levers(business={"price_cap_inr": 80})
    rec = store.dish("D53")  # gajar halwa: carrot, milk, sugar, ghee, cardamom
    as_dish = check_dish(rec, lev, store, kind="dish")
    as_addon = check_dish(rec, lev, store, kind="addon")
    assert as_dish.eligible and "price_cap" not in as_dish.failed
    assert as_addon.basket_cost_inr > 80 and not as_addon.eligible and "price_cap" in as_addon.failed
    # C18: ingredients already in the cart do not count towards the add-on's cost
    in_cart = check_dish(rec, lev, store, kind="addon", cart_terms={"milk", "ghee", "cardamom", "sugar"})
    assert in_cart.basket_cost_inr < as_addon.basket_cost_inr


def test_t019_hidden_animal_ingredient_excluded_via_ingredient_list(store, personas):
    v = store.variants_for("sugar")[0]
    tampered = v.model_copy(update={"ingredient_list": v.ingredient_list + ["gelatin"]})
    assert tampered.diet_class in {"vegan", "vegetarian"}  # tags still look vegetarian
    m = check_variant(tampered, personas["P2"], store)
    assert not m.eligible and "diet:pure_veg" in m.failed
    parmesan = next(x for x in store.variants if strip_qualifier(x.ingredient_list[0]) == "parmesan")
    assert not check_variant(parmesan, personas["P2"], store).eligible


def test_masks_intersect_for_contradictory_persona(store):
    lev = levers(diet="Non-Veg / Flexitarian", faith="Jain (Strict Root-Free)")
    onion = store.variants_for("onion")[0]
    chicken = store.variants_for("chicken")[0]
    assert not check_variant(onion, lev, store).eligible
    assert not check_variant(chicken, lev, store).eligible


def test_declared_allergen(store):
    cashew = store.variants_for("cashew")[0]
    m = check_variant(cashew, levers(), store, declared_allergens=("tree_nut",))
    assert not m.eligible and "allergen:tree_nut" in m.failed


def test_c68_jain_never_gets_fungi(store, personas):
    """C68: Grilled Vegetables (D111, mushroom) is not eligible for a Jain persona; it still is by default."""
    dish = store.dish("D111")
    jain = levers(diet=JAIN, faith="Jain (Strict Root-Free)")
    assert not check_dish(dish, jain, store).eligible
    assert check_dish(dish, levers(), store).eligible
