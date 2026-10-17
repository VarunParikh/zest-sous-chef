"""Vision providers behind one interface (ADR-003 v2): `ollama` (local), `gemini` (optional,
key in the local .env only) and `samples` (labelled sample photos, always available).

Every provider takes already-prepared image bytes (EXIF stripped, see image.py) and
returns a schema-validated DetectionResult. The Gemini key travels only in the
`x-goog-api-key` header, never in a URL, a log line or an error message.
"""
from __future__ import annotations

import base64
import json
import re

import httpx
from pydantic import ValidationError

from backend.catalogue.seed import MOCK
from backend.llm.client import LLMError, LLMInvalid, LLMTimeout
from backend.llm.prompts import text
from backend.llm.schemas import DetectedItem, DetectionResult

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _parse(content: str) -> DetectionResult:
    try:
        return DetectionResult.model_validate(json.loads(content))
    except (json.JSONDecodeError, ValidationError, TypeError) as e:
        raise LLMInvalid(str(e).splitlines()[0][:200]) from e


class OllamaVision:
    def __init__(self, base_url: str, model: str, timeout_s: float = 60, transport=None, keep_alive: str = "10m"):
        self.base_url, self.model, self.keep_alive = base_url.rstrip("/"), model, keep_alive
        self._http = httpx.Client(transport=transport, timeout=timeout_s)
        self.name = f"ollama:{model}"
        self.last_served_model: str | None = None

    def detect(self, image: bytes) -> DetectionResult:
        body = {"model": self.model, "stream": False, "format": "json", "keep_alive": self.keep_alive,
                "options": {"temperature": 0, "seed": 0},
                "messages": [{"role": "user", "content": text("photo_detect"), "images": [base64.b64encode(image).decode()]}]}
        try:
            r = self._http.post(f"{self.base_url}/api/chat", json=body)
            r.raise_for_status()
        except httpx.TimeoutException as e:
            raise LLMTimeout("vision model timed out") from e
        except httpx.HTTPError as e:
            raise LLMError(f"vision call failed: {type(e).__name__}") from e
        data = r.json()
        self.last_served_model = data.get("model")
        return _parse(data.get("message", {}).get("content", ""))


class GeminiVision:
    def __init__(self, api_key: str, model: str, timeout_s: float = 20, transport=None):
        self._key, self.model = api_key, model
        self._http = httpx.Client(transport=transport, timeout=timeout_s)
        self.name = f"gemini:{model}"
        self.last_served_model: str | None = None

    def _scrub(self, s: str) -> str:
        return s.replace(self._key, "[key]") if self._key else s

    def detect(self, image: bytes) -> DetectionResult:
        body = {"contents": [{"parts": [{"text": text("photo_detect")},
                                        {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(image).decode()}}]}],
                "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
        try:
            r = self._http.post(GEMINI_URL.format(model=self.model), json=body, headers={"x-goog-api-key": self._key})
        except httpx.TimeoutException as e:
            raise LLMTimeout("Gemini timed out") from e
        except httpx.HTTPError as e:
            raise LLMError(self._scrub(f"Gemini call failed: {type(e).__name__}")) from None
        if r.status_code != 200:
            raise LLMError(self._scrub(f"Gemini returned HTTP {r.status_code}"))
        data = r.json()
        self.last_served_model = data.get("modelVersion")
        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as e:
            raise LLMInvalid("Gemini reply had no content") from e
        return _parse(content)


class SampleVision:
    """Pre-computed results for the bundled sample photos, labelled as samples (FR-55)."""

    def __init__(self, photos_path=MOCK / "photos.json"):
        self._photos = {p["id"]: p for p in json.loads(photos_path.read_text())["photos"]}
        self.name = "samples"

    def detect_sample(self, photo_id: str) -> DetectionResult:
        p = self._photos[photo_id]
        quality = "blurry" if "blurry" in p["kind"] else "dark" if "dark" in p["kind"] else "ok"
        items = []
        for label in p["visible"]:
            if re.search(r"\b(uncertain|unclear)\b", label):
                continue
            name = re.sub(r"\s*\(.*?\)", "", label).split(" or ")[0].strip()
            if name:
                items.append(DetectedItem(name=name, confidence=0.9))
        return DetectionResult(items=items, scene_is_food=bool(items) or quality != "ok", quality=quality)
