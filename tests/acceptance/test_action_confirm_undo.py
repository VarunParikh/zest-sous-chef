"""confirm and undo actions through the API (API Spec §4.3; FR-77; T-060 cart part)."""
from backend.cart import service
from tests.acceptance.test_cart_api import _carted


def _act(client, sid, type_, **payload):
    return client.post(f"/api/v1/sessions/{sid}/action", json={"type": type_, "payload": payload})


def test_t060_replace_and_undo_through_actions(tmp_path):
    app, client, sid, session = _carted(tmp_path, "D06")
    before = client.get(f"/api/v1/sessions/{sid}/cart").json()
    card = service.offer_replace(session, "D01", "mood")
    r = _act(client, sid, "confirm", confirm_id=card.confirm_id, choice="replace")
    turn = r.json()
    assert r.status_code == 200 and turn["cart_changed"] is True
    assert [d["dish_id"] for d in turn["cart"]["dishes"]] == ["D01"]
    msg = turn["messages"][0]
    assert msg["template_id"] == "MSG-CLEAR-DONE" and msg["cards"][0]["type"] == "undo"
    r = _act(client, sid, "undo", suggestion_id=msg["cards"][0]["suggestion_id"])
    assert r.json()["cart"] == before and r.json()["messages"][0]["template_id"] == "MSG-UNDO"
    assert r.json()["messages"][0]["text"] == "Done. Removed Dal Chawal."


def test_cancel_through_the_action_changes_nothing(tmp_path):
    _, client, sid, session = _carted(tmp_path, "D06")
    before = client.get(f"/api/v1/sessions/{sid}/cart").json()
    card = service.offer_replace(session, "D01", "mood")
    turn = _act(client, sid, "confirm", confirm_id=card.confirm_id, choice="cancel").json()
    assert turn["cart_changed"] is False and turn["cart"] == before
    assert _act(client, sid, "undo", suggestion_id="sg_404").status_code == 409
