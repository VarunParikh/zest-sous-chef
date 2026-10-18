"""E6 lever sensitivity (Evaluation Plan §4 E6; §4.15 C47; Kendall 1938).

RDI for a group = mean over its applicable prompts of 1 − |top3_base ∩ top3_changed| / 3.
The changed setting is the end of the lever's range farthest from the default (C47).
Status per group: RDI = 0 on its applicable prompts is critical (an inert lever); RDI below
0.33 fails; fewer than 5 applicable prompts is INCONCLUSIVE (under-exercised).
"""
from __future__ import annotations

from itertools import combinations
from statistics import mean

from backend.session.levers import LeverSet

RDI_MIN = 0.33
MIN_APPLICABLE = 5

# group -> (dotted path in LeverSet, contrasting value)
CONTRASTS: dict[str, tuple[str, object]] = {
    "w_pairing": ("weights.culinary_pairing", 1.0),
    "w_history": ("weights.purchase_history", 1.0),
    "w_trend": ("weights.market_trend", 1.0),
    "w_gourmet": ("weights.persona_gourmet", 1.0),
    "gourmet": ("gourmet_affinity", 1.0),
    "organic": ("artisanal_organic", 0.0),
    "h_bakery": ("history.bakery", 0.0),
    "h_dairy": ("history.dairy", 0.0),
    "h_desserts": ("history.desserts", 0.0),
    "h_salads": ("history.salads", 0.0),
    "h_kebabs": ("history.kebabs", 0.0),
    "t_weekend": ("trends.weekend_indulgence", 0.0),
    "t_cooling": ("trends.cooling_drinks", 0.0),
    "diet": ("diet", "Pure Veg (Strict)"),
    "faith": ("faith", "Jain (Strict Root-Free)"),
    "specialised": ("specialized_diets", ["Vegan"]),
    "addon_cap": ("business.price_cap_inr", 80),
    "stock_filter": ("business.stock_filter", False),
}


def apply_contrast(levers: LeverSet, group: str) -> LeverSet:
    path, value = CONTRASTS[group]
    data = levers.model_dump(mode="json")
    node, keys = data, path.split(".")
    for k in keys[:-1]:
        node = node[k]
    node[keys[-1]] = value
    return LeverSet.model_validate(data)


def divergence(base: list[str], changed: list[str]) -> float:
    return 1 - len(set(base[:3]) & set(changed[:3])) / 3


def kendall_distance(a: list[str], b: list[str]) -> float | None:
    """Normalised Kendall tau distance over the items both rankings contain (None if fewer than 2)."""
    common = [x for x in a if x in set(b)]
    if len(common) < 2:
        return None
    pos = {x: i for i, x in enumerate(b)}
    pairs = list(combinations(common, 2))
    return sum(pos[x] > pos[y] for x, y in pairs) / len(pairs)


def random_rdi(n: int, k: int = 3) -> float:
    """Expected RDI of a random re-ranker against a fixed top k from an n-item eligible pool: 1 − k/n."""
    k = min(k, n)
    if n <= k:
        return 0.0
    return 1 - k / n


def group_status(values: list[float]) -> tuple[str, bool]:
    """(status, critical) from the per-prompt divergences of one group's applicable prompts."""
    if not values:
        return "INCONCLUSIVE", False
    rdi = mean(values)
    if rdi == 0:
        return "FAIL", True
    if len(values) < MIN_APPLICABLE:
        return "INCONCLUSIVE", False
    return ("PASS" if rdi >= RDI_MIN else "FAIL"), False
