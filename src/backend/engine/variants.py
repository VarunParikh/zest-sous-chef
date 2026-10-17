"""Variant choice: S_v = M_elig × [(1 − β) Σ ŵ_k s_k + β v] (FR-113; ADR-008; PRD Appendix A).

v = 1 − min-max-normalised price per unit among the eligible variants of the ingredient,
β = β0 × (1 − gourmet_affinity) with β0 = VALUE_WEIGHT. A named attribute ("skimmed")
restricts the eligible set (FR-113, AC-39). Remaining ties go to the lowest price, then ID.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.catalogue.models import Variant
from backend.catalogue.store import Store
from backend.config import load_settings
from backend.engine.context import Context
from backend.engine.eligibility import check_variant
from backend.engine.features import BOOST, IRON_CALCIUM_TERMS
from backend.engine.scoring import KEYS, effective_weights, minmax, rank_normalise
from backend.session.levers import LeverSet


@dataclass
class VariantChoice:
    term: str
    chosen: Variant | None
    scored: list[tuple[Variant, float]] = field(default_factory=list)  # eligible, best first
    breakdowns: dict[str, dict] = field(default_factory=dict)
    excluded: list[tuple[Variant, tuple[str, ...]]] = field(default_factory=list)
    beta: float = 0.0
    reason: str = ""

    @property
    def alternatives(self) -> list[Variant]:
        return [v for v, _ in self.scored[1:]]


def _matches(v: Variant, required: tuple[str, ...]) -> bool:
    text = f"{v.ingredient_list[0]} {v.attributes.get('variant', '')}".lower()
    return all(word.lower() in text for word in required)


def choose_variant(
    item: str, levers: LeverSet, ctx: Context, store: Store, required: tuple[str, ...] = (),
    match_ranks: dict[str, int] | None = None, declared_allergens: tuple[str, ...] = (), value_weight: float | None = None,
) -> VariantChoice:
    beta0 = load_settings().value_weight if value_weight is None else value_weight
    beta = round(beta0 * (1 - levers.gourmet_affinity), 10)
    term = store.lexicon.canonical(item) or item
    eligible, excluded = [], []
    for v in store.variants_for(item):
        if required and not _matches(v, required):
            continue
        m = check_variant(v, levers, store, declared_allergens)
        (eligible.append(v) if m.eligible else excluded.append((v, m.failed)))
    if not eligible:
        return VariantChoice(term, None, excluded=excluded, beta=beta, reason="No eligible variant for your settings")
    w, _ = effective_weights(levers.weights)
    hist = levers.history.model_dump()
    ranks = [(match_ranks or {}).get(v.variant_id, 1) for v in eligible]

    def g_raw(v: Variant) -> float:
        base = 0.5 * (1 - abs(levers.gourmet_affinity - v.gourmet_score)) + 0.5 * (1 - abs(levers.artisanal_organic - v.organic_score))
        cohort = (levers.gender == "Female" and store.lexicon.canonical(v.ingredient_list[0]) in IRON_CALCIUM_TERMS) or \
                 (levers.gender == "Male" and v.nutrition.protein_g >= 10)
        return base * (1 + BOOST) if cohort else base

    comps = {
        "s_p": rank_normalise(ranks),
        "s_h": minmax([hist.get(v.history_bucket, 0.5) if v.history_bucket else 0.5 for v in eligible]),
        "s_t": [0.5] * len(eligible),  # no category-level trend rows in the seed (C23)
        "s_g": minmax([g_raw(v) for v in eligible]),
    }
    value = [1 - x for x in minmax([v.price_per_unit_inr for v in eligible])]
    scored, breakdowns = [], {}
    for i, v in enumerate(eligible):
        s = {k: comps[k][i] for k in KEYS}
        lever_part = sum(w[k] * s[k] for k in KEYS)
        total = (1 - beta) * lever_part + beta * value[i]
        scored.append((v, total))
        breakdowns[v.variant_id] = {**s, "value_term": value[i], "beta": beta, "final": total}
    scored.sort(key=lambda x: (-round(x[1], 12), x[0].price_per_unit_inr, x[0].variant_id))
    chosen = scored[0][0]
    cheapest = min(eligible, key=lambda v: v.price_per_unit_inr)
    reason = ("Lowest price per unit among eligible options" if chosen is cheapest
              else "Best match for your gourmet and organic settings")
    return VariantChoice(term, chosen, scored, breakdowns, excluded, beta, reason)
