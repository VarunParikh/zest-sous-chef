"""Cart entities (Data Model §8.4, §14). Models only; allocation and pricing come in block 2.2."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from backend.catalogue.models import Unit


class PackItem(BaseModel):
    sku_id: str
    count: int = Field(ge=1, le=9)


class CartLine(BaseModel):
    line_id: str
    cart_dish_id: str
    ingredient_name: str
    need_qty: float
    need_unit: Unit
    estimated: bool = False
    variant_id: str
    packs: list[PackItem] = []
    priced: bool = True
    shared_from_line_id: Optional[str] = None
    reason: str = ""
    alternative_variant_ids: list[str] = []


class CartDish(BaseModel):
    cart_dish_id: str
    dish_id: Optional[str] = None
    name: str  # the dish name, or the free-text name when there is no dish_id
    source: Literal["youtube", "text", "mood", "photo"]
    servings: int = Field(2, ge=1)
    lines: list[CartLine] = []
    added_by_suggestion_id: Optional[str] = None


class Cart(BaseModel):
    dishes: list[CartDish] = []

    @property
    def is_empty(self) -> bool:
        return not self.dishes
