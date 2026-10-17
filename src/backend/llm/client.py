"""Ollama chat client for schema-validated JSON (Agent Design §8; NFR-10, NFR-11).

Temperature 0, JSON format, one timeout per call, at most one retry that tells the
model why its reply was invalid. The second failure raises LLMInvalid so the caller
takes its defined fallback. Every call is traced as `llm_call` (model, latency,
schema_valid, retry); prompt and reply text are never traced.
"""
from __future__ import annotations

import json
import time
from typing import TypeVar

import httpx
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    pass


class LLMTimeout(LLMError):
    pass


class LLMInvalid(LLMError):
    pass


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_s: float = 30, transport: httpx.BaseTransport | None = None,
                 tracer=None, session_id: str = "-", num_ctx: int | None = None):
        self.base_url, self.model, self.timeout_s = base_url.rstrip("/"), model, timeout_s
        self._http = httpx.Client(transport=transport, timeout=timeout_s)
        self.tracer, self.session_id, self.num_ctx = tracer, session_id, num_ctx
        self.last_stats: dict = {}

    def _chat(self, messages: list[dict]) -> tuple[str, dict]:
        body = {"model": self.model, "messages": messages, "stream": False, "format": "json",
                "options": {"temperature": 0, "seed": 0, **({"num_ctx": self.num_ctx} if self.num_ctx else {})}}
        try:
            r = self._http.post(f"{self.base_url}/api/chat", json=body)
            r.raise_for_status()
        except httpx.TimeoutException as e:
            raise LLMTimeout(str(e)) from e
        except httpx.HTTPError as e:
            raise LLMError(str(e)) from e
        data = r.json()
        return data.get("message", {}).get("content", ""), data

    def generate(self, system: str, user: str, schema: type[T]) -> T:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        t0, retry, error = time.perf_counter(), False, ""
        for attempt in range(2):
            content, raw = self._chat(messages)
            try:
                result = schema.model_validate(json.loads(content))
                self._trace(t0, True, retry, raw)
                return result
            except (json.JSONDecodeError, ValidationError, TypeError) as e:
                error = str(e).splitlines()[0][:200]
                if attempt == 0:
                    retry = True
                    messages += [{"role": "assistant", "content": content},
                                 {"role": "user", "content": f"Your last reply was invalid because: {error}. Return valid JSON only."}]
        self._trace(t0, False, retry, raw)
        raise LLMInvalid(error)

    def _trace(self, t0: float, valid: bool, retry: bool, raw: dict):
        latency = (time.perf_counter() - t0) * 1000
        self.last_stats = {"latency_ms": latency, "schema_valid": valid, "retry": retry,
                           "eval_count": raw.get("eval_count"), "prompt_eval_count": raw.get("prompt_eval_count"),
                           "served_model": raw.get("model")}
        if self.tracer is not None:
            self.tracer.emit("llm_call", self.session_id, model=self.model, latency_ms=round(latency, 1),
                             schema_valid=valid, retry=retry)
