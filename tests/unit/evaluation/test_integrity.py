"""E8 checks (Evaluation Plan §4 E8): an independent re-derivation of packs and prices, written before any E8 run."""
from backend.evaluation.integrity import Pack, cart_mismatches, optimal_packs, rupees


def test_combined_need_uses_one_pack_fr71():
    # FR-71: 100 g of butter needed twice is one 200 g pack, not two 100 g packs
    packs = [Pack("b100", 100, 50, 9), Pack("b200", 200, 90, 9)]
    assert optimal_packs(200, packs) == {"b200": 1}


def test_least_quantity_then_fewest_packs_then_price():
    packs = [Pack("a250", 250, 30, 9), Pack("a500", 500, 55, 9), Pack("a1k", 1000, 100, 9)]
    assert optimal_packs(450, packs) == {"a500": 1}  # 500 beats 2 x 250 (same quantity, fewer packs)
    assert optimal_packs(260, packs) == {"a500": 1}  # 500 g either way; one pack beats two
    cheap = [Pack("x", 500, 40, 9), Pack("y", 500, 35, 9)]
    assert optimal_packs(500, cheap) == {"y": 1}


def test_stock_limits_the_pack_set():
    packs = [Pack("big", 1000, 90, 0), Pack("small", 500, 50, 9)]
    assert optimal_packs(900, packs) == {"small": 2}
    assert optimal_packs(900, packs, limit_by_stock=False) == {"big": 1}


def test_no_cover_returns_none():
    assert optimal_packs(900, [Pack("big", 1000, 90, 0)]) is None


def test_rupee_amounts():
    assert rupees("Added Dal Chawal (₹212). Cart total: ₹1,045.") == [212, 1045]
    assert rupees("Rs. 40 and Rs 5") == [40, 5]
    assert rupees("No prices here, 3 items") == []


def _view(lines, dish_total, subtotal):
    return {"dishes": [{"cart_dish_id": "cd1", "dish_total_inr": dish_total, "lines": lines}], "subtotal_inr": subtotal,
            "item_count": len(lines)}


def test_cart_mismatches_finds_wrong_line_dish_and_subtotal():
    prices = {"s1": 40, "s2": 25}
    good = [{"line_id": "l1", "packs": [{"sku_id": "s1", "count": 2}], "price_inr": 80, "priced": True, "shared_from_line_id": None},
            {"line_id": "l2", "packs": [], "price_inr": 0, "priced": False, "shared_from_line_id": "l1"}]
    assert cart_mismatches(_view(good, 80, 80), prices) == []
    bad = [{**good[0], "price_inr": 79}, {**good[1], "shared_from_line_id": None}]
    kinds = {m["kind"] for m in cart_mismatches(_view(bad, 81, 82), prices)}
    assert kinds == {"line_price", "dish_total", "subtotal", "unpriced_line_not_shared"}
