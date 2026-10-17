"""Contradictory persona settings and the gender boost (US-04; FR-07, FR-09; AC-25; C30; T-006)."""
from datetime import datetime

import pytest

from backend.catalogue.store import load_store
from backend.engine.context import build_context
from backend.engine.eligibility import check_variant
from backend.engine.features import dish_candidate
from backend.flows.templates import render
from backend.session.levers import LeverSet, persona_conflicts
from tests.acceptance.test_sessions import _app

NON_VEG, PURE_VEG, JAIN_DIET = "Non-Veg / Flexitarian", "Pure Veg (Strict)", "Jain (No Root Veggies / Pure Veg)"
JAIN, SHRAVAN, HALAL = "Jain (Strict Root-Free)", "Hindu (Shravan Month / Fasting Active)", "Muslim (Strict Halal Only)"


@pytest.fixture(scope="module")
def store():
    return load_store()


@pytest.mark.parametrize("lev, expected", [
    (LeverSet(diet=NON_VEG, faith=JAIN), [(NON_VEG, JAIN)]),
    (LeverSet(diet=NON_VEG, faith=SHRAVAN), [(NON_VEG, SHRAVAN)]),
    (LeverSet(diet=NON_VEG, specialized_diets=["Vegan"]), [(NON_VEG, "Vegan")]),
    (LeverSet(diet=NON_VEG, faith=JAIN, specialized_diets=["Vegan"]), [(NON_VEG, JAIN), (NON_VEG, "Vegan")]),
    (LeverSet(diet=PURE_VEG, faith=JAIN), [(PURE_VEG, JAIN)]),  # Pure Veg allows root veg; Jain forbids it
    (LeverSet(diet=PURE_VEG, faith=SHRAVAN), [(PURE_VEG, SHRAVAN)]),  # onion and garlic
    # Only stricter in the same direction, or unrelated: no warning.
    (LeverSet(diet=PURE_VEG, specialized_diets=["Vegan"]), []),
    (LeverSet(diet=JAIN_DIET, faith=JAIN), []),
    (LeverSet(diet=JAIN_DIET, faith=SHRAVAN, specialized_diets=["Vegan"]), []),
    (LeverSet(diet=NON_VEG, faith=HALAL), []),
    (LeverSet(diet=NON_VEG, specialized_diets=["Keto Diet", "Gluten-Free", "High-Protein Fitness"]), []),
    (LeverSet(), []),
])
def test_conflict_rule(lev, expected):
    assert persona_conflicts(lev) == expected


def test_t006_jain_faith_with_non_veg_warns_and_masks_intersect(tmp_path, store):
    _, client = _app(tmp_path)
    turn = client.post("/api/v1/sessions", json={"levers": {"diet": NON_VEG, "faith": JAIN}}).json()["turn"]
    assert turn["notices"] == [{"type": "notice", "level": "warning", "template_id": "MSG-PERSONA-WARN",
                                "text": render("MSG-PERSONA-WARN", a=NON_VEG, b=JAIN)}]
    lev = LeverSet(diet=NON_VEG, faith=JAIN)
    chicken = check_variant(store.variants_for("chicken")[0], lev, store)
    onion = check_variant(store.variants_for("onion")[0], lev, store)
    assert not chicken.eligible and "faith:jain" in chicken.failed
    assert not onion.eligible and "faith:jain" in onion.failed


def test_no_warning_without_a_conflict(tmp_path):
    _, client = _app(tmp_path)
    turn = client.post("/api/v1/sessions", json={"levers": {"diet": JAIN_DIET, "faith": JAIN}}).json()["turn"]
    assert turn["notices"] == []


def test_gender_not_set_gives_no_cohort_boost(store):
    ctx = build_context(datetime(2026, 10, 17, 19, 0))
    assert all(dish_candidate(rec, LeverSet(), ctx, store, 1).g_boost == 0 for rec in store.dishes)
