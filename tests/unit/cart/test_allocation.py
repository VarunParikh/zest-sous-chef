"""Pack allocation and shared lines (US-21; FR-70, 71, 73; AC-08, AC-24; Data Model v0.3 §8.4, C33)."""
from backend.cart.allocation import allocate, smallest_pack_set
from backend.cart.service import view
from tests.unit.cart.conftest import BUTTER, PANEER, cart, line, lines


def _packs(ln):
    return [(p.sku_id.rsplit("-", 1)[1], p.count) for p in ln.packs]


def test_t050_two_200g_paneer_needs_take_two_200g_packs(store):
    c = allocate(cart(("cd_1", [line("l_1", "cd_1", PANEER, 200, "paneer")]),
                      ("cd_2", [line("l_2", "cd_2", PANEER, 200, "paneer")])), store)
    ls = lines(c)
    assert _packs(ls["l_1"]) == [("200g", 1)] and _packs(ls["l_2"]) == [("200g", 1)]  # not one 500 g pack
    assert ls["l_1"].priced and ls["l_2"].priced and ls["l_2"].shared_from_line_id is None


def test_fr71_shared_butter_takes_one_200g_pack(store):
    c = allocate(cart(("cd_1", [line("l_1", "cd_1", BUTTER, 100)]), ("cd_2", [line("l_2", "cd_2", BUTTER, 100)])), store)
    ls = lines(c)
    assert _packs(ls["l_1"]) == [("200g", 1)] and ls["l_2"].packs == []


def test_smallest_set_prefers_least_quantity_then_fewest_packs(store):
    skus = store.skus_for(BUTTER)
    chosen, in_stock, estimated = smallest_pack_set(250, "g", skus, store)
    assert sorted((s.pack.qty, n) for s, n in chosen) == [(100.0, 1), (200.0, 1)] and in_stock and not estimated
    chosen, _, _ = smallest_pack_set(600, "g", skus, store)
    assert sorted((s.pack.qty, n) for s, n in chosen) == [(100.0, 1), (500.0, 1)]


def test_smallest_set_respects_stock_counts(store):
    big = next(s for s in store.skus_for(BUTTER) if s.pack.qty == 200)
    low = store.with_stock({big.sku_id: 0})
    chosen, in_stock, _ = smallest_pack_set(200, "g", low.skus_for(BUTTER), low)
    assert [(s.pack.qty, n) for s, n in chosen] == [(100.0, 2)] and in_stock


def test_unit_mismatch_takes_one_smallest_pack_and_is_estimated(store):
    chosen, _, estimated = smallest_pack_set(2, "piece", store.skus_for(BUTTER), store)
    assert [(s.pack.qty, n) for s, n in chosen] == [(100.0, 1)] and estimated


def test_unit_mismatch_prefers_the_smallest_in_stock_pack(store):
    # E7 adversarial arm, 2026-10-18: "1 piece" of bread sold by weight took the 400 g pack with stock 0
    # although the 700 g pack was in stock, so the line was carted out of stock with the stock filter on.
    smallest = min(store.skus_for(BUTTER), key=lambda s: s.pack.qty)
    low = store.with_stock({smallest.sku_id: 0})
    chosen, in_stock, estimated = smallest_pack_set(2, "piece", low.skus_for(BUTTER), low)
    assert [(s.pack.qty, n) for s, n in chosen] == [(200.0, 1)] and in_stock and estimated


def test_unit_mismatch_with_nothing_in_stock_is_flagged(store):
    low = store.with_stock({s.sku_id: 0 for s in store.skus_for(BUTTER)})
    chosen, in_stock, _ = smallest_pack_set(2, "piece", low.skus_for(BUTTER), low)
    assert [(s.pack.qty, n) for s, n in chosen] == [(100.0, 1)] and not in_stock


def test_t051_second_shared_line_is_dimmed_and_unpriced(store):
    c = allocate(cart(("cd_1", [line("l_1", "cd_1", BUTTER, 50)]), ("cd_2", [line("l_2", "cd_2", BUTTER, 30)])), store)
    ls = lines(c)
    assert ls["l_1"].priced and not ls["l_2"].priced and ls["l_2"].shared_from_line_id == "l_1"
    v = view(c, store)
    first, second = v.dishes
    assert first.lines[0].price_inr > 0 and second.lines[0].price_inr == 0 and second.lines[0].priced is False
    assert second.dish_total_inr == 0


def test_t052_removing_the_owner_transfers_ownership_and_totals_hold(store):
    c = allocate(cart(("cd_1", [line("l_1", "cd_1", BUTTER, 50), line("l_3", "cd_1", PANEER, 200, "paneer")]),
                      ("cd_2", [line("l_2", "cd_2", BUTTER, 30)])), store)
    price_100g = next(s.price_inr for s in store.skus_for(BUTTER) if s.pack.qty == 100)
    assert view(c, store).subtotal_inr == price_100g + next(s.price_inr for s in store.skus_for(PANEER) if s.pack.qty == 200)
    c.dishes[0].lines = [ln for ln in c.dishes[0].lines if ln.line_id != "l_1"]
    c = allocate(c, store)
    ls = lines(c)
    assert ls["l_2"].priced and ls["l_2"].shared_from_line_id is None and _packs(ls["l_2"]) == [("100g", 1)]
    v = view(c, store)
    assert v.dishes[1].dish_total_inr == price_100g
    assert v.subtotal_inr == sum(d.dish_total_inr for d in v.dishes)


def test_prices_and_quotes_come_from_the_catalogue(store):
    c = allocate(cart(("cd_1", [line("l_1", "cd_1", BUTTER, 100)])), store)
    sku = c.dishes[0].lines[0].packs[0].sku_id
    catalogue = next(s.price_inr for s in store.skus_for(BUTTER) if s.sku_id == sku)
    assert c.quotes == {sku: catalogue}
    assert view(c, store).dishes[0].lines[0].price_inr == catalogue
    dearer = store.with_prices({sku: catalogue + 7})
    assert view(c, dearer).dishes[0].lines[0].price_inr == catalogue + 7  # render time, never stale
    assert allocate(c, dearer).quotes == {sku: catalogue}  # the quote keeps what the user first saw
