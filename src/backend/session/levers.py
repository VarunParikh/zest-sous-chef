"""Lever set (Data Model §8.1; Settings Panel; personas.json shape).

Option strings are the Settings Panel strings exactly, held in one constant.
Field nesting follows `mock-data/personas.json` (`business.price_cap_inr`).
"""
from __future__ import annotations

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
