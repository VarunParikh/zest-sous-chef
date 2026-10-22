"""Lever snapshot (US-01; FR-01, FR-02; Data Model §8.1, §8.2; T-001)."""
from datetime import datetime

from backend.engine.context import build_context
from backend.engine.recommend import recommend_dishes
from backend.session.levers import LeverSet, merge_levers, persona_label, snapshot_hash
from backend.session.store import SessionNotFound, SessionStore
from tests.unit.retrieval.conftest import events, retriever, settings, store, tracer, vector  # noqa: F401

import pytest

QUERY = "I am feeling indulgent"
CTX = build_context(now=datetime(2026, 10, 17, 19, 30), weather="cool")


def _edited() -> LeverSet:
    base = LeverSet().model_dump()
    return LeverSet.model_validate(merge_levers(base, {
        "diet": "Pure Veg (Strict)",
        "weights": {"culinary_pairing": 0, "purchase_history": 0, "market_trend": 0, "persona_gourmet": 1},
    }))


def _ids(rec) -> list[str]:
    return [s.candidate_id for s in rec.shown]


def test_t001_lever_edit_after_start_does_not_change_the_session(store, retriever):
    panel = LeverSet()  # the client's lever panel at page load
    session = SessionStore().create(panel)
    before = session.recommend_dishes(QUERY, CTX, store, retriever)

    # The user edits the panel mid-session (the client-side object, and a new one).
    panel.diet = "Pure Veg (Strict)"
    panel.weights.persona_gourmet = 1.0
    after = session.recommend_dishes(QUERY, CTX, store, retriever)

    assert _ids(after) == _ids(before)
    assert [s.breakdown.final for s in after.scored] == [s.breakdown.final for s in before.scored]
    # Control: the edited levers, used directly, do change the ranking, so this test can fail.
    assert _ids(recommend_dishes(QUERY, _edited(), CTX, store, retriever)) != _ids(before)


def test_snapshot_is_a_deep_copy_and_reads_return_copies():
    panel = LeverSet()
    session = SessionStore().create(panel)
    panel.history.bakery = 0.0
    session.snapshot.history.bakery = 0.1  # mutating a read must not reach the stored snapshot
    assert session.snapshot.history.bakery == 0.85
    assert session.snapshot_hash == snapshot_hash(LeverSet())


def test_snapshot_hash_is_stable_and_ignores_diet_order():
    a = LeverSet(specialized_diets=["Vegan", "Gluten-Free"])
    b = LeverSet(specialized_diets=["Gluten-Free", "Vegan"])
    assert snapshot_hash(a) == snapshot_hash(b)
    assert len(snapshot_hash(a)) == 12
    assert snapshot_hash(LeverSet()) != snapshot_hash(a)


def test_persona_label_custom_unless_a_preset_matches():
    presets = {"Priya Nair": LeverSet(diet="Pure Veg (Strict)")}
    assert persona_label(LeverSet(), presets) == "Default settings"  # untouched defaults (Zest 2.0, C82)
    assert persona_label(LeverSet(faith="Hindu (Regular)"), presets) == "Custom"
    assert persona_label(LeverSet(diet="Pure Veg (Strict)"), presets) == "Priya Nair"


def test_store_create_get_delete_and_trace(tmp_path):
    from backend.trace import Tracer

    t = Tracer(tmp_path / "trace.jsonl")
    sessions = SessionStore(tracer=t)
    s = sessions.create(LeverSet())
    assert s.session_id.startswith("s_") and sessions.get(s.session_id) is s and len(sessions) == 1
    assert [e["event"] for e in events(t)] == ["session_started", "lever_snapshot_applied"]
    assert events(t, "lever_snapshot_applied")[0]["data"]["snapshot_hash"] == s.snapshot_hash
    sessions.delete(s.session_id)
    with pytest.raises(SessionNotFound):
        sessions.get(s.session_id)
    with pytest.raises(SessionNotFound):
        sessions.delete(s.session_id)


def test_turn_and_message_ids_increase():
    s = SessionStore().create(LeverSet())
    assert (s.next_turn_id(), s.next_turn_id()) == ("t_0001", "t_0002")
    assert (s.next_message_id(), s.next_message_id()) == ("m_1", "m_2")
