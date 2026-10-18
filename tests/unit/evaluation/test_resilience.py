"""E10 pure parts: request kinds, the fault proxy and the per-run checks (Evaluation Plan v0.6 §4.16, C62, C63, C66)."""
import json

import httpx
import pytest

from backend.evaluation.resilience import FaultProxy, check_run, classify, scenario_status

OLLAMA = "http://127.0.0.1:11434/api/chat"
SUCCESS = ["MSG-MOOD-ADD", "MSG-YT-OK", "MSG-TXT-DRAFT"]


def _req(body, url=OLLAMA):
    return httpx.Request("POST", url, json=body)


def _text(system):
    return {"model": "llama3.2:3b", "messages": [{"role": "system", "content": system}, {"role": "user", "content": "x"}]}


@pytest.mark.parametrize("body,kind", [
    ({"model": "llama-guard3:1b", "messages": [{"role": "user", "content": "hi"}]}, "guard"),
    ({"model": "qwen3-vl:4b-instruct", "messages": [{"role": "user", "content": "p", "images": ["AAAA"]}]}, "vision"),
    (_text("You extract a recipe from the text."), "extract"),
    (_text("You are the intent classifier for Zest."), "intent"),
    (_text("Write one short reason."), "reason"),
])
def test_classify_by_model_and_prompt(body, kind):
    assert classify(_req(body), guard_model="llama-guard3:1b") == kind


def test_classify_gemini_host_is_vision():
    req = _req({"contents": []}, url="https://generativelanguage.googleapis.com/v1beta/models/x:generateContent")
    assert classify(req, guard_model="llama-guard3:1b") == "vision"


def _inner(seen):
    def handler(req):
        seen.append(json.loads(req.content)["model"])
        return httpx.Response(200, json={"model": "m", "message": {"content": "{}"}})
    return httpx.MockTransport(handler)


def test_unfaulted_calls_pass_through_and_are_counted():
    seen = []
    proxy = FaultProxy(_inner(seen), {}, guard_model="llama-guard3:1b")
    r = proxy.handle_request(_req(_text("You are the intent classifier.")))
    assert r.status_code == 200 and seen == ["llama3.2:3b"] and proxy.attempts == {"intent": 1}


@pytest.mark.parametrize("mode,check", [
    ({"mode": "status", "code": 503}, lambda r: r.status_code == 503),
    ({"mode": "garbage"}, lambda r: r.status_code == 200 and r.json()["message"]["content"] == "this is not json"),
])
def test_faulted_text_call_never_reaches_the_model(mode, check):
    seen = []
    proxy = FaultProxy(_inner(seen), {"intent": mode}, guard_model="llama-guard3:1b")
    assert check(proxy.handle_request(_req(_text("You are the intent classifier."))))
    assert seen == [] and proxy.attempts == {"intent": 1}


def test_guard_garbage_has_no_message_field():
    proxy = FaultProxy(_inner([]), {"guard": {"mode": "garbage"}}, guard_model="llama-guard3:1b")
    r = proxy.handle_request(_req({"model": "llama-guard3:1b", "messages": [{"role": "user", "content": "hi"}]}))
    assert "message" not in r.json()


@pytest.mark.parametrize("mode,exc", [({"mode": "timeout"}, httpx.ReadTimeout), ({"mode": "connect"}, httpx.ConnectError)])
def test_timeout_and_connect_faults_raise_the_transport_errors(mode, exc):
    proxy = FaultProxy(_inner([]), {"*": mode}, guard_model="llama-guard3:1b")
    with pytest.raises(exc):
        proxy.handle_request(_req(_text("Write one short reason.")))


def test_delay_then_forwards(monkeypatch):
    slept, seen = [], []
    monkeypatch.setattr("backend.evaluation.resilience.time.sleep", slept.append)
    proxy = FaultProxy(_inner(seen), {"intent": {"mode": "delay", "seconds": 5}}, guard_model="llama-guard3:1b")
    assert proxy.handle_request(_req(_text("You are the intent classifier."))).status_code == 200
    assert slept == [5] and seen == ["llama3.2:3b"]


def test_external_host_without_a_fault_is_refused():
    seen = []
    proxy = FaultProxy(_inner(seen), {}, guard_model="llama-guard3:1b")
    with pytest.raises(RuntimeError, match="external"):
        proxy.handle_request(_req({"contents": []}, url="https://generativelanguage.googleapis.com/v1beta/models/x:generateContent"))
    assert seen == []


def _obs(**kw):
    base = {"status": 200, "error_code": None, "templates": ["MSG-REPHRASE"], "texts": {}, "cart_before": [], "cart_after": [],
            "cart_changed": False, "fallbacks_used": [], "trace_fallbacks": [], "attempts": {}, "llm_outcomes": [],
            "follow_up_ok": True, "busy": None}
    return {**base, **kw}


def test_matching_run_has_no_failures():
    expect = {"status": 200, "templates": ["MSG-REPHRASE"], "cart": "unchanged", "attempts": {"intent": 2},
              "llm_outcomes": {"intent": "invalid"}}
    obs = _obs(attempts={"intent": 2, "guard": 1}, llm_outcomes=[("guard", "ok"), ("intent", "invalid")])
    assert check_run(expect, obs, SUCCESS) == []


def test_http_500_and_failed_follow_up_always_fail():
    fails = check_run({"status": 200}, _obs(status=500, follow_up_ok=False), SUCCESS)
    assert any("500" in f for f in fails) and any("follow-up" in f for f in fails)


def test_success_template_without_a_confirmed_cart_change_fails():
    obs = _obs(templates=["MSG-MOOD-ADD"], cart_changed=False)
    assert any("success" in f for f in check_run({"status": 200, "cart": "may_change"}, obs, SUCCESS))
    ok = _obs(templates=["MSG-MOOD-ADD"], cart_changed=True, cart_before=[], cart_after=[("v1", 1)])
    assert check_run({"status": 200, "cart": "may_change"}, ok, SUCCESS) == []


def test_unchanged_cart_is_checked_line_by_line():
    obs = _obs(cart_before=[("v1", 1)], cart_after=[("v1", 2)])
    assert any("cart" in f for f in check_run({"status": 200, "cart": "unchanged"}, obs, SUCCESS))


def test_missing_template_wrong_attempts_and_missing_fallbacks_are_reported():
    expect = {"status": 200, "templates": ["MSG-PHOTO-SAMPLES"], "attempts": {"vision": 2}, "fallbacks_used": ["vision"],
              "trace_fallback": ["vision"], "llm_outcomes": {"vision": "error"}, "forbid": ["MSG-SERVER"]}
    obs = _obs(templates=["MSG-SERVER"], attempts={"vision": 1})
    fails = check_run(expect, obs, SUCCESS)
    for word in ("MSG-PHOTO-SAMPLES", "attempts", "fallbacks_used", "trace", "llm_call", "forbidden"):
        assert any(word in f for f in fails), word


def test_template_reason_and_busy_checks():
    expect = {"status": 200, "reason": "template", "busy": {"status": 409, "code": "SESSION_BUSY"}, "cart": "may_change"}
    good = _obs(templates=["MSG-MOOD-ADD"], cart_changed=True, cart_after=[("v", 1)],
                texts={"MSG-MOOD-ADD": "Feeling indulgent? Let's go with X: Matches your mood and fits your settings. ✅"},
                busy={"status": 409, "code": "SESSION_BUSY", "state_unchanged": True})
    assert check_run(expect, good, SUCCESS) == []
    bad = {**good, "texts": {"MSG-MOOD-ADD": "Feeling indulgent? Let's go with X: Rich and creamy."},
           "busy": {"status": 200, "code": None, "state_unchanged": False}}
    fails = check_run(expect, bad, SUCCESS)
    assert any("template reason" in f for f in fails) and any("busy" in f for f in fails)


def test_error_code_is_checked():
    expect = {"status": 503, "error_code": "DEPENDENCY_UNAVAILABLE", "templates": ["MSG-SERVER"]}
    assert check_run(expect, _obs(status=503, error_code="DEPENDENCY_UNAVAILABLE", templates=["MSG-SERVER"]), SUCCESS) == []
    assert check_run(expect, _obs(status=503, error_code="INTERNAL", templates=["MSG-SERVER"]), SUCCESS)


def test_a_scenario_passes_only_if_every_run_passes():
    assert scenario_status([[], [], []]) == "PASS"
    assert scenario_status([[], ["x"], []]) == "FAIL"
    assert scenario_status([]) == "NOT RUN"
