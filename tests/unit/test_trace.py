"""Trace module (US-35; NFR-06; data model §11; T-109; S-07)."""
import base64
import json

import pytest

from backend.trace import EVENTS, Tracer


def _lines(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def test_event_names_match_data_model_section_11():
    assert EVENTS == {
        "session_started", "lever_snapshot_applied", "intent_classified", "retrieval_candidates",
        "guardrail_filtered", "llm_call", "suggestion_shown", "suggestion_accepted",
        "suggestion_dismissed", "cart_mutated", "fallback_used", "checkout_placed",
    }


def test_line_shape(tmp_path):
    path = tmp_path / "logs" / "trace.jsonl"
    Tracer(path).emit("session_started", "s_1")
    [line] = _lines(path)
    assert set(line) == {"ts", "session_id", "event", "data"}
    assert line["event"] == "session_started" and line["session_id"] == "s_1"
    assert line["ts"].endswith("Z")


def test_unknown_event_rejected(tmp_path):
    with pytest.raises(ValueError):
        Tracer(tmp_path / "t.jsonl").emit("user_profile", "s_1")


def test_t109_long_text_truncated_to_120(tmp_path):
    path = tmp_path / "t.jsonl"
    Tracer(path).emit("intent_classified", "s_1", text="x" * 500, nested={"message": "y" * 300})
    data = _lines(path)[0]["data"]
    assert len(data["text"]) == 120
    assert len(data["nested"]["message"]) == 120


def test_t109_no_image_data_written(tmp_path):
    path = tmp_path / "t.jsonl"
    raw = bytes(range(256)) * 40
    b64 = base64.b64encode(raw).decode()
    Tracer(path).emit(
        "llm_call", "s_1",
        image=raw,
        payload=[b64],
        uri="data:image/jpeg;base64," + b64[:80],
        model="fake",
    )
    text = path.read_text()
    assert b64[:60] not in text
    assert "data:image" not in text
    data = _lines(path)[0]["data"]
    assert data["image"] == "[removed]"
    assert data["payload"] == ["[removed]"]
    assert data["uri"] == "[removed]"
    assert data["model"] == "fake"


def test_appends_one_line_per_event(tmp_path):
    path = tmp_path / "t.jsonl"
    t = Tracer(path)
    t.emit("cart_mutated", "s_1", operation="add", line_ids=["l1"], subtotal=120)
    t.emit("fallback_used", "s_1", dependency="vector_store", reason="disabled")
    assert [l["event"] for l in _lines(path)] == ["cart_mutated", "fallback_used"]
