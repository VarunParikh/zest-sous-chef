"""E2E fixtures: the real backend app in a thread (fake Ollama, lexical retrieval) and `vite preview` of the built frontend."""
import os
import socket
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

import httpx
import pytest
import uvicorn

from backend.api.app import create_app
from backend.config import load_settings
from backend.retrieval.retriever import Retriever
from backend.transcripts.source import default_chain
from tests.acceptance.chat_harness import FakeOllama, intent

ROOT = Path(__file__).resolve().parents[2]
MOOD = "I am feeling indulgent"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait(url: str, timeout: float = 30) -> None:
    end = time.time() + timeout
    while time.time() < end:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except Exception:  # noqa: BLE001  not up yet
            time.sleep(0.2)
    raise RuntimeError(f"{url} did not start")


@pytest.fixture(scope="session")
def backend_url(tmp_path_factory):
    fake = FakeOllama()
    fake.intents[MOOD] = intent("mood_intent", mood_tags=["indulgent"])
    fake.intents["Something comforting tonight"] = intent("mood_intent", mood_tags=["comforting"])  # MSG-HELP example
    tmp = tmp_path_factory.mktemp("e2e")
    settings = load_settings(env={"TRACE_PATH": str(tmp / "trace.jsonl"), "CHROMA_PATH": str(tmp / "chroma"),
                                  "CONTEXT_NOW": "2026-10-17T19:30:00", "CONTEXT_WEATHER": "cool"}, env_file=None)
    app = create_app(settings, http_transport=httpx.MockTransport(fake), llm_transport=httpx.MockTransport(fake))
    app.state.retriever = Retriever(app.state.store, None, settings, app.state.tracer)  # lexical: deterministic, no index
    app.state.transcripts = default_chain(live=None)
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    _wait(f"http://127.0.0.1:{port}/api/v1/health")
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)


@pytest.fixture(scope="session")
def app_url(backend_url):
    if not (ROOT / "src/frontend/dist/index.html").exists():
        pytest.fail("Build the frontend first: make test-e2e builds it (npm --prefix src/frontend run build)")
    port = _free_port()
    proc = subprocess.Popen(["npm", "--prefix", str(ROOT / "src/frontend"), "run", "preview", "--", "--port", str(port)],
                            env={**os.environ, "ZEST_API": backend_url}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        _wait(f"http://localhost:{port}/")
        yield f"http://localhost:{port}"
    finally:
        proc.terminate()
        proc.wait(timeout=10)
