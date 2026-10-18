"""Templated copy (Conversation Design §6). Text here is the approved wording only."""
from __future__ import annotations

TEMPLATES = {
    "MSG-GREET": "Hey there! I'm Zest, your AI cooking assistant. Paste a YouTube recipe link, describe what's in "
                 "your fridge, or upload a photo of your ingredients to start!",
    "MSG-LEVER-BANNER": "Changes apply from your next chat session.",
    "MSG-WEIGHTS-DEFAULT": "All four weights were 0, so I'm using the default mix.",  # C30
    "MSG-PERSONA-WARN": "Your settings overlap: {a} and {b}. I'm applying both, so options may be limited.",
    "MSG-CHAT-CLEAR-CONFIRM": "Clearing the chat will also empty your cart. Continue?",
    "MSG-CLEAR-CONFIRM": "Replace the {dish} cart, or add to it?",
    "MSG-CLEAR-DONE": "Replaced. You can Undo if you change your mind.",
    "MSG-MOOD-SWAP": "Swapped to {dish}. Your earlier items are untouched.",
    "MSG-UNDO": "Done. Removed {dish}.",
    "MSG-EMPTY-CART": "Your cart is empty. Pick a recipe or paste a YouTube link to get started!",
    "MSG-ORDER": "Order is placed, the rider will see you in 10 mins",
    "MSG-BLOCKED-ORDER": "{item} is no longer available. Swap or remove it to place your order.",
    "MSG-PRICE-CHANGED": "A price changed since you added it. The updated total is shown.",
    "MSG-EDIT-OK": "Done. {change}. ✅",
    "MSG-REDIRECT": "I'm here to help with cooking and groceries. Tell me what you'd like to cook.",
    "MSG-HAZARD": "I can't help with that. If you'd like to cook something, I'm happy to help.",
    "MSG-INJECT-DATA": "That content contained instructions, so I ignored them.",
    "MSG-REPHRASE": "I didn't quite catch that. Could you rephrase it?",
    "MSG-THANKS": "Anytime. What shall we cook next?",
    "MSG-UNSUPPORTED": "I can't do that here. I can build your cart and you can place the order with Buy Now.",
    "MSG-ALLERGY": "I can't confirm that an item is safe for an allergy. Dietary labels here are simplified, so please check the product label.",
    "MSG-SERVER": "Your food will be ready but seems like our servers are struggling. We will be back shortly",
}

STARTER_CHIPS = ["YouTube link", "Upload photo", "Text recipe", "Feeling hungry"]


def render(template_id: str, **values: str) -> str:
    return TEMPLATES[template_id].format(**values)
