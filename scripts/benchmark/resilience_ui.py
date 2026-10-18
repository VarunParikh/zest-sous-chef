"""E10 browser scenarios F25 and F26 (Evaluation Plan v0.6 §4.16, C63): the built frontend in headless
Chromium against an in-process backend with the fake model, both on free ports (8000 and 5173 stay free).

F25: the model answers after a delay, so the input must stay locked until the reply arrives.
F26: the chat request is aborted, or answered with a bare 500; the page must show MSG-SERVER, no
success text, and the cart must stay empty.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

import httpx
import uvicorn
from _common import ROOT

sys.path.insert(0, str(ROOT))  # the acceptance FakeOllama lives under tests/

from backend.api.app import create_app  # noqa: E402
from backend.config import load_settings  # noqa: E402
from backend.retrieval.retriever import Retriever  # noqa: E402
from backend.transcripts.source import default_chain  # noqa: E402
from tests.acceptance.chat_harness import FakeOllama, intent  # noqa: E402

MOOD = "I am feeling indulgent"
SERVER_TEXT = "seems like our servers are struggling"


class SlowFake(FakeOllama):
    def __init__(self, delay_s: float = 0.0):
        super().__init__()
        self.delay_s = delay_s

    def __call__(self, request):
        if self.delay_s and b"intent classifier" in request.content:
            time.sleep(self.delay_s)
        return super().__call__(request)


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


def _servers(fake):
    tmp = tempfile.mkdtemp(prefix="zest-e10-ui-")
    settings = load_settings(env={"TRACE_PATH": f"{tmp}/trace.jsonl", "CHROMA_PATH": f"{tmp}/chroma",
                                  "CONTEXT_NOW": "2026-10-17T19:30:00", "CONTEXT_WEATHER": "cool"}, env_file=None)
    app = create_app(settings, http_transport=httpx.MockTransport(fake), llm_transport=httpx.MockTransport(fake))
    app.state.retriever = Retriever(app.state.store, None, settings, app.state.tracer)
    app.state.transcripts = default_chain(live=None)
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    backend = f"http://127.0.0.1:{port}"
    _wait(f"{backend}/api/v1/health")
    fport = _free_port()
    proc = subprocess.Popen(["npm", "--prefix", str(ROOT / "src/frontend"), "run", "preview", "--", "--port", str(fport)],
                            env={**os.environ, "ZEST_API": backend}, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _wait(f"http://localhost:{fport}/")
    return server, proc, f"http://localhost:{fport}"


def _send(page, text=MOOD):
    page.get_by_label("Message Zest").fill(text)
    page.get_by_label("Message Zest").press("Enter")


def _f25(page, url, sc) -> list[str]:
    from playwright.sync_api import expect

    fails = []
    page.goto(url)
    expect(page.get_by_text("Hey there! I'm Zest")).to_be_visible()
    _send(page)
    t0 = time.time()
    try:
        expect(page.get_by_label("Message Zest")).to_be_disabled(timeout=1500)
    except AssertionError:
        fails.append("input not locked while the reply was pending")
    try:
        expect(page.get_by_text(sc["expect"]["reply_text"]).first).to_be_visible(timeout=30000)
    except AssertionError:
        fails.append("reply never arrived")
    waited = time.time() - t0
    if waited < sc["inject"]["fake_delay_s"] - 0.5:
        fails.append(f"reply after {waited:.1f} s, the injected delay did not apply")
    try:
        expect(page.get_by_label("Message Zest")).to_be_enabled(timeout=5000)
    except AssertionError:
        fails.append("input still locked after the reply")
    if page.get_by_role("alert").count():
        fails.append("an error was shown for a slow but successful reply")
    return fails


def _f26(page, url, sc, mode: str) -> list[str]:
    from playwright.sync_api import expect

    fails = []
    page.goto(url)
    expect(page.get_by_text("Hey there! I'm Zest")).to_be_visible()
    if mode == "abort":
        page.route("**/chat", lambda route: route.abort())
    else:
        page.route("**/chat", lambda route: route.fulfill(status=500, body="Internal Server Error", content_type="text/plain"))
    _send(page)
    try:
        expect(page.get_by_role("alert")).to_contain_text(sc["expect"]["error_text"], timeout=10000)
    except AssertionError:
        fails.append(f"{mode}: MSG-SERVER text not shown")
    if page.get_by_text(sc["expect"]["success_text_absent"]).count():
        fails.append(f"{mode}: success text shown")
    if page.locator(f"button[aria-label='{sc['expect']['cart_label']}']").count() != 1:
        fails.append(f"{mode}: cart icon no longer empty")
    try:
        expect(page.get_by_label("Message Zest")).to_be_enabled(timeout=5000)
    except AssertionError:
        fails.append(f"{mode}: input stayed locked after the failure")
    page.unroute("**/chat")
    return fails


def run_browser_scenarios(scenarios: list[dict], runs: int) -> list[dict]:
    from playwright.sync_api import sync_playwright

    subprocess.run(["npm", "--prefix", str(ROOT / "src/frontend"), "run", "build"], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    out = []
    for sc in scenarios:
        fake = SlowFake(sc["inject"].get("fake_delay_s", 0.0))
        fake.intents[MOOD] = intent("mood_intent", mood_tags=["indulgent"])
        server, proc, url = _servers(fake)
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                for run in range(1, runs + 1):
                    page = browser.new_page(viewport={"width": 1280, "height": 800})
                    if sc["id"] == "F25":
                        fails = _f25(page, url, sc)
                    else:
                        fails = [f for mode in sc["inject"]["route"] for f in _f26(page, url, sc, mode)]
                    page.close()
                    out.append({"id": sc["id"], "run": run, "layer": "browser", "failures": fails, "pass": not fails})
                browser.close()
        finally:
            proc.terminate()
            proc.wait(timeout=10)
            server.should_exit = True
    return out
