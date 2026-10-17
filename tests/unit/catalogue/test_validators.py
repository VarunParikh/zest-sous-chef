"""Validators V1 to V14 (Data Model §13; T-020 canary, T-100, T-101)."""
import copy
import json

import pytest

from backend.catalogue.validators import VALIDATORS, load_context, run_all


@pytest.fixture(scope="module")
def base_ctx():
    return load_context()


@pytest.fixture
def ctx(base_ctx):
    return copy.deepcopy(base_ctx)


def _first(ctx, pred):
    return next(v for v in ctx.variants if pred(v))


def test_shipped_data_passes(base_ctx):
    results = run_all(base_ctx)
    assert set(results) == {f"V{i}" for i in range(1, 15)}
    failing = {k: r.errors[:5] for k, r in results.items() if r.status == "FAIL"}
    assert not failing
    # Honest statuses: these depend on later blocks and must not pretend to pass.
    assert results["V9"].status == "NOT RUN"
    assert results["V12"].status == "NOT RUN"


def test_v1_missing_field(ctx):
    del ctx.variants[0]["brand"]
    assert VALIDATORS["V1"](ctx).status == "FAIL"


def test_v2_duplicate_ingredient_list(ctx):
    ctx.variants[1]["ingredient_list"] = list(ctx.variants[0]["ingredient_list"])
    assert VALIDATORS["V2"](ctx).status == "FAIL"


def test_t020_canary_mis_tagged_variant_fails_v3(ctx):
    v = _first(ctx, lambda v: v["diet_class"] == "non_veg")
    v["diet_class"] = "vegetarian"
    assert VALIDATORS["V3"](ctx).status == "FAIL"


def test_v3_mis_tagged_jain_flag(ctx):
    v = _first(ctx, lambda v: v["ingredient_list"][0].startswith("onion"))
    v["jain_ok"] = True
    assert VALIDATORS["V3"](ctx).status == "FAIL"


def test_v3_dish_claimed_diet(ctx):
    ctx.dishes[0].dish.diet_class = "vegan"  # D01 contains ghee
    assert VALIDATORS["V3"](ctx).status == "FAIL"


def test_v4_unknown_term(ctx):
    ctx.variants[0]["ingredient_list"].append("unobtainium")
    assert VALIDATORS["V4"](ctx).status == "FAIL"


def test_v5_meat_without_halal_status(ctx):
    v = _first(ctx, lambda v: "meat" in v["flags"])
    v["halal_status"] = "not_applicable"
    assert VALIDATORS["V5"](ctx).status == "FAIL"


def test_v6_price_out_of_range(ctx):
    ctx.variants[0]["price_per_unit_inr"] *= 50
    assert VALIDATORS["V6"](ctx).status == "FAIL"


def test_v6_larger_pack_dearer(ctx):
    by_variant = {}
    for s in ctx.skus:
        by_variant.setdefault(s["variant_id"], []).append(s)
    skus = next(s for s in by_variant.values() if len(s) > 1)
    big = max(skus, key=lambda s: s["pack"]["qty"])
    big["price_inr"] *= 10
    assert VALIDATORS["V6"](ctx).status == "FAIL"


def test_v7_negative_stock(ctx):
    ctx.skus[0]["stock_count"] = -1
    assert VALIDATORS["V7"](ctx).status == "FAIL"


def test_v8_unresolved_dish_ingredient(ctx):
    line = ctx.dishes[0].ingredients[0]
    ctx.dishes[0].ingredients[0] = line.model_copy(update={"ingredient_name": "nori"})
    assert VALIDATORS["V8"](ctx).status == "FAIL"


def test_t101_sushi_gap_is_by_design(base_ctx):
    r = VALIDATORS["V8"](base_ctx)
    assert r.status == "PASS"
    assert "D35" in r.note


def test_v10_alias_collision(ctx):
    ctx.lexicon.entries["tomato"].aliases.append("palak")
    assert VALIDATORS["V10"](ctx).status == "FAIL"


def test_v10_synonym_without_target(ctx):
    ctx.synonyms.append({"query_term": "zzz", "maps_to": "unobtainium", "type": "ingredient"})
    assert VALIDATORS["V10"](ctx).status == "FAIL"


def test_v11_price_in_embedding_text(ctx):
    ctx.variants[0]["embedding_text"] += " Only ₹45."
    assert VALIDATORS["V11"](ctx).status == "FAIL"


def test_v13_committed_file_stale(ctx, tmp_path):
    for name in ("variants.json", "skus.json"):
        (tmp_path / name).write_bytes((ctx.generated_dir / name).read_bytes())
    data = json.loads((tmp_path / "skus.json").read_text())
    data[0]["stock_count"] += 1
    (tmp_path / "skus.json").write_text(json.dumps(data))
    ctx.generated_dir = tmp_path
    assert VALIDATORS["V13"](ctx).status == "FAIL"


def test_v14_persona_out_of_range(ctx):
    ctx.personas["personas"][0]["levers"]["gourmet_affinity"] = 1.5
    assert VALIDATORS["V14"](ctx).status == "FAIL"


def test_v14_unknown_option_string(ctx):
    ctx.personas["personas"][0]["levers"]["diet"] = "Jain"
    assert VALIDATORS["V14"](ctx).status == "FAIL"
