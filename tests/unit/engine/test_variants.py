"""Variant choice (FR-113, ADR-008; US-38; T-035, T-036)."""
from datetime import datetime

from backend.engine.context import build_context
from backend.engine.variants import choose_variant
from tests.unit.engine.conftest import levers

CTX = build_context(datetime(2026, 10, 17, 19, 0))


def test_resolution_prefers_plain_products(store):
    names = {v.name for v in store.variants_for("milk")}
    assert names and not any(w in n.lower() for n in names for w in ("kulfi", "ice cream", "condensed", "powder", "flavoured"))
    assert len(store.variants_for("milk")) >= 4


def test_t035_organic_slider_changes_choice(store):
    lo = choose_variant("milk", levers(artisanal_organic=0.0), CTX, store)
    hi = choose_variant("milk", levers(artisanal_organic=1.0), CTX, store)
    assert lo.chosen.variant_id != hi.chosen.variant_id
    assert hi.chosen.organic_score > lo.chosen.organic_score


def test_t035_gourmet_slider_changes_choice_via_value_term(store):
    lo = choose_variant("milk", levers(gourmet_affinity=0.0), CTX, store)
    hi = choose_variant("milk", levers(gourmet_affinity=1.0), CTX, store)
    assert lo.chosen.variant_id != hi.chosen.variant_id
    assert lo.chosen.price_per_unit_inr < hi.chosen.price_per_unit_inr
    assert lo.beta == 0.30 and hi.beta == 0.0


def test_t036_named_attribute_restricts_eligible_set(store):
    for g in (0.0, 0.5, 1.0):
        for o in (0.0, 1.0):
            c = choose_variant("milk", levers(gourmet_affinity=g, artisanal_organic=o), CTX, store, required=("skimmed",))
            assert c.chosen and all("skimmed" in v.ingredient_list[0] for v, _ in c.scored)


def test_variant_choice_respects_persona(store, personas):
    c = choose_variant("milk", personas["P6"], CTX, store)  # vegan persona: no dairy milk
    assert c.chosen is None and c.excluded


def test_choice_carries_reason_and_alternatives(store):
    c = choose_variant("milk", levers(), CTX, store)
    assert c.reason and c.alternatives and c.chosen not in c.alternatives
