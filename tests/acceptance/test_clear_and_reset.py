"""Clear chat and Reset levers, backend side (US-03; FR-04, FR-05; AC-18, AC-19; C32; T-007, T-008).

The confirmation dialog and the Reset button are frontend parts (block 2.5).
"""
from backend.cart.models import Cart, CartDish, CartLine
from backend.session.levers import LeverSet
from tests.acceptance.test_sessions import _app

LEVERS = {"diet": "Pure Veg (Strict)", "gourmet_affinity": 0.9}


def _seed_cart(session):
    line = CartLine(line_id="l_1", cart_dish_id="cd_1", ingredient_name="paneer", need_qty=200, need_unit="g",
                    variant_id="V0001")
    session.cart = Cart(dishes=[CartDish(cart_dish_id="cd_1", dish_id="D01", name="Paneer Butter Masala",
                                         source="mood", lines=[line])])


def test_t007_cancel_changes_nothing_confirm_empties_cart_levers_untouched(tmp_path):
    app, client = _app(tmp_path)
    sid = client.post("/api/v1/sessions", json={"levers": LEVERS}).json()["session_id"]
    session = app.state.sessions.get(sid)
    _seed_cart(session)
    snapshot = session.snapshot
    messages = list(session.messages)

    # Cancel: the frontend sends nothing (C32), so the session, cart and snapshot stay as they were.
    assert app.state.sessions.get(sid) is session
    assert not session.cart.is_empty and session.snapshot == snapshot and session.messages == messages

    # Confirm: discard the session (and its cart), then start anew with the panel's levers.
    assert client.delete(f"/api/v1/sessions/{sid}").status_code == 204
    new = client.post("/api/v1/sessions", json={"levers": LEVERS}).json()
    fresh = app.state.sessions.get(new["session_id"])
    assert fresh.cart.is_empty and new["turn"]["cart"]["item_count"] == 0
    assert fresh.snapshot == LeverSet.model_validate(LEVERS) == snapshot  # levers untouched
    assert len(app.state.sessions) == 1
    assert [m["template_id"] for m in new["turn"]["messages"]] == ["MSG-GREET"]


def test_t008_reset_defaults_leave_chat_and_snapshot_untouched(tmp_path):
    app, client = _app(tmp_path)
    sid = client.post("/api/v1/sessions", json={"levers": LEVERS}).json()["session_id"]
    session = app.state.sessions.get(sid)
    before = (session.snapshot_hash, session.snapshot, list(session.messages))

    defaults = client.get("/api/v1/config/levers").json()["defaults"]
    assert LeverSet.model_validate(defaults) == LeverSet()  # Reset restores the Settings Panel defaults
    assert (session.snapshot_hash, session.snapshot, list(session.messages)) == before
