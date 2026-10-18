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
    "MSG-MOOD-ADD": "Feeling {mood}? Let's go with {dish}: {reason}. I've added the ingredients. ✅",
    "MSG-MOOD-NONE": "I couldn't find a dish that fits your {constraint} settings for that mood. Try another mood, or tell me what you'd like to cook.",
    "MSG-TXT-DRAFT": "Got it. Adding {n} ingredients for {dish}. Say 'new dish' when you start another. ✅",
    "MSG-TXT-STORED": "I'll use my standard {dish} recipe for {servings}. Tell me if you cook it differently.",
    "MSG-TXT-UNKNOWN": "I don't have a recipe for {dish} yet. Tell me its ingredients, or choose something close:",
    "MSG-AMBIG": "Did you mean {option_a} or {option_b}?",
    "MSG-EDIT-UNCLEAR": "Which item do you mean? {options}",
    "MSG-PERSONA-BLOCK": "{item} isn't available with your {setting} setting. How about {alternative}?",
    "MSG-YT-OK": "Lovely choice. That's {dish}. I've added {n} ingredients to your cart. ✅",
    "MSG-YT-FIXTURE": "I couldn't reach the video live, so I used my saved copy of this recipe.",
    "MSG-YT-TITLE": "I couldn't get the full recipe, so I worked from the video's title and description. Quantities are estimates.",
    "MSG-YT-PASTE": "I can't read that video right now. Could you paste the recipe or its ingredients here?",
    "MSG-YT-BAD-URL": "That doesn't look like a YouTube link. Paste a youtube.com or youtu.be link, or type the recipe.",
    "MSG-YT-NONFOOD": "That video doesn't look like a recipe. Share a cooking video, or tell me what you'd like to cook.",
    "MSG-YT-DUP": "You've already added {dish}. Add it again?",
    "MSG-PANTRY": "Both dishes use {staples}. Already have them at home?",
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
