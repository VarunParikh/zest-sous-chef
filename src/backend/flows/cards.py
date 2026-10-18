"""Messages, typed cards and the turn response (API Spec §4.4 to §4.6).

`/chat` and `/action` return the same `TurnResponse`; cards are a discriminated
union on `type`, so the frontend renders one structure.
"""
from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class _Card(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ChoiceOption(_Card):
    value: str
    label: str


class SwapOption(_Card):
    dish_id: str
    name: str


class AddonItem(_Card):
    name: str
    variant: Optional[str] = None
    price_inr: int


class SamplePhoto(_Card):
    id: str
    caption: str
    label: Literal["Sample"] = "Sample"


class StarterChips(_Card):
    type: Literal["starter_chips"] = "starter_chips"
    chips: list[str]


class DishAdded(_Card):
    type: Literal["dish_added"] = "dish_added"
    suggestion_id: str
    dish_id: str
    dish_name: str
    reason: str
    line_count: int
    dish_total_inr: int


class SwapOptions(_Card):
    type: Literal["swap_options"] = "swap_options"
    suggestion_id: str
    options: list[SwapOption] = Field(max_length=2)


class Undo(_Card):
    type: Literal["undo"] = "undo"
    suggestion_id: str


class WhyThis(_Card):
    type: Literal["why_this"] = "why_this"
    suggestion_id: str
    breakdown: Optional[dict] = None  # embedded when small, else fetched from the inspector


class Clarify(_Card):
    type: Literal["clarify"] = "clarify"
    question_id: str
    prompt: str
    options: list[ChoiceOption]


class Confirm(_Card):
    type: Literal["confirm"] = "confirm"
    confirm_id: str
    prompt: str
    options: list[ChoiceOption]


class AddonSuggestion(_Card):
    type: Literal["addon_suggestion"] = "addon_suggestion"
    suggestion_id: str
    item: AddonItem
    reason: str


class Substitution(_Card):
    type: Literal["substitution"] = "substitution"
    substitution_id: str
    from_item: str
    to_item: str
    price_delta_inr: int
    flavour_note: str


class PhotoConsent(_Card):
    type: Literal["photo_consent"] = "photo_consent"
    notice: str


class SamplePhotos(_Card):
    type: Literal["sample_photos"] = "sample_photos"
    photos: list[SamplePhoto]


class Notice(_Card):
    type: Literal["notice"] = "notice"
    level: Literal["info", "warning"]
    template_id: str
    text: str


class CartSummary(_Card):
    type: Literal["cart_summary"] = "cart_summary"
    item_count: int
    subtotal_inr: int


Card = Annotated[
    Union[StarterChips, DishAdded, SwapOptions, Undo, WhyThis, Clarify, Confirm, AddonSuggestion,
          Substitution, PhotoConsent, SamplePhotos, Notice, CartSummary],
    Field(discriminator="type"),
]


class Message(BaseModel):
    message_id: str
    role: Literal["user", "assistant", "system"]
    template_id: Optional[str] = None
    text: str
    cards: list[Card] = []


class PackView(BaseModel):
    sku_id: str
    count: int
    pack: str


class CartLineView(BaseModel):
    line_id: str
    ingredient_name: str
    variant_id: str
    variant_name: str
    packs: list[PackView] = []
    price_inr: int
    priced: bool = True
    shared_from_line_id: Optional[str] = None
    estimated: bool = False
    reason: str = ""
    alternative_variant_ids: list[str] = []
    in_stock: bool = True  # API Spec v0.4, C34
    quantity: int = 1  # C35


class CartDishView(BaseModel):
    cart_dish_id: str
    dish_id: Optional[str] = None
    name: str
    dish_total_inr: int
    lines: list[CartLineView] = []


class CartView(BaseModel):
    """The full cart snapshot sent with every turn (API Spec §4.6). Prices come from the catalogue only."""
    dishes: list[CartDishView] = []
    item_count: int = 0
    subtotal_inr: int = 0


class SuggestionRef(BaseModel):
    suggestion_id: str
    type: Literal["dish", "addon", "substitute", "variant"]
    candidate_id: str
    rank: int


class TurnResponse(BaseModel):
    turn_id: str
    messages: list[Message]
    cart: CartView = CartView()
    cart_changed: bool = False
    pending: Optional[dict] = None
    suggestions: list[SuggestionRef] = []
    notices: list[Notice] = []
    fallbacks_used: list[str] = []
    levers_changed_since_snapshot: bool = False  # v0.3, C31: shows MSG-LEVER-BANNER (FR-03)
