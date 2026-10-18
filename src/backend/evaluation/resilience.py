"""E10 resilience: request kinds, the fault proxy and the per-run checks (Evaluation Plan v0.6 §4.16; C62, C63, C66).

`FaultProxy` sits where the app's HTTP transport goes. Calls that are not faulted pass through
to the real local Ollama; the target call gets the configured fault. It forwards only to local
hosts: any other host (Gemini) needs a configured fault, so no request ever leaves the machine.
"""
from __future__ import annotations

import json
import time

import httpx

LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
GEMINI_HOST = "generativelanguage.googleapis.com"
GARBAGE = "this is not json"


def classify(request: httpx.Request, guard_model: str) -> str:
    """guard | vision | extract | intent | reason (the same markers the acceptance FakeOllama uses)."""
    if request.url.host == GEMINI_HOST:
        return "vision"
    try:
        body = json.loads(request.content or b"{}")
    except ValueError:
        return "other"
    messages = body.get("messages") or []
    if body.get("model") == guard_model:
        return "guard"
    if any(m.get("images") for m in messages):
        return "vision"
    system = messages[0].get("content", "") if messages and messages[0].get("role") == "system" else ""
    if system.startswith("You extract a recipe"):
        return "extract"
    if "intent classifier" in system:
        return "intent"
    return "reason" if system else "other"


class FaultProxy(httpx.BaseTransport):
    """`faults`: {kind or "*": {"mode": status|garbage|timeout|connect|delay, "code": int, "seconds": float}}."""

    def __init__(self, inner: httpx.BaseTransport | None, faults: dict, guard_model: str):
        self.inner, self.faults, self.guard_model = inner, dict(faults), guard_model
        self.attempts: dict[str, int] = {}

    def clear(self) -> None:
        self.faults = {}

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        kind = classify(request, self.guard_model)
        self.attempts[kind] = self.attempts.get(kind, 0) + 1
        fault = self.faults.get(kind) or self.faults.get("*")
        if fault is not None:
            mode = fault["mode"]
            if mode == "status":
                return httpx.Response(fault["code"], json={}, request=request)
            if mode == "garbage":
                body = {"model": "fault"} if kind == "guard" else {"model": "fault", "message": {"content": GARBAGE}}
                return httpx.Response(200, json=body, request=request)
            if mode == "timeout":
                raise httpx.ReadTimeout("injected timeout", request=request)
            if mode == "connect":
                raise httpx.ConnectError("injected connection refusal", request=request)
            if mode == "delay":
                time.sleep(fault["seconds"])
            else:
                raise ValueError(f"unknown fault mode {mode}")
        if request.url.host not in LOCAL_HOSTS or self.inner is None:
            raise RuntimeError(f"external call refused by the E10 proxy: {request.url.host}")
        return self.inner.handle_request(request)


def check_run(expect: dict, obs: dict, success_templates: list[str]) -> list[str]:
    """Every failed check for one run, as readable strings; an empty list is a pass."""
    fails: list[str] = []
    if obs["status"] == 500:
        fails.append("HTTP 500 (crash)")
    if not obs["follow_up_ok"]:
        fails.append("follow-up after the fault was removed did not get a normal reply")
    if "status" in expect and obs["status"] != expect["status"]:
        fails.append(f"status {obs['status']}, expected {expect['status']}")
    if "error_code" in expect and obs["error_code"] != expect["error_code"]:
        fails.append(f"error code {obs['error_code']}, expected {expect['error_code']}")
    for t in expect.get("templates", []):
        if t not in obs["templates"]:
            fails.append(f"{t} missing (got {obs['templates']})")
    for t in expect.get("forbid", []):
        if t in obs["templates"]:
            fails.append(f"forbidden template {t} shown")
    changed = obs["cart_changed"] and obs["cart_before"] != obs["cart_after"]
    shown_success = [t for t in obs["templates"] if t in success_templates]
    if shown_success and not changed:
        fails.append(f"success template {shown_success} without a confirmed cart change")
    if expect.get("cart") == "unchanged" and obs["cart_before"] != obs["cart_after"]:
        fails.append("cart changed in a fault-only scenario")
    for kind, n in expect.get("attempts", {}).items():
        if obs["attempts"].get(kind, 0) != n:
            fails.append(f"{kind} attempts {obs['attempts'].get(kind, 0)}, expected {n}")
    for f in expect.get("fallbacks_used", []):
        if f not in obs["fallbacks_used"]:
            fails.append(f"fallbacks_used lacks {f} (got {obs['fallbacks_used']})")
    for f in expect.get("trace_fallback", []):
        if f not in obs["trace_fallbacks"]:
            fails.append(f"no fallback_used trace for {f} (got {obs['trace_fallbacks']})")
    for kind, outcome in expect.get("llm_outcomes", {}).items():
        if (kind, outcome) not in obs["llm_outcomes"]:
            fails.append(f"no llm_call {kind} with outcome {outcome} (got {obs['llm_outcomes']})")
    if expect.get("reason") == "template":
        from backend.flows.mood import TEMPLATE_REASON

        text = obs["texts"].get("MSG-MOOD-ADD", "")
        if TEMPLATE_REASON not in text:
            fails.append("MSG-MOOD-ADD does not carry the template reason")
    if "busy" in expect:
        b = obs["busy"] or {}
        if b.get("status") != expect["busy"]["status"] or b.get("code") != expect["busy"]["code"] or not b.get("state_unchanged"):
            fails.append(f"second message during the slow turn: {b}, expected busy {expect['busy']} with no state change")
    return fails


def scenario_status(runs: list[list[str]]) -> str:
    if not runs:
        return "NOT RUN"
    return "PASS" if all(not r for r in runs) else "FAIL"
