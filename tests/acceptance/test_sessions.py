"""Sessions API (US-01; API Spec §3 endpoints 2 to 4, §4.1, §5; T-003, T-005)."""
from fastapi.testclient import TestClient

from backend.api.app import create_app
from backend.config import load_settings
from backend.flows.templates import TEMPLATES
from backend.session.levers import LeverSet, snapshot_hash

import httpx


def _app(tmp_path):
    env = {"CHROMA_PATH": str(tmp_path / "chroma"), "TRACE_PATH": str(tmp_path / "trace.jsonl")}
    app = create_app(load_settings(env=env, env_file=None),
                     http_transport=httpx.MockTransport(lambda r: httpx.Response(200, json={"models": []})))
    return app, TestClient(app, raise_server_exceptions=False)


def test_create_session_returns_greeting_turn(tmp_path):
    app, client = _app(tmp_path)
    r = client.post("/api/v1/sessions", json={"levers": {}})
    assert r.status_code == 201 and r.headers["X-Request-Id"]
    body = r.json()
    assert body["session_id"].startswith("s_")
    assert body["snapshot_hash"] == snapshot_hash(LeverSet())
    # The defaults equal two presets (P7 Alex and P9 Jordan, the control); the first in personas.json wins.
    assert body["persona_label"] == "Alex (Reviewer)"
    turn = body["turn"]
    assert turn["turn_id"] == "t_0001"
    (msg,) = turn["messages"]
    assert msg["role"] == "assistant" and msg["template_id"] == "MSG-GREET"
    assert msg["text"] == TEMPLATES["MSG-GREET"]
    assert msg["cards"] == [{"type": "starter_chips",
                             "chips": ["YouTube link", "Upload photo", "Text recipe", "Feeling hungry"]}]
    assert turn["cart"] == {"dishes": [], "item_count": 0, "subtotal_inr": 0}
    assert turn["cart_changed"] is False and turn["pending"] is None and turn["notices"] == []
    assert len(app.state.sessions) == 1


def test_omitted_body_takes_defaults(tmp_path):
    _, client = _app(tmp_path)
    r = client.post("/api/v1/sessions", json={})
    assert r.status_code == 201 and r.json()["snapshot_hash"] == snapshot_hash(LeverSet())


def test_non_preset_levers_are_labelled_custom(tmp_path):
    _, client = _app(tmp_path)
    r = client.post("/api/v1/sessions", json={"levers": {"gourmet_affinity": 0.51}})
    assert r.json()["persona_label"] == "Custom"


def test_t003_new_session_after_end_uses_new_levers(tmp_path):
    app, client = _app(tmp_path)
    old = client.post("/api/v1/sessions", json={"levers": {}}).json()["session_id"]
    assert client.delete(f"/api/v1/sessions/{old}").status_code == 204
    new_levers = {"diet": "Pure Veg (Strict)", "weights": {"market_trend": 0.9}, "business": {"price_cap_inr": 120}}
    r = client.post("/api/v1/sessions", json={"levers": new_levers})
    body = r.json()
    assert body["session_id"] != old
    expected = LeverSet.model_validate({**new_levers, "weights": {**LeverSet().weights.model_dump(), "market_trend": 0.9}})
    assert body["snapshot_hash"] == snapshot_hash(expected)
    assert app.state.sessions.get(body["session_id"]).snapshot == expected
    gone = client.delete(f"/api/v1/sessions/{old}")
    assert gone.status_code == 404 and gone.json()["error"]["code"] == "SESSION_NOT_FOUND"


def test_t005_invalid_levers_rejected_and_no_session_created(tmp_path):
    app, client = _app(tmp_path)
    bad = [
        {"weights": {"culinary_pairing": 1.5}},
        {"business": {"price_cap_inr": 79}},
        {"business": {"price_cap_inr": 401}},
        {"diet": "Carnivore"},
        {"specialized_diets": ["Paleo"]},
        {"unknown_lever": 1},
    ]
    for levers in bad:
        r = client.post("/api/v1/sessions", json={"levers": levers})
        assert r.status_code == 422, levers
        err = r.json()["error"]
        assert err["code"] == "INVALID_LEVERS" and err["retryable"] is False
        assert set(err) == {"code", "template_id", "user_message", "retryable", "details"}
        assert r.headers["X-Request-Id"]
    assert len(app.state.sessions) == 0


def test_config_levers_lists_defaults_options_ranges_presets(tmp_path):
    _, client = _app(tmp_path)
    body = client.get("/api/v1/config/levers").json()
    assert body["defaults"] == LeverSet().model_dump(mode="json")
    assert body["options"]["diet"] == ["Pure Veg (Strict)", "Jain (No Root Veggies / Pure Veg)", "Non-Veg / Flexitarian"]
    assert body["ranges"]["business.price_cap_inr"] == {"min": 80, "max": 400}
    assert body["ranges"]["weights.culinary_pairing"] == {"min": 0, "max": 1}
    assert body["ranges"]["history.bakery"] == {"min": 0, "max": 1}
    names = [p["name"] for p in body["presets"]]
    assert "Priya Nair" in names and len(names) == 11
    for p in body["presets"]:
        LeverSet.model_validate(p["levers"])  # every preset is a full, valid lever set


def test_unhandled_error_uses_the_envelope(tmp_path):
    app, client = _app(tmp_path)

    @app.get("/boom")
    def boom():
        raise RuntimeError("secret internals")

    r = client.get("/boom")
    assert r.status_code == 500
    err = r.json()["error"]
    assert err["code"] == "INTERNAL" and err["template_id"] == "MSG-SERVER"
    assert "secret" not in r.text
