"""Model output schemas (Agent Design §5) plus business validators (§8)."""
from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

_IMPLAUSIBLE = re.compile(r"https?://|www\.|<|>|\{|\}")


class IngredientLine(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    qty: Optional[float] = Field(default=None, gt=0, le=10000)
    unit: Optional[Literal["g", "kg", "ml", "l", "piece", "bunch", "tsp", "tbsp", "cup", "pinch"]] = None
    estimated: bool = False

    @field_validator("name")
    @classmethod
    def _plausible(cls, v: str) -> str:
        if _IMPLAUSIBLE.search(v) or len(v.split()) > 6:
            raise ValueError("ingredient name is not a plausible name (no URLs, markup or sentences)")
        return v.strip()


class ExtractionResult(BaseModel):
    dish_name: Optional[str] = Field(default=None, max_length=80)
    servings: Optional[int] = Field(default=None, ge=1, le=12)
    ingredients: list[IngredientLine] = Field(max_length=40)


class GuardResult(BaseModel):
    label: Literal["ok", "off_topic", "injection", "hazard"]
    confidence: float = Field(ge=0, le=1)


class DetectedItem(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    confidence: float = Field(ge=0, le=1)

    @field_validator("name")
    @classmethod
    def _plausible(cls, v: str) -> str:
        if _IMPLAUSIBLE.search(v) or len(v.split()) > 6:
            raise ValueError("item name is not a plausible name")
        return v.strip()


class DetectionResult(BaseModel):
    items: list[DetectedItem] = Field(max_length=40)
    scene_is_food: bool
    quality: Literal["ok", "dark", "blurry"]
