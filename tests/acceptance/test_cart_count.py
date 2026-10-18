"""Cart icon count, backend part (US-23; FR-75; AC-12; T-056). The greyed, disabled icon is a UI part (block 2.5)."""
from tests.acceptance.test_cart_api import _carted
from tests.acceptance.test_sessions import _app


def test_t056_empty_cart_has_zero_items(tmp_path):
    _, client = _app(tmp_path)
    body = client.post("/api/v1/sessions", json={"levers": {}}).json()
    assert body["turn"]["cart"]["item_count"] == 0
    assert client.get(f"/api/v1/sessions/{body['session_id']}/cart").json()["item_count"] == 0


def test_t056_count_matches_the_lines_and_drops_to_zero(tmp_path):
    _, client, sid, session = _carted(tmp_path, "D01", "D40")
    expected = sum(len(d.lines) for d in session.cart.dishes)
    assert client.get(f"/api/v1/sessions/{sid}/cart").json()["item_count"] == expected > 0
    for d in list(session.cart.dishes):
        r = client.delete(f"/api/v1/sessions/{sid}/cart/dishes/{d.cart_dish_id}")
    assert r.json()["item_count"] == 0 and r.json()["dishes"] == []
