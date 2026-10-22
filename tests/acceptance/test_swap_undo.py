"""Swap and Undo by suggestion (FR-41; AC-30; T-062). The mood flow that creates the suggestion is block 2.3."""
import pytest

from backend.cart import service
from tests.acceptance.test_cart_api import CTX, _carted


def _act(client, sid, type_, **payload):
    return client.post(f"/api/v1/sessions/{sid}/action", json={"type": type_, "payload": payload})


def test_t062_swap_replaces_only_the_suggested_dish_and_undo_restores(tmp_path):
    app, client, sid, session = _carted(tmp_path, "D01")  # added earlier by the user
    before = client.get(f"/api/v1/sessions/{sid}/cart").json()
    user_dish = before["dishes"][0]
    sg, added = service.add_suggested(session, "D06", ["D130", "D05"], "mood", CTX, app.state.store)
    assert added.added_by_suggestion_id == sg and [d.dish_id for d in session.cart.dishes] == ["D01", "D06"]

    r = _act(client, sid, "swap", suggestion_id=sg, alt_dish_id="D05")
    turn = r.json()
    assert r.status_code == 200 and turn["cart_changed"] is True
    assert [d["dish_id"] for d in turn["cart"]["dishes"]] == ["D01", "D05"]
    # The user's items are never touched: same lines, variants and quantities. Pack sizes may change, because a
    # shared ingredient (tomato) is allocated for the combined need (C33).
    items = lambda d: [(ln["line_id"], ln["ingredient_name"], ln["variant_id"], ln["quantity"]) for ln in d["lines"]]
    assert items(turn["cart"]["dishes"][0]) == items(user_dish)
    msg = turn["messages"][0]
    assert msg["template_id"] == "MSG-MOOD-SWAP" and msg["text"].startswith("Swapped to Chicken Tikka Masala.")
    swaps = next(c for c in msg["cards"] if c["type"] == "swap_options")
    assert [o["dish_id"] for o in swaps["options"]] == ["D06", "D130"]  # the replaced dish becomes an option
    assert any(c["type"] == "undo" and c["suggestion_id"] == sg for c in msg["cards"])

    r = _act(client, sid, "undo", suggestion_id=sg)
    assert r.json()["cart"] == before and r.json()["messages"][0]["text"] == "Done. Removed Chicken Tikka Masala."


def test_swap_to_a_dish_not_offered_or_after_undo_is_stale(tmp_path):
    app, client, sid, session = _carted(tmp_path)
    sg, _ = service.add_suggested(session, "D06", ["D130", "D05"], "mood", CTX, app.state.store)
    assert _act(client, sid, "swap", suggestion_id=sg, alt_dish_id="D01").status_code == 409
    _act(client, sid, "undo", suggestion_id=sg)
    # FR-127: after Undo the tap asks whether to add D05 instead; the cart is not swapped, and the service still refuses
    after = _act(client, sid, "swap", suggestion_id=sg, alt_dish_id="D05")
    assert after.status_code == 200 and after.json()["messages"][-1]["template_id"] == "MSG-SWAP-GONE"
    assert "D05" not in [d.dish_id for d in session.cart.dishes]
    with pytest.raises(service.CartRuleError):
        service.swap(session, sg, "D05", CTX, app.state.store)
