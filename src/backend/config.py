"""Runtime configuration (architecture §6, NFR-07).

Every model name, threshold and timeout is configuration. Values come from the
process environment, then the local git-ignored `.env`, then the defaults below.
The Gemini key is a SecretStr so it never appears in a repr, log or response.
"""
from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Literal

from dotenv import dotenv_values
from pydantic import BaseModel, SecretStr, field_validator

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseModel):
    # Models (ADR-002, ADR-003 v2, ADR-005)
    llm_provider: Literal["ollama"] = "ollama"
    llm_model: str = "llama3.2:3b"  # ADR-002, chosen by the Day-1 benchmark E1 (2026-10-18)
    llm_num_ctx: int = 4096  # context window; 4k keeps the model's memory down (E1 post-hoc, 2026-10-18)
    ollama_base_url: str = "http://127.0.0.1:11434"
    # Input guard (ADR-006): rules first, then this classifier on text the rules pass
    guard_classifier: bool = True
    guard_model: str = "llama-guard3:1b"
    guard_ignore_categories: list[str] = ["S8", "S6"]  # ADR-006 v3 (C40, C44): classifier categories that do not block
    # Intent (Agent Design §6.1): below this confidence the bot asks to rephrase, never acts
    intent_confidence_min: float = 0.5
    vision_provider: Literal["ollama", "gemini", "samples"] = "ollama"  # ADR-003 v3 (owner decision, C37)
    vision_model: str = "qwen3-vl:4b-instruct"  # failed E3; photo accuracy NOT MET
    vision_num_ctx: int = 4096  # set before the first official E3 run: at 16k Ollama evicted the text model
    gemini_api_key: SecretStr = SecretStr("")
    embedding_provider: str = "chroma_default"
    embedding_model: str = ""  # empty means Chroma's default ONNX embedder
    # Retrieval and add-ons (ADR-004 v2); lexical-only is the ADR-004 rollback
    retrieval_mode: Literal["hybrid", "lexical"] = "hybrid"
    rrf_k: int = 60
    dish_pool: int = 25  # ADR-004 v4 (C53)
    variant_pool: int = 10
    ambiguity_margin: float = 0.15
    addon_courses: list[str] = ["side", "beverage", "dessert"]
    addon_weights: dict[str, float] = {"curated": 2.0, "vector": 1.0}
    addon_pool: int = 12  # ADR-004 v4 (C53)
    # Scoring (ADR-008)
    value_weight: float = 0.20  # ADR-008 v2 (C53, E12)
    # Timeouts (NFR-10)
    timeout_llm_s: float = 30
    timeout_vision_s: float = 60  # ADR-003 v3: above the 10 to 20 s target, by owner decision
    timeout_transcript_s: float = 10
    # Transcripts and recipe text (C39): live YouTube fetch switch; text cap for the 4k context (Agent Design §4)
    live_transcripts: bool = True
    max_recipe_chars: int = 6000
    # Photo detection
    confidence_threshold: float = 0.6
    # Reproducible context: empty means system clock / mock label
    context_now: str = ""
    context_weather: str = ""
    # Demo endpoints off by default (S-09)
    demo_controls: bool = False
    # Local, git-ignored storage
    trace_path: str = "logs/trace.jsonl"
    chroma_path: str = "data/chroma"

    @field_validator("guard_ignore_categories", mode="before")
    @classmethod
    def _split_categories(cls, v):
        if isinstance(v, str):
            return [part.strip().upper() for part in v.split(",") if part.strip()]
        return v

    @field_validator("addon_courses", mode="before")
    @classmethod
    def _split_courses(cls, v):
        if isinstance(v, str):
            return [part.strip() for part in v.split(",") if part.strip()]
        return v

    @field_validator("addon_weights", mode="before")
    @classmethod
    def _parse_weights(cls, v):
        if isinstance(v, str):
            pairs = (part.split(":", 1) for part in v.split(",") if part.strip())
            return {name.strip(): float(weight) for name, weight in pairs}
        return v

    @property
    def gemini_enabled(self) -> bool:
        return self.vision_provider == "gemini" and bool(self.gemini_api_key.get_secret_value())

    def resolve(self, path: str) -> Path:
        """Resolve a configured path against the repository root."""
        p = Path(path)
        return p if p.is_absolute() else REPO_ROOT / p


def load_settings(env: Mapping[str, str] | None = None, env_file: str | Path | None = REPO_ROOT / ".env") -> Settings:
    """Build Settings from `.env` (if given) overlaid by `env` (default: os.environ)."""
    merged: dict[str, str] = {}
    if env_file is not None and Path(env_file).exists():
        merged.update({k: v for k, v in dotenv_values(env_file).items() if v is not None})
    merged.update(os.environ if env is None else env)
    values = {name: merged[name.upper()] for name in Settings.model_fields if merged.get(name.upper(), "") != ""}
    return Settings(**values)
