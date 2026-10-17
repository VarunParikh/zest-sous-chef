"""Raw score components for dish candidates (PRD Appendix A; C24, C26).

s_h: mean history slider over the dish's derived buckets (none -> 0.5).
s_t: trend multiplier from the context.
s_g: gourmet match between the slider and the dish's premium level, plus a gender
     cohort boost of 10% of the base (FR-07: never a filter).
s_p: from the caller's fused match rank (retrieval, block 1.4).
"""
from __future__ import annotations

from statistics import mean

from backend.catalogue.seed import DishRecord
from backend.catalogue.store import Store
from backend.engine.context import Context, load_trends, trend_multiplier
from backend.engine.eligibility import check_dish
from backend.engine.scoring import RawCandidate
from backend.session.levers import LeverSet

DAIRY = {"curd", "paneer", "milk", "buttermilk"}
BREADS = {"bread loaf", "bread rolls", "refined flour", "wheat flour", "millet"}
PROTEIN_TERMS = {"chicken", "mutton", "fish", "prawns", "egg", "paneer", "tofu", "soy chunks", "whey protein",
                 "chickpeas", "kidney beans", "toor dal", "moong dal", "urad dal", "chana dal", "masoor dal",
                 "cowpea", "horse gram", "moth beans"}
IRON_CALCIUM_TERMS = {"milk", "curd", "paneer", "buttermilk", "cheese", "khoya", "spinach", "amaranth", "mustard greens",
                      "fenugreek leaves", "millet", "dates", "almond", "cashew", "walnut", "pistachio", "sesame seeds",
                      "jaggery"}
BOOST = 0.10  # FR-07 cap: at most 10% of s_g


def _essential_terms(rec: DishRecord, store: Store) -> list[str]:
    return [store.lexicon.canonical(i.ingredient_name) or i.ingredient_name for i in rec.ingredients if i.essential]


def history_buckets(rec: DishRecord, store: Store) -> set[str]:
    d, terms = rec.dish, _essential_terms(rec, store)
    words = " ".join([d.name, *d.aliases]).lower()
    buckets = set()
    if d.course == "dessert":
        buckets.add("desserts")
    if DAIRY & set(terms[:2]):
        buckets.add("dairy")
    if d.course in {"side", "breakfast"} and terms and terms[0] in BREADS:
        buckets.add("bakery")
    if "salad" in words or (d.course == "beverage" and "healthy" in d.mood_tags):
        buckets.add("salads")
    if d.diet_class in {"non_veg", "egg"} or "high_protein" in d.mood_tags:
        buckets.add("kebabs")
    return buckets


_PREMIUM: dict[tuple[int, str], float] = {}


def premium_level(rec: DishRecord, store: Store) -> float:
    key = (id(store), rec.dish.dish_id)
    if key not in _PREMIUM:
        levels = [mean(v.gourmet_score for v in vs) for t in _essential_terms(rec, store) if (vs := store.variants_for(t))]
        _PREMIUM[key] = mean(levels) if levels else 0.5
    return _PREMIUM[key]


def cohort_match(gender: str, terms: set[str], high_protein: bool) -> bool:
    if gender == "Female":
        return bool(terms & IRON_CALCIUM_TERMS)
    if gender == "Male":
        return high_protein
    return False


def dish_candidate(
    rec: DishRecord, levers: LeverSet, ctx: Context, store: Store, match_rank: int,
    kind: str = "dish", cart_terms: frozenset[str] = frozenset(), declared_allergens: tuple[str, ...] = (),
) -> RawCandidate:
    mask = check_dish(rec, levers, store, kind=kind, cart_terms=cart_terms, declared_allergens=declared_allergens)
    hist = levers.history.model_dump()
    buckets = history_buckets(rec, store)
    h = mean(hist[b] for b in buckets) if buckets else 0.5
    t = trend_multiplier(rec, ctx, load_trends(), levers)
    g_base = 1 - abs(levers.gourmet_affinity - premium_level(rec, store))
    terms = set(_essential_terms(rec, store))
    boost = BOOST * g_base if cohort_match(levers.gender, terms, bool(terms & PROTEIN_TERMS) or "high_protein" in rec.dish.mood_tags) else 0.0
    return RawCandidate(rec.dish.dish_id, match_rank, h, t, g_base + boost, mask.eligible, mask.failed,
                        g_base=g_base, g_boost=boost, kind=kind)
