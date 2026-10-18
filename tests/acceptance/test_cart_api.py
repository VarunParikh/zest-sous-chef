"""Cart endpoints (API Spec v0.4 §3 endpoints 7 to 10, §4.6; FR-72, 74; T-054, T-055)."""
from datetime import datetime

from backend.cart import service
from backend.engine.context import build_context
from tests.acceptance.test_sessions import _app

CTX = build_context(now=datetime(2026, 10, 17, 19, 30), weather="cool")


def _carted(tmp_path, *dish_ids):
    app, client = _app(tmp_path)
    sid = client.post("/api/v1/sessions", json={"levers": {}}).json()["session_id"]
    session = app.state.sessions.get(sid)
    for d in dish_ids:
        service.add_dish(session, d, "text", CTX, app.state.store)
    return app, client, sid, session


def test_get_cart_returns_the_view(tmp_path):
    app, client, sid, session = _carted(tmp_path, "D06")
    body = client.get(f"/api/v1/sessions/{sid}/cart").json()
    assert body == service.view(session.cart, app.state.store).model_dump(mode="json")
    line = body["dishes"][0]["lines"][0]
    assert {"in_stock", "quantity", "variant_name", "packs", "price_inr"} <= set(line)


def test_t054_quantity_only_1_to_9(tmp_path):
    _, client, sid, session = _carted(tmp_path, "D01")
    line_id = session.cart.dishes[0].lines[0].line_id
    url = f"/api/v1/sessions/{sid}/cart/lines/{line_id}"
    for bad in (0, 10):
        r = client.patch(url, json={"quantity": bad})
        assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR", bad
    for good in (1, 9):
        r = client.patch(url, json={"quantity": good})
        assert r.status_code == 200, good
        assert next(ln for d in r.json()["dishes"] for ln in d["lines"] if ln["line_id"] == line_id)["quantity"] == good
    assert client.patch(url, json={}).status_code == 422  # exactly one of quantity or variant_id
    assert client.patch(url, json={"quantity": 2, "variant_id": "x"}).status_code == 422


def test_t055_delete_line_and_dish_through_the_api(tmp_path):
    _, client, sid, session = _carted(tmp_path, "D01", "D40")
    first, second = (d.cart_dish_id for d in session.cart.dishes)
    line_id = session.cart.dishes[1].lines[0].line_id
    r = client.delete(f"/api/v1/sessions/{sid}/cart/lines/{line_id}")
    assert r.status_code == 200 and line_id not in [ln["line_id"] for d in r.json()["dishes"] for ln in d["lines"]]
    r = client.delete(f"/api/v1/sessions/{sid}/cart/dishes/{second}")
    assert [d["cart_dish_id"] for d in r.json()["dishes"]] == [first]
    assert r.json()["subtotal_inr"] == r.json()["dishes"][0]["dish_total_inr"]
    stale = client.delete(f"/api/v1/sessions/{sid}/cart/dishes/{second}")
    assert stale.status_code == 409 and stale.json()["error"]["code"] == "STALE_ACTION"


def test_busy_session_rejects_cart_mutations(tmp_path):
    _, client, sid, session = _carted(tmp_path, "D01")
    line_id = session.cart.dishes[0].lines[0].line_id
    with session.busy():
        r = client.delete(f"/api/v1/sessions/{sid}/cart/lines/{line_id}")
    assert r.status_code == 409 and r.json()["error"]["code"] == "SESSION_BUSY"
    assert client.get(f"/api/v1/sessions/{sid}/cart").status_code == 200  # reads are not locked


def test_unknown_session_cart_is_404(tmp_path):
    _, client = _app(tmp_path)
    assert client.get("/api/v1/sessions/s_nope/cart").json()["error"]["code"] == "SESSION_NOT_FOUND"
