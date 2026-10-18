"""The substitute action through the API (API Spec §4.3; FR-76; T-059)."""
from tests.acceptance.test_cart_api import CTX, _carted
from backend.cart import service


def test_t059_substitute_action_accept(tmp_path):
    app, client, sid, session = _carted(tmp_path, "D06")
    line = next(ln for ln in session.cart.lines() if ln.ingredient_name == "paneer")
    app.state.store = app.state.store.with_stock({s.sku_id: 0 for s in app.state.store.skus_for(line.variant_id)})
    card = service.propose_substitution(session, line.line_id, CTX, app.state.store)
    r = client.post(f"/api/v1/sessions/{sid}/action",
                    json={"type": "substitute", "payload": {"substitution_id": card.substitution_id, "choice": "accept"}})
    assert r.status_code == 200
    turn = r.json()
    assert turn["cart_changed"] is True and turn["messages"][0]["template_id"] == "MSG-EDIT-OK"
    paneer = next(ln for d in turn["cart"]["dishes"] for ln in d["lines"] if ln["line_id"] == line.line_id)
    assert paneer["variant_name"] == card.to_item and paneer["in_stock"] is True
    stale = client.post(f"/api/v1/sessions/{sid}/action",
                        json={"type": "substitute", "payload": {"substitution_id": card.substitution_id, "choice": "accept"}})
    assert stale.status_code == 409 and stale.json()["error"]["code"] == "STALE_ACTION"


def test_unknown_action_type_is_a_validation_error(tmp_path):
    _, client, sid, _ = _carted(tmp_path)
    r = client.post(f"/api/v1/sessions/{sid}/action", json={"type": "teleport", "payload": {}})
    assert r.status_code == 422
