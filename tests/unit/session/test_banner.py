"""Lever-changed banner flag (US-01; FR-03; API Spec v0.3 §4.2 to §4.4; C31; T-002)."""
from backend.flows.cards import TurnResponse
from backend.flows.turns import build_turn
from backend.session.levers import LeverSet
from backend.session.store import SessionStore
from tests.acceptance.test_sessions import _app


def _session():
    return SessionStore().create(LeverSet(diet="Pure Veg (Strict)"))


def test_t002_flag_true_when_current_levers_differ():
    s = _session()
    turn = build_turn(s, [], current_levers=LeverSet(diet="Pure Veg (Strict)", gourmet_affinity=0.9))
    assert turn.levers_changed_since_snapshot is True


def test_t002_flag_false_when_levers_match_or_are_omitted():
    s = _session()
    assert build_turn(s, [], current_levers=LeverSet(diet="Pure Veg (Strict)")).levers_changed_since_snapshot is False
    assert build_turn(s, []).levers_changed_since_snapshot is False


def test_flag_ignores_specialised_diet_order():
    s = SessionStore().create(LeverSet(specialized_diets=["Vegan", "Gluten-Free"]))
    same = LeverSet(specialized_diets=["Gluten-Free", "Vegan"])
    assert build_turn(s, [], current_levers=same).levers_changed_since_snapshot is False


def test_flag_never_changes_the_snapshot():
    s = _session()
    before = s.snapshot_hash
    build_turn(s, [], current_levers=LeverSet())
    assert s.snapshot_hash == before and s.snapshot == LeverSet(diet="Pure Veg (Strict)")


def test_turn_ids_advance_and_default_is_false():
    s = _session()
    assert build_turn(s, []).turn_id == "t_0001"
    assert TurnResponse(turn_id="t", messages=[]).levers_changed_since_snapshot is False


def test_create_session_returns_flag_false(tmp_path):
    _, client = _app(tmp_path)
    turn = client.post("/api/v1/sessions", json={"levers": {}}).json()["turn"]
    assert turn["levers_changed_since_snapshot"] is False
