"""A fake Ollama for chat tests: the guard model, the intent classifier (A2) and the reason line (A4)."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.config import load_settings
from backend.retrieval.retriever import Retriever


def intent(name, confidence=0.95, mood_tags=(), dish_name=None):
    return {"intent": name, "confidence": confidence, "mood_tags": list(mood_tags), "dish_name": dish_name, "servings": None}


class FakeOllama:
    def __init__(self):
        self.intents: dict[str, object] = {}  # message -> IntentResult dict, raw string, or Exception
        self.unsafe: set[str] = set()
        self.reason: object = {"reason": "Rich, creamy and a weekend favourite."}
        self.calls: list[str] = []  # "guard", "intent", "reason"
        self.down = False
        self.extractions: dict[str, object] = {}  # recipe text (substring) -> ExtractionResult dict, raw string, or Exception

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if self.down:
            raise httpx.ConnectError("refused", request=request)
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": []})
        body = json.loads(request.content)
        if body["model"] == "llama-guard3:1b":
            self.calls.append("guard")
            text = body["messages"][-1]["content"]
            return httpx.Response(200, json={"message": {"content": "unsafe\nS1" if text in self.unsafe else "safe"}})
        system = body["messages"][0]["content"]
        user = body["messages"][1]["content"]
        if system.startswith("You extract a recipe"):
            self.calls.append("extract")
            content_text = user.split("<content>", 1)[1].split("</content>", 1)[0]
            out = next((v for k, v in self.extractions.items() if k in content_text),
                       {"dish_name": None, "servings": None, "ingredients": []})
        elif "intent classifier" in system:
            self.calls.append("intent")
            msg = user.split("<content>", 1)[1].split("</content>", 1)[0]
            out = self.intents.get(msg, intent("smalltalk"))
        else:
            self.calls.append("reason")
            out = self.reason
        if isinstance(out, Exception):
            raise out
        content = out if isinstance(out, str) else json.dumps(out)
        return httpx.Response(200, json={"model": body["model"], "message": {"content": content}})


@pytest.fixture
def fake():
    return FakeOllama()


@pytest.fixture
def chat_app(tmp_path, fake, store, vector, settings):
    env = {"CHROMA_PATH": str(tmp_path / "chroma"), "TRACE_PATH": str(tmp_path / "trace.jsonl"),
           "CONTEXT_NOW": "2026-10-17T19:30:00", "CONTEXT_WEATHER": "cool"}
    app = create_app(load_settings(env=env, env_file=None), http_transport=httpx.MockTransport(fake),
                     llm_transport=httpx.MockTransport(fake))
    app.state.retriever = Retriever(store, vector, settings, app.state.tracer)
    from backend.transcripts.source import default_chain

    def live_down(vid, timeout):  # tests never touch the network; a test can swap in its own chain
        raise RuntimeError("no network in tests")

    app.state.transcripts = default_chain(live=live_down)
    return app, TestClient(app, raise_server_exceptions=False)


def start(client, levers=None):
    return client.post("/api/v1/sessions", json={"levers": levers or {}}).json()["session_id"]


def say(client, sid, text, **extra):
    return client.post(f"/api/v1/sessions/{sid}/chat", json={"text": text, **extra})


def trace(app):
    path = app.state.tracer.path
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


def line(name, qty=None, unit=None, estimated=False):
    return {"name": name, "qty": qty, "unit": unit, "estimated": estimated}


def extraction(dish=None, *lines, servings=None):
    return {"dish_name": dish, "servings": servings, "ingredients": list(lines)}
