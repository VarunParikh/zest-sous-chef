"""E12 gate logic (Evaluation Plan §4 E12; ADR-008), written before any E12 run."""
from backend.evaluation.variant_sweep import IngredientSweep, e12_gate


def sweep(name, organic=("a", "b"), gourmet=("a", "c"), price=("a", "d"), organic_at_max_beta=True, has_organic=True,
          cheapest_at_g0=True, premium_at_g1=True):
    return IngredientSweep(name, organic, gourmet, price, organic_at_max_beta, has_organic, cheapest_at_g0, premium_at_g1)


def test_effect_visible_on_four_of_six_passes():
    rows = [sweep(f"i{k}") for k in range(4)] + [sweep(f"j{k}", organic=("a", "a"), gourmet=("a", "a"), price=("a", "a"))
                                                for k in range(2)]
    g = e12_gate(rows)
    assert g["organic"]["k"] == 4 and g["gourmet"]["k"] == 4 and g["price"]["k"] == 4
    assert g["status"] == "PASS" and not g["price_overrides_organic"]


def test_three_of_six_fails():
    rows = [sweep(f"i{k}") for k in range(3)] + [sweep(f"j{k}", organic=("a", "a")) for k in range(3)]
    assert e12_gate(rows)["status"] == "FAIL"


def test_price_overriding_organic_everywhere_rejects():
    rows = [sweep(f"i{k}", organic_at_max_beta=False) for k in range(5)] + [sweep("x", has_organic=False)]
    g = e12_gate(rows)
    assert g["price_overrides_organic"] and g["status"] == "FAIL"
