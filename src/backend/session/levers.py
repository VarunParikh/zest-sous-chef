"""Lever set (Data Model §8.1; Settings Panel; personas.json shape).

Option strings are the Settings Panel strings exactly, held in one constant.
Field nesting follows `mock-data/personas.json` (`business.price_cap_inr`).
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

LEVER_OPTIONS = {
    "gender": ("Female", "Male", "Unisex / Neutral"),
    "diet": ("Pure Veg (Strict)", "Jain (No Root Veggies / Pure Veg)", "Non-Veg / Flexitarian"),
    "faith": (
        "Hindu (Shravan Month / Fasting Active)",
        "Jain (Strict Root-Free)",
        "Muslim (Strict Halal Only)",
        "Hindu (Regular)",
        "None / Secular",
    ),
    "specialized_diets": (
        "Standard / Balanced",
        "Keto Diet",
        "Intermittent Fasting / Low-GI",
        "Vegan",
        "Gluten-Free",
        "High-Protein Fitness",
    ),
}


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Weights(Strict):
    culinary_pairing: float = Field(0.30, ge=0, le=1)
    purchase_history: float = Field(0.35, ge=0, le=1)
    market_trend: float = Field(0.20, ge=0, le=1)
    persona_gourmet: float = Field(0.15, ge=0, le=1)


class History(Strict):
    bakery: float = Field(0.85, ge=0, le=1)
    dairy: float = Field(0.70, ge=0, le=1)
    desserts: float = Field(0.65, ge=0, le=1)
    salads: float = Field(0.60, ge=0, le=1)
    kebabs: float = Field(0.75, ge=0, le=1)


class Trends(Strict):
    weekend_indulgence: float = Field(0.80, ge=0, le=1)
    cooling_drinks: float = Field(0.65, ge=0, le=1)


class Business(Strict):
    price_cap_inr: int = Field(200, ge=80, le=400)
    stock_filter: bool = True


class LeverSet(Strict):
    weights: Weights = Weights()
    gender: Literal[LEVER_OPTIONS["gender"]] = "Unisex / Neutral"  # type: ignore[valid-type]
    diet: Literal[LEVER_OPTIONS["diet"]] = "Non-Veg / Flexitarian"  # type: ignore[valid-type]
    faith: Literal[LEVER_OPTIONS["faith"]] = "None / Secular"  # type: ignore[valid-type]
    specialized_diets: list[str] = ["Standard / Balanced"]
    gourmet_affinity: float = Field(0.50, ge=0, le=1)
    artisanal_organic: float = Field(0.60, ge=0, le=1)
    history: History = History()
    trends: Trends = Trends()
    business: Business = Business()

    @field_validator("specialized_diets")
    @classmethod
    def _known_diets(cls, v: list[str]) -> list[str]:
        unknown = [d for d in v if d not in LEVER_OPTIONS["specialized_diets"]]
        if unknown or not v:
            raise ValueError(f"unknown or empty specialized_diets: {unknown}")
        return v


def merge_levers(defaults: dict, overrides: dict) -> dict:
    """Deep-merge a persona's partial levers over the defaults (one level of nesting)."""
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in defaults.items()}
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = {**out[k], **v}
        else:
            out[k] = v
    return out


def snapshot_hash(levers: LeverSet) -> str:
    """Short, stable hash of a lever set (API Spec §4.1). Specialised-diet order does not matter."""
    data = levers.model_dump(mode="json")
    data["specialized_diets"] = sorted(data["specialized_diets"])
    canon = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canon.encode()).hexdigest()[:12]


def persona_label(levers: LeverSet, presets: Mapping[str, LeverSet]) -> str:
    """The preset name when the levers equal a preset, else "Custom" (API Spec §10 item 3).

    When several presets are equal (P7 and P9 both use the defaults), the first in `personas.json` wins.
    """
    h = snapshot_hash(levers)
    return next((name for name, preset in presets.items() if snapshot_hash(preset) == h), "Custom")


# C30: item classes each diet allows, and the classes a faith or specialised diet forbids.
ALL_CLASSES = frozenset({"meat_fish", "egg", "root_veg", "onion_garlic"})
DIET_ALLOWS = {
    "Non-Veg / Flexitarian": ALL_CLASSES,
    "Pure Veg (Strict)": frozenset({"root_veg", "onion_garlic"}),
    "Jain (No Root Veggies / Pure Veg)": frozenset(),
}
FORBIDS = {
    "Jain (Strict Root-Free)": ALL_CLASSES,
    "Hindu (Shravan Month / Fasting Active)": frozenset({"meat_fish", "egg", "onion_garlic"}),
    "Vegan": frozenset({"meat_fish", "egg"}),
}


def persona_conflicts(levers: LeverSet) -> list[tuple[str, str]]:
    """Contradictory settings (FR-09, C30): the diet allows a class that the faith or a specialised diet forbids.

    Only a warning: the eligibility masks always intersect in code, so the stricter rule wins.
    """
    allowed = DIET_ALLOWS[levers.diet]
    others = [levers.faith, *levers.specialized_diets]
    return [(levers.diet, s) for s in others if allowed & FORBIDS.get(s, frozenset())]


# Persona cards (FR-121, AC-50; Zest 2.0): the summary is generated from the levers, never typed by hand.
SPECIAL_WORDS = {"Keto Diet": "keto", "Intermittent Fasting / Low-GI": "low-GI", "Vegan": "vegan",
                 "Gluten-Free": "gluten-free", "High-Protein Fitness": "high-protein"}
JAIN_SUMMARY = "Jain: no root vegetables, onion, garlic or mushrooms"  # Data Model §9 with C68 (fungi)


def persona_summary(levers: LeverSet) -> str:
    """One plain line for a persona card, for example "Vegan, gluten-free" or "No restrictions"."""
    special = [SPECIAL_WORDS[d] for d in LEVER_OPTIONS["specialized_diets"] if d in levers.specialized_diets and d in SPECIAL_WORDS]
    halal = levers.faith == "Muslim (Strict Halal Only)"
    parts: list[str] = []
    if levers.diet.startswith("Jain") or levers.faith.startswith("Jain"):
        parts.append(JAIN_SUMMARY)
    elif levers.diet == "Pure Veg (Strict)" and "vegan" not in special:
        parts.append("pure vegetarian")
    if halal:
        parts.append("halal only")
    if levers.faith.startswith("Hindu (Shravan"):
        parts.append("Shravan fasting")
    parts += special
    if levers.diet == "Non-Veg / Flexitarian" and special and not halal:
        parts.append("eats meat")
    if not parts:
        return "No restrictions"
    text = ", ".join(parts)
    return text[0].upper() + text[1:]


def persona_tag(name: str) -> str | None:
    """Reviewer and control personas are tagged so the cards list them last (FR-121)."""
    low = name.lower()
    return "Reviewer" if "(reviewer)" in low else "Control" if "(control)" in low else None
