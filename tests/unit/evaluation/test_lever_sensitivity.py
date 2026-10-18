"""E6 maths and rules (Evaluation Plan §4 E6, §4.15 C47), written before any E6 run."""
import pytest

from backend.evaluation.lever_sensitivity import (CONTRASTS, MIN_APPLICABLE, RDI_MIN, apply_contrast, divergence,
                                                   group_status, kendall_distance, random_rdi)
from backend.session.levers import LeverSet


def test_divergence_per_prompt():
    assert divergence(["a", "b", "c"], ["a", "b", "c"]) == 0
    assert divergence(["a", "b", "c"], ["a", "x", "y"]) == pytest.approx(2 / 3)
    assert divergence(["a", "b", "c"], []) == 1  # nothing shown after the change
    assert divergence(["a", "b", "c"], ["c", "b", "a"]) == 0  # order inside the top 3 does not count


def test_kendall_distance_on_common_items():
    assert kendall_distance(["a", "b", "c", "d"], ["a", "b", "c", "d"]) == 0
    assert kendall_distance(["a", "b", "c", "d"], ["d", "c", "b", "a"]) == 1
    assert kendall_distance(["a", "b", "c"], ["b", "a", "c", "z"]) == pytest.approx(1 / 3)
    assert kendall_distance(["a"], ["a"]) is None


def test_random_reranker_expected_rdi():
    assert random_rdi(15) == pytest.approx(0.8)
    assert random_rdi(3) == 0
    assert random_rdi(2) == 0


def test_contrasts_are_the_far_end_from_the_default_c47():
    assert len(CONTRASTS) == 18
    d = LeverSet()
    assert apply_contrast(d, "w_pairing").weights.culinary_pairing == 1.0
    assert apply_contrast(d, "h_bakery").history.bakery == 0.0
    assert apply_contrast(d, "t_cooling").trends.cooling_drinks == 0.0
    assert apply_contrast(d, "organic").artisanal_organic == 0.0
    assert apply_contrast(d, "gourmet").gourmet_affinity == 1.0
    assert apply_contrast(d, "addon_cap").business.price_cap_inr == 80
    assert apply_contrast(d, "stock_filter").business.stock_filter is False
    assert apply_contrast(d, "diet").diet == "Pure Veg (Strict)"
    assert apply_contrast(d, "faith").faith == "Jain (Strict Root-Free)"
    assert apply_contrast(d, "specialised").specialized_diets == ["Vegan"]
    assert apply_contrast(d, "w_trend").weights.purchase_history == d.weights.purchase_history  # everything else equal


def test_group_status_rules():
    assert RDI_MIN == 0.33 and MIN_APPLICABLE == 5
    assert group_status([0.4, 0.6, 0.2, 0.5, 0.3]) == ("PASS", False)
    assert group_status([0.0, 0.3, 0.2, 0.3, 0.3]) == ("FAIL", False)
    assert group_status([0.0] * 6) == ("FAIL", True)  # inert lever: critical
    assert group_status([0.6, 0.6]) == ("INCONCLUSIVE", False)  # under-exercised
    assert group_status([0.0, 0.0]) == ("FAIL", True)  # applicable somewhere and inert: still critical
    assert group_status([]) == ("INCONCLUSIVE", False)
