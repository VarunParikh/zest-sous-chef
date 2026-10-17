"""Catalogue and recipe models (Data Model §4, §5, §14). Values are mock and illustrative."""
from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

DietClass = Literal["vegan", "vegetarian", "egg", "non_veg"]
Course = Literal["main", "soup", "side", "snack", "breakfast", "dessert", "beverage"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Unit(str, Enum):
    g = "g"
    kg = "kg"
    ml = "ml"
    l = "l"  # noqa: E741
    piece = "piece"
    bunch = "bunch"


class Pack(Strict):
    qty: float = Field(gt=0)
    unit: Unit


class Nutrition(Strict):
    carbs_g: float = Field(ge=0)
    sugar_g: float = Field(ge=0)
    protein_g: float = Field(ge=0)
    fat_g: float = Field(ge=0)


class Variant(Strict):
    variant_id: str
    base_id: str
    name: str
    category: str
    history_bucket: Optional[Literal["bakery", "dairy", "desserts", "salads", "kebabs"]] = None
    attributes: dict[str, str]
    ingredient_list: list[str] = Field(min_length=1)
    brand: str
    price_per_unit_inr: float = Field(gt=0)
    gourmet_score: float = Field(ge=0, le=1)
    organic_score: float = Field(ge=0, le=1)
    diet_class: DietClass
    flags: list[str] = []
    allergens: list[str] = []
    halal_status: Literal["halal", "not_halal", "not_applicable"] = "not_applicable"
    gluten_free: bool
    vegan: bool
    jain_ok: bool
    satvik_ok: bool
    nutrition: Nutrition
    gi_label: Literal["low", "medium", "high", "not_applicable"]
    icon: str
    embedding_text: str


class Sku(Strict):
    sku_id: str
    variant_id: str
    pack: Pack
    price_inr: int = Field(gt=0)
    stock_count: int = Field(ge=0)
    dark_store_ok: bool = True


class RecipeIngredient(Strict):
    dish_id: str
    line_no: int
    ingredient_name: str
    qty: float = Field(gt=0)
    unit: Unit
    scale_class: Literal["staple", "vegetable", "spice", "salt", "oil", "garnish", "liquid"]
    essential: bool = True
    substitute_group: Optional[str] = None
    attribute_hint: Optional[dict[str, str]] = None


class Dish(Strict):
    dish_id: str
    name: str
    aliases: list[str] = []
    course: Course
    cuisine: str
    base_servings: int = 2
    mood_tags: list[str]
    flavour: list[str] = []
    description: str
    history_bucket: Optional[str] = None
    trend_group: Optional[Literal["indulgence", "cooling"]] = None
    diet_class: DietClass
    variant_of: Optional[str] = None
    edge_case: bool = False


class Pairing(Strict):
    dish_a: str
    dish_b: str
    strength: float = Field(ge=0, le=1)
    note: str = ""
