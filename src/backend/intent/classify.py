"""A2 `intent_classify` (Agent Design §6.1; FR-11). Sees only the latest message, spotlighted as data (§4, §7)."""
from __future__ import annotations

from backend.llm import prompts
from backend.llm.client import OllamaClient
from backend.llm.schemas import IntentResult


def classify(client: OllamaClient, message: str) -> IntentResult:
    """Raises LLMInvalid after one retry, or LLMError when the model is unreachable."""
    system, user = prompts.render("intent_classify", message)
    return client.generate(system, user, IntentResult, call="intent")
