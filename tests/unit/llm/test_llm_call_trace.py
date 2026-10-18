"""`llm_call` carries the call kind and outcome for every model call (Data Model v0.5 §11, C61), and a
timeout is not retried (C62; Conversation Design v0.4 §9). Prompt, reply and image data are never traced."""
import json

import httpx
import pytest

from backend.guard import default_guard
from backend.guard.pipeline import InputGuard, LlamaGuard
from backend.llm.client import LLMError, LLMInvalid, LLMTimeout, OllamaClient
from backend.llm.image import prepare_image
from backend.llm.schemas import ExtractionResult
from backend.llm.vision import GeminiVision, OllamaVision
from backend.trace import Tracer
from tests.acceptance.chat_harness import image_bytes

GOOD = {"dish_name": "dal", "servings": 2, "ingredients": [{"name": "toor dal", "qty": 150, "unit": "g", "estimated": False}]}
DETECTED = {"items": [{"name": "paneer", "confidence": 0.9}], "scene_is_food": True, "quality": "ok"}
FAKE_KEY = "not-a-real-key-trace"


def _events(path):
    return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []


def _calls(path):
    return [e["data"] for e in _events(path) if e["event"] == "llm_call"]


def _text_client(handler, tracer):
    return OllamaClient("http://127.0.0.1:11434", "fake:1b", timeout_s=5, transport=httpx.MockTransport(handler),
                        tracer=tracer, session_id="s1")


def _reply(content):
    return httpx.Response(200, json={"model": "fake:1b", "message": {"content": content}})


def test_text_call_traces_kind_and_ok(tmp_path):
    tracer = Tracer(tmp_path / "t.jsonl")
    _text_client(lambda req: _reply(json.dumps(GOOD)), tracer).generate("sys", "user", ExtractionResult, call="extract")
    [ev] = _calls(tmp_path / "t.jsonl")
    assert ev["call"] == "extract" and ev["outcome"] == "ok" and ev["schema_valid"] is True and ev["retry"] is False
    assert ev["model"] == "fake:1b" and ev["latency_ms"] >= 0


def test_text_call_invalid_twice_traces_invalid_after_one_retry(tmp_path):
    seen = []

    def handler(req):
        seen.append(1)
        return _reply("not json")

    tracer = Tracer(tmp_path / "t.jsonl")
    with pytest.raises(LLMInvalid):
        _text_client(handler, tracer).generate("sys", "user", ExtractionResult, call="intent")
    [ev] = _calls(tmp_path / "t.jsonl")
    assert len(seen) == 2 and ev["call"] == "intent" and ev["outcome"] == "invalid" and ev["retry"] is True
    assert ev["schema_valid"] is False


def test_text_call_timeout_is_traced_and_not_retried(tmp_path):
    seen = []

    def handler(req):
        seen.append(1)
        raise httpx.ReadTimeout("slow", request=req)

    tracer = Tracer(tmp_path / "t.jsonl")
    with pytest.raises(LLMTimeout):
        _text_client(handler, tracer).generate("sys", "user", ExtractionResult, call="reason")
    [ev] = _calls(tmp_path / "t.jsonl")
    assert len(seen) == 1  # C62: a timeout is not retried
    assert ev["call"] == "reason" and ev["outcome"] == "timeout" and ev["schema_valid"] is False


def test_text_call_unreachable_is_traced_as_error(tmp_path):
    def handler(req):
        raise httpx.ConnectError("refused", request=req)

    tracer = Tracer(tmp_path / "t.jsonl")
    with pytest.raises(LLMError):
        _text_client(handler, tracer).generate("sys", "user", ExtractionResult, call="extract")
    [ev] = _calls(tmp_path / "t.jsonl")
    assert ev["outcome"] == "error" and ev["call"] == "extract"


def test_trace_never_holds_prompt_or_reply_text(tmp_path):
    tracer = Tracer(tmp_path / "t.jsonl")
    _text_client(lambda req: _reply(json.dumps(GOOD)), tracer).generate("SECRET-SYSTEM", "SECRET-USER", ExtractionResult,
                                                                         call="extract")
    raw = (tmp_path / "t.jsonl").read_text()
    assert "SECRET" not in raw and "toor dal" not in raw


def _guard_transport(behaviour):
    def handler(req):
        if behaviour == "down":
            raise httpx.ConnectError("refused", request=req)
        if behaviour == "timeout":
            raise httpx.ReadTimeout("slow", request=req)
        if behaviour == "garbage":
            return httpx.Response(200, json={"nothing": True})
        return httpx.Response(200, json={"message": {"content": "safe"}})
    return httpx.MockTransport(handler)


@pytest.mark.parametrize("behaviour,outcome", [("ok", "ok"), ("down", "error"), ("timeout", "timeout"), ("garbage", "invalid")])
def test_guard_classifier_call_is_traced(tmp_path, behaviour, outcome):
    tracer = Tracer(tmp_path / "t.jsonl")
    clf = LlamaGuard("http://ollama", "llama-guard3:1b", 5, transport=_guard_transport(behaviour), tracer=tracer)
    verdict = InputGuard(default_guard(), clf, tracer).check("how long do I boil rice", session_id="s9")
    assert verdict.blocked is False  # a classifier failure leaves the rules verdict standing (ADR-006)
    [ev] = _calls(tmp_path / "t.jsonl")
    assert ev["call"] == "guard" and ev["outcome"] == outcome and ev["model"] == "llama-guard3:1b"
    assert [e["session_id"] for e in _events(tmp_path / "t.jsonl") if e["event"] == "llm_call"] == ["s9"]


def _vision_transport(behaviour):
    def handler(req):
        if behaviour == "timeout":
            raise httpx.ReadTimeout("slow", request=req)
        if behaviour == "invalid":
            return httpx.Response(200, json={"model": "fake-vl", "message": {"content": "not json"}})
        return httpx.Response(200, json={"model": "fake-vl", "message": {"content": json.dumps(DETECTED)}})
    return httpx.MockTransport(handler)


@pytest.mark.parametrize("behaviour,outcome,error", [("ok", "ok", None), ("timeout", "timeout", LLMTimeout),
                                                     ("invalid", "invalid", LLMInvalid)])
def test_local_vision_call_is_traced(tmp_path, behaviour, outcome, error):
    tracer = Tracer(tmp_path / "t.jsonl")
    v = OllamaVision("http://x.test", "fake-vl", transport=_vision_transport(behaviour), tracer=tracer, session_id="s2")
    img = prepare_image(image_bytes())
    if error is None:
        v.detect(img)
    else:
        with pytest.raises(error):
            v.detect(img)
    [ev] = _calls(tmp_path / "t.jsonl")
    assert ev["call"] == "vision" and ev["outcome"] == outcome and ev["model"] == "fake-vl"
    assert "base64" not in (tmp_path / "t.jsonl").read_text()


def test_gemini_busy_twice_is_one_traced_call_with_a_retry(tmp_path):
    seen = []

    def busy(req):
        seen.append(1)
        return httpx.Response(503, json={})

    tracer = Tracer(tmp_path / "t.jsonl")
    g = GeminiVision(FAKE_KEY, "gemini-x", transport=httpx.MockTransport(busy), retry_wait_s=0, tracer=tracer, session_id="s3")
    with pytest.raises(LLMError):
        g.detect(prepare_image(image_bytes()))
    [ev] = _calls(tmp_path / "t.jsonl")
    assert len(seen) == 2 and ev["call"] == "vision" and ev["outcome"] == "error" and ev["retry"] is True
    assert FAKE_KEY not in (tmp_path / "t.jsonl").read_text()


def test_gemini_timeout_is_not_retried(tmp_path):
    seen = []

    def slow(req):
        seen.append(1)
        raise httpx.ReadTimeout("slow", request=req)

    tracer = Tracer(tmp_path / "t.jsonl")
    g = GeminiVision(FAKE_KEY, "gemini-x", transport=httpx.MockTransport(slow), retry_wait_s=0, tracer=tracer)
    with pytest.raises(LLMTimeout):
        g.detect(prepare_image(image_bytes()))
    [ev] = _calls(tmp_path / "t.jsonl")
    assert len(seen) == 1 and ev["outcome"] == "timeout"
