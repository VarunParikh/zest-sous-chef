"""Input guard pipeline (ADR-006, decided 2026-10-18; FR-10, 12; Agent Design A1, §7).

Rules first, in code. Text the rules pass goes to `llama-guard3:1b`, called exactly as
in E4 (the raw text as one user message, temperature 0; a reply starting with
"unsafe" blocks). A block replies with a template only: no intent call, no cart
change. If the classifier fails, the rules result stands and `fallback_used` is traced.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass

import httpx

from backend.guard import YOUTUBE, Guard

CLASSIFIER_TEMPLATE = {"user": "MSG-REDIRECT", "transcript": "MSG-INJECT-DATA"}


@dataclass(frozen=True)
class Verdict:
    blocked: bool
    label: str  # ok | injection | hazard | off_topic | unsafe
    template_id: str | None
    layer: str | None = None  # rules | classifier
    fallback: bool = False


class LlamaGuard:
    """`ignore`: categories that never block (S6 Specialized Advice flagged "what should I eat", C44).
    `ignore_if_link`: categories ignored only when the text has a YouTube link (S8 Intellectual Property flagged
    every bare video link, C40; ADR-006 v5, C55: elsewhere an S8 verdict blocks)."""

    def __init__(self, base_url: str, model: str, timeout_s: float, transport: httpx.BaseTransport | None = None,
                 ignore: frozenset[str] = frozenset({"S6"}), ignore_if_link: frozenset[str] = frozenset({"S8"}),
                 tracer=None):
        self.base_url, self.model, self.ignore = base_url.rstrip("/"), model, frozenset(c.upper() for c in ignore)
        self.ignore_if_link = frozenset(c.upper() for c in ignore_if_link)
        self._http = httpx.Client(transport=transport, timeout=timeout_s)
        self.tracer = tracer

    def _trace(self, t0: float, outcome: str, session_id: str) -> None:
        if self.tracer is not None:  # C61: one `llm_call` per classifier call; the text is never traced
            self.tracer.emit("llm_call", session_id, model=self.model, call="guard", outcome=outcome,
                             latency_ms=round((time.perf_counter() - t0) * 1000, 1), schema_valid=outcome == "ok",
                             retry=False)

    def verdict(self, text: str, session_id: str = "-") -> tuple[bool, tuple[str, ...]]:
        """(blocks, categories the classifier gave); the categories are recorded by E4 (C46). Not retried (C62)."""
        t0 = time.perf_counter()
        try:
            r = self._http.post(f"{self.base_url}/api/chat", json={
                "model": self.model, "stream": False, "options": {"temperature": 0},
                "messages": [{"role": "user", "content": text}]})
            r.raise_for_status()
        except httpx.TimeoutException:
            self._trace(t0, "timeout", session_id)
            raise
        except httpx.HTTPError:
            self._trace(t0, "error", session_id)
            raise
        try:
            reply = r.json()["message"]["content"].strip()
        except (KeyError, ValueError, TypeError, AttributeError):
            self._trace(t0, "invalid", session_id)
            raise
        self._trace(t0, "ok", session_id)
        if not reply.lower().startswith("unsafe"):
            return False, ()
        categories = tuple(sorted({c.strip().upper() for c in re.split(r"[,\s]+", reply[len("unsafe"):]) if c.strip()}))
        ignored = self.ignore | (self.ignore_if_link if YOUTUBE.search(text) else frozenset())
        return (not categories or bool(set(categories) - ignored)), categories  # no category given: block

    def unsafe(self, text: str, session_id: str = "-") -> bool:
        return self.verdict(text, session_id)[0]


class InputGuard:
    def __init__(self, rules: Guard, classifier: LlamaGuard | None = None, tracer=None):
        self.rules, self.classifier, self.tracer = rules, classifier, tracer

    def check(self, text: str, source: str = "user", session_id: str = "-") -> Verdict:
        s = self.rules.screen(text, source=source)
        if s.label != "ok" and s.message_id is not None:
            return Verdict(True, s.label, s.message_id, "rules")
        if self.classifier is None:
            return Verdict(False, "ok", None)
        try:
            if self.classifier.unsafe(text, session_id):
                return Verdict(True, "unsafe", CLASSIFIER_TEMPLATE.get(source, "MSG-REDIRECT"), "classifier")
        except (httpx.HTTPError, KeyError, ValueError, TypeError, AttributeError) as e:
            if self.tracer is not None:
                self.tracer.emit("fallback_used", session_id, component="guard_classifier", reason=type(e).__name__)
            return Verdict(False, "ok", None, fallback=True)
        return Verdict(False, "ok", None)
