"""Model output schemas (Agent Design §5) plus business validators (§8)."""
from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

_IMPLAUSIBLE = re.compile(r"https?://|www\.|<|>|\{|\}")


UNITS = ("g", "kg", "ml", "l", "piece", "bunch", "tsp", "tbsp", "cup", "pinch")
UNIT_SPELLINGS = {
    "gram": "g", "grams": "g", "gm": "g", "gms": "g", "gr": "g", "kilogram": "kg", "kilograms": "kg", "kgs": "kg",
    "millilitre": "ml", "milliliter": "ml", "millilitres": "ml", "milliliters": "ml", "litre": "l", "liter": "l",
    "litres": "l", "liters": "l", "ltr": "l", "pieces": "piece", "pc": "piece", "pcs": "piece", "nos": "piece",
    "no": "piece", "bunches": "bunch", "teaspoon": "tsp", "teaspoons": "tsp", "tsps": "tsp", "tesp": "tsp",
    "tesps": "tsp", "tablespoon": "tbsp", "tablespoons": "tbsp", "tbsps": "tbsp", "tbs": "tbsp", "tbl": "tbsp",
    "cups": "cup", "pinches": "pinch",
}


class IngredientLine(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    qty: Optional[float] = Field(default=None, gt=0, le=10000)
    unit: Optional[Literal[UNITS]] = None  # type: ignore[valid-type]
    estimated: bool = False

    @model_validator(mode="before")
    @classmethod
    def _normalise_unit(cls, data):
        """Common spellings map to the allowed units; an unknown unit becomes no unit and the line an estimate.
        Found live in block 2.4: one "tesps" rejected a whole video recipe."""
        if isinstance(data, dict) and isinstance(data.get("unit"), str):
            raw = data["unit"].strip().lower().rstrip(".")
            unit = raw if raw in UNITS else UNIT_SPELLINGS.get(raw)
            data = {**data, "unit": unit}
            if unit is None and raw:
                data["estimated"] = True
        return data

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


Intent = Literal["youtube_recipe", "recipe_text", "named_dish", "mood_intent", "cart_edit",
                 "cart_clear_or_replace", "staples_answer", "variant_request", "question_cooking",
                 "declare_allergy", "smalltalk", "off_topic", "unsafe", "unsupported"]


class IntentResult(BaseModel):
    """A2 `intent_classify` output (Agent Design §5)."""
    intent: Intent
    confidence: float = Field(ge=0, le=1)
    mood_tags: list[str] = Field(default_factory=list, max_length=4)
    dish_name: Optional[str] = Field(default=None, max_length=80)
    servings: Optional[int] = Field(default=None, ge=1, le=12)


class ReasonResult(BaseModel):
    """A4 `reason_line` output (Agent Design §5); the business validator lives in `flows.mood`."""
    reason: str = Field(min_length=3, max_length=140)
