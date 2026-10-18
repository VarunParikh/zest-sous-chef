"""Buy Now (US-26; API Spec v0.4 §4.7; FR-80, 81, 83; AC-13, AC-28; T-057, T-058, T-017 Buy Now part)."""
from backend.cart import service
from backend.flows.templates import TEMPLATES
from tests.acceptance.test_cart_api import CTX, _carted
from tests.acceptance.test_sessions import _app


def _buy(client, sid, key="k-1"):
    headers = {"Idempotency-Key": key} if key else {}
    return client.post(f"/api/v1/sessions/{sid}/checkout", headers=headers)


def _paneer(session):
    return next(ln for ln in session.cart.lines() if ln.ingredient_name == "paneer")


def test_t057_same_key_twice_places_one_order(tmp_path):
    app, client, sid, session = _carted(tmp_path, "D06")
    subtotal = client.get(f"/api/v1/sessions/{sid}/cart").json()["subtotal_inr"]
    first = _buy(client, sid)
    assert first.status_code == 200
    body = first.json()
    assert body["subtotal_inr"] == subtotal and body["collapse_after_s"] == 10
    assert body["message"] == {"template_id": "MSG-ORDER", "text": TEMPLATES["MSG-ORDER"]}
    assert client.get(f"/api/v1/sessions/{sid}/cart").json()["item_count"] == 0  # FR-81: cart empty
    again = _buy(client, sid)
    assert again.status_code == 200 and again.json() == body and len(session.orders) == 1
    assert _buy(client, sid, key="k-2").json()["error"]["code"] == "EMPTY_CART"


def test_missing_key_and_empty_cart(tmp_path):
    _, client, sid, _ = _carted(tmp_path)
    assert _buy(client, sid, key=None).json()["error"]["code"] == "BAD_REQUEST"
    r = _buy(client, sid)
    assert r.status_code == 400 and r.json()["error"]["code"] == "EMPTY_CART"


def test_t058_stock_out_blocks_then_price_change_is_shown(tmp_path):
    app, client, sid, session = _carted(tmp_path, "D06")
    paneer = _paneer(session)
    butter = next(ln for ln in session.cart.lines() if ln.ingredient_name == "butter")
    butter_sku = butter.packs[0].sku_id
    old_price = session.cart.quotes[butter_sku]
    store = app.state.store
    app.state.store = store.with_stock({s.sku_id: 0 for s in store.skus_for(paneer.variant_id)}).with_prices(
        {butter_sku: old_price + 9})

    r = _buy(client, sid)
    assert r.status_code == 409
    err = r.json()["error"]
    assert err["code"] == "OUT_OF_STOCK" and err["details"]["line_ids"] == [paneer.line_id]
    assert err["template_id"] == "MSG-BLOCKED-ORDER" and store.variant(paneer.variant_id).name in err["user_message"]
    (sub,) = err["details"]["substitutions"]
    assert sub["type"] == "substitution" and not session.orders

    client.post(f"/api/v1/sessions/{sid}/action",
                json={"type": "substitute", "payload": {"substitution_id": sub["substitution_id"], "choice": "accept"}})
    r = _buy(client, sid)
    assert r.status_code == 409
    err = r.json()["error"]
    assert err["code"] == "PRICE_CHANGED" and err["template_id"] == "MSG-PRICE-CHANGED"
    shown = next(ln for d in err["details"]["cart"]["dishes"] for ln in d["lines"] if ln["line_id"] == butter.line_id)
    assert shown["price_inr"] == old_price + 9 and not session.orders

    r = _buy(client, sid)  # the user has now seen the new price
    assert r.status_code == 200 and r.json()["subtotal_inr"] == err["details"]["cart"]["subtotal_inr"]


def test_t017_buy_now_blocked_for_a_kept_out_of_stock_line(tmp_path):
    app, client = _app(tmp_path)
    store = app.state.store
    app.state.store = store.with_stock({s.sku_id: 0 for v in store.variants_for("paneer") for s in store.skus_for(v.variant_id)})
    sid = client.post("/api/v1/sessions", json={"levers": {"business": {"stock_filter": False}}}).json()["session_id"]
    session = app.state.sessions.get(sid)
    service.add_dish(session, "D06", "text", CTX, app.state.store)
    r = _buy(client, sid)
    assert r.status_code == 409 and r.json()["error"]["details"]["line_ids"] == [_paneer(session).line_id]
    assert r.json()["error"]["details"]["substitutions"] == []  # no paneer in stock to offer


def test_checkout_respects_the_session_lock(tmp_path):
    _, client, sid, session = _carted(tmp_path, "D01")
    with session.busy():
        assert _buy(client, sid).json()["error"]["code"] == "SESSION_BUSY"
