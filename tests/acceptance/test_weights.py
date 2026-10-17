"""Weights shares and the all-zero notice (US-02; FR-08; AC-03; C30; T-004)."""
from backend.engine.scoring import effective_weights
from backend.flows.templates import TEMPLATES
from backend.session.levers import Weights
from tests.acceptance.test_sessions import _app

ZERO = {"culinary_pairing": 0, "purchase_history": 0, "market_trend": 0, "persona_gourmet": 0}


def test_t004_shares_for_80_80_40_0():
    w, restored = effective_weights(Weights(culinary_pairing=0.8, purchase_history=0.8, market_trend=0.4, persona_gourmet=0))
    assert w == {"s_p": 0.4, "s_h": 0.4, "s_t": 0.2, "s_g": 0.0} and not restored
    assert abs(sum(w.values()) - 1) < 1e-9


def test_t004_all_zero_restores_defaults_and_sets_the_notice(tmp_path):
    w, restored = effective_weights(Weights(**ZERO))
    d = Weights()
    assert restored and w == {"s_p": d.culinary_pairing, "s_h": d.purchase_history,
                              "s_t": d.market_trend, "s_g": d.persona_gourmet}  # defaults already sum to 1
    _, client = _app(tmp_path)
    notices = client.post("/api/v1/sessions", json={"levers": {"weights": ZERO}}).json()["turn"]["notices"]
    assert notices == [{"type": "notice", "level": "info", "template_id": "MSG-WEIGHTS-DEFAULT",
                        "text": TEMPLATES["MSG-WEIGHTS-DEFAULT"]}]


def test_no_notice_when_any_weight_is_set(tmp_path):
    _, client = _app(tmp_path)
    levers = {"weights": {**ZERO, "market_trend": 0.05}}
    assert client.post("/api/v1/sessions", json={"levers": levers}).json()["turn"]["notices"] == []


def test_config_levers_shows_default_shares(tmp_path):
    _, client = _app(tmp_path)
    shares = client.get("/api/v1/config/levers").json()["default_shares"]
    assert shares == {"s_p": 0.3, "s_h": 0.35, "s_t": 0.2, "s_g": 0.15}
