"""E7 independent persona checker (Evaluation Plan §4 E7; Data Model §9; FR-60, FR-90, FR-91, FR-116).

Separate from `backend.engine.eligibility` on purpose (this module never imports it): it
reads the raw generated catalogue and re-applies the Data Model §9 rules. Each variant's
classes come from its stored tags AND from keywords in its name and ingredient list; the
stricter result wins, so a mis-tagged variant is still caught (as in T-019). Simplified
rules for a demonstration, not medical or religious advice.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from backend.config import REPO_ROOT

VARIANTS = REPO_ROOT / "mock-data" / "generated" / "variants.json"

KEYWORDS = {  # lexicon-flagged terms (mock-data/ingredient_lexicon.csv) plus common synonyms
    "meat": r"chicken|mutton|lamb|beef|pork|bacon|\bham\b|lard|sausage|salami|pepperoni|gelatin",
    "fish": r"\bfish\b|prawns?|shrimps?|crab|lobster|tuna|salmon|anchov|sardine|mackerel",
    "egg": r"\beggs?\b|\begg\b",
    "dairy": r"\bmilk\b|butter|buttermilk|cheese|\bcream\b|\bcurd\b|yogh?urt|\bghee\b|khoya|paneer|parmesan|whey|condensed",
    "honey": r"\bhoney\b",
    "alcohol": r"\bwine\b|\bbeer\b|\brum\b|vodka|whisk(e)?y|brandy|liqueur|\bsake\b|mirin",
    "root_veg": r"potato|carrot|beetroot|radish|ginger|\byam\b|colocasia|arbi|turnip",
    "onion_garlic": r"onion|garlic|shallot|\bleek",
    "gluten": r"wheat|refined flour|maida|semolina|sooji|\brava\b|barley|\brye\b",
    "pork": r"pork|bacon|\bham\b|lard|gelatin",
}
EXEMPT = {  # plant or unrelated products that contain a keyword (calibrated on the catalogue before any E7 run)
    "dairy": r"coconut milk|soy milk|almond milk|oat milk|rice milk|cashew milk|plant milk|peanut butter|cocoa butter|"
             r"nut butter|plant butter|vegan|plant[- ]based cream, cream|oat cream|soy cream|plant[- ]based( cream)?|dairy[- ]free( ice cream)?|cream of tartar|coconut cream",
    "egg": r"eggplant|eggless|egg-free",
    "honey": r"honeydew",
    "gluten": r"buckwheat|gluten[- ]free|idli rava",
    "root_veg": r"potato masala",
    "onion_garlic": r"no onion no garlic",
    "meat": r"\bveg(an|etarian)?\b|soy|plant[- ]based|mock|agar",
    "pork": r"agar|vegan|chicken sausages and bacon",
}
KETO_CATEGORIES = {"grains", "pulses", "bakery", "sweeteners", "breakfast", "snacks", "ready", "frozen"}  # C25


def _hits(text: str, cls: str) -> bool:
    if not re.search(KEYWORDS[cls], text):
        return False
    exempt = EXEMPT.get(cls)
    if exempt and re.search(exempt, text):
        stripped = re.sub(exempt, " ", text)
        return bool(re.search(KEYWORDS[cls], stripped))
    return True


@dataclass(frozen=True)
class Classes:
    has: frozenset[str]


def classes(v: dict) -> frozenset[str]:
    """Stored tags OR keywords: the union is the stricter reading."""
    text = " ".join([v["name"], *v["ingredient_list"]]).lower()
    out = set(v.get("flags", []))
    out |= {c for c in KEYWORDS if _hits(text, c)}
    if v.get("diet_class") == "non_veg":
        out.add("meat")
    if v.get("diet_class") == "egg":
        out.add("egg")
    if v.get("halal_status") == "not_halal":
        out.add("not_halal")
    if not v.get("vegan", False):
        out.add("not_vegan")
    if not v.get("jain_ok", False):
        out.add("not_jain")
    if not v.get("satvik_ok", False):
        out.add("not_satvik")
    if not v.get("gluten_free", False):
        out.add("gluten")
    return frozenset(out)


def violations(v: dict, levers: dict) -> list[str]:
    """Rules from Data Model §9 that this variant breaks for these levers (empty: compliant)."""
    c, out = classes(v), []
    veg_bad = c & {"meat", "fish", "egg"}
    diet, faith = levers["diet"], levers["faith"]
    special = set(levers.get("specialized_diets", []))
    if diet == "Pure Veg (Strict)" and veg_bad:
        out.append("pure_veg:" + "+".join(sorted(veg_bad)))
    if diet.startswith("Jain") or faith.startswith("Jain"):
        bad = veg_bad | (c & {"root_veg", "onion_garlic", "not_jain"})
        if bad:
            out.append("jain:" + "+".join(sorted(bad)))
    if faith.startswith("Hindu (Shravan"):
        bad = veg_bad | (c & {"onion_garlic", "non_satvik", "not_satvik"})
        if bad:
            out.append("shravan:" + "+".join(sorted(bad)))
    if faith == "Muslim (Strict Halal Only)":
        bad = c & {"not_halal", "alcohol", "pork"}
        if bad:
            out.append("halal:" + "+".join(sorted(bad)))
    if "Vegan" in special:
        bad = c & {"meat", "fish", "egg", "dairy", "honey", "not_vegan"}
        if bad:
            out.append("vegan:" + "+".join(sorted(bad)))
    if "Gluten-Free" in special and "gluten" in c:
        out.append("gluten_free")
    if "Keto Diet" in special and v.get("category") in KETO_CATEGORIES and v["nutrition"]["carbs_g"] > 10:
        out.append("keto")
    if "Intermittent Fasting / Low-GI" in special and v.get("gi_label") not in {"low", "not_applicable"}:
        out.append("low_gi")
    return out


def load_variants(path: Path = VARIANTS) -> dict[str, dict]:
    return {v["variant_id"]: v for v in json.loads(path.read_text())}
