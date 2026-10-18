"""In-process app for the block 2.6 evaluations (ports 8000 and 5173 stay free).

`fake`: a FakeOllama from the acceptance harness (scripted intent, extraction and reason
replies, guard always safe), or None for the real local models. Transcripts never use the
network (fixtures only) and photos use the labelled samples (C52). Settings come from
`.env` overlaid with the run's context; the Gemini key is never read here.
"""
from __future__ import annotations

import tempfile

import httpx
from _common import ROOT  # noqa: F401  (puts src/ on the path)
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.catalogue.store import load_store
from backend.config import load_settings
from backend.transcripts.source import default_chain

TRACE_DIR = tempfile.mkdtemp(prefix="zest-eval-")


def eval_settings(context_now: str, weather: str, **extra):
    env = {"CONTEXT_NOW": context_now, "CONTEXT_WEATHER": weather, "LIVE_TRANSCRIPTS": "false",
           "VISION_PROVIDER": "samples", "TRACE_PATH": f"{TRACE_DIR}/trace.jsonl", **extra}
    return load_settings(env=env)


def build(fake=None, context_now="2026-05-16T19:30:00", weather="hot", store=None, **extra):
    transport = httpx.MockTransport(fake) if fake is not None else None
    app = create_app(eval_settings(context_now, weather, **extra), http_transport=transport, llm_transport=transport)
    app.state.store = store or load_store()  # a private store: stock overrides never leak between runs

    def no_network(vid, timeout):
        raise RuntimeError("live transcripts are off in evaluations")

    app.state.transcripts = default_chain(live=no_network)
    return app, TestClient(app, raise_server_exceptions=False)


def set_context(app, context_now: str, weather: str) -> None:
    app.state.settings = app.state.settings.model_copy(update={"context_now": context_now, "context_weather": weather})
