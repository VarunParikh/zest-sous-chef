"""Evaluation Plan §8 spot-check samples (C67): 20 reason lines and a 10% SKU sample, seeded and reproducible.

The owner delegated both checks to the assistant on 2026-10-18 (C67), so they are not independent: the
same assistant wrote the catalogue generator, the tags and the reason prompt. This script draws the
samples and runs the mechanical checks; the assistant's reading of each row is in
`docs/epics/zest/verify/benchmarks/spot-checks.md`.

- Reason lines: 20 of the 30 distinct E13 headline lines (run 1 of `post-hoc/c54/E13-…`; the 3 runs
  were identical), each with the exact facts the model saw (rebuilt in code; no model call).
- SKUs: 103 of the 1,027 variants (10%), each with its packs and prices. The checks are:
  - keyword classes the stored tags miss (the E7 checker's keyword reading)
  - pack price against price per unit
  - one to three packs per variant
  - stock that is not negative
"""
from __future__ import annotations

import json
import random

from _app import build, set_context
from _common import ROOT

from backend.api.cart import context
from backend.evaluation.compliance import KEYWORDS, _hits
from backend.flows.mood import DRIVERS, TEMPLATE_REASON, meal_for, steer

SEED = 20261018
OUT = ROOT / "eval" / "spot-checks"
E13 = ROOT / "eval/results/post-hoc/c54/E13-reason-line-llama3.2_3b.json"


class _Req:
    def __init__(self, app):
        self.app = app


def reason_sample() -> list[dict]:
    rows = [r for r in json.loads(E13.read_text())["per_example"] if r["run"] == 1]
    picked = {r["id"]: r for r in random.Random(SEED).sample(rows, 20)}
    prompts = {json.loads(x)["id"]: json.loads(x) for x in (ROOT / "eval/datasets/reasons_v1.jsonl").read_text().splitlines() if x.strip()}
    app, client = build(None)
    store = app.state.store
    personas = {f"P{i}": lv for i, lv in enumerate(app.state.presets.values(), 1)}
    out = []
    for pid, p in prompts.items():  # rebuild the facts exactly as reasons.py did
        set_context(app, p["context_now"], p["context_weather"])
        ctx = context(_Req(app))
        sid = client.post("/api/v1/sessions", json={"levers": personas[p["persona"]].model_dump(mode="json")}).json()["session_id"]
        session = app.state.sessions.get(sid)
        meal = meal_for(p["text"], p["mood_tags"], ctx)
        query = " ".join([p["text"], *p["mood_tags"], *([meal] if meal else [])])
        rec = session.recommend_dishes(query, ctx, store, app.state.get_retriever(), display=15)
        for k, top in enumerate(steer(rec.shown, meal, store)[: p["cards"]], 1):
            rid = f"{pid}-{k}"
            if rid not in picked:
                continue
            dish = store.dish(top.candidate_id).dish
            drivers = [DRIVERS[c] for c, v in sorted(top.breakdown.contributions.items(), key=lambda kv: -kv[1]) if v > 0][:3]
            r = picked[rid]
            assert dish.name == r["dish"], (rid, dish.name, r["dish"])  # same suggestion as the E13 run
            out.append({"id": rid, "prompt": p["text"], "persona": p["persona"], "dish": dish.name,
                        "tags": [*dish.flavour, *dish.mood_tags][:5], "drivers": drivers, "shown": r["shown"],
                        "template": r["shown"] == TEMPLATE_REASON, "c50_problems": r["problems_shown"]})
    return sorted(out, key=lambda r: r["id"])


def sku_sample() -> list[dict]:
    variants = json.loads((ROOT / "mock-data/generated/variants.json").read_text())
    skus = json.loads((ROOT / "mock-data/generated/skus.json").read_text())
    by_variant: dict[str, list] = {}
    for s in skus:
        by_variant.setdefault(s["variant_id"], []).append(s)
    n = round(len(variants) * 0.10)
    out = []
    for v in sorted(random.Random(SEED).sample(variants, n), key=lambda v: v["variant_id"]):
        text = " ".join([v["name"], *v["ingredient_list"]]).lower()
        kw = sorted(c for c in KEYWORDS if _hits(text, c))
        stored = set(v.get("flags", [])) | ({"meat"} if v["diet_class"] == "non_veg" else set()) | ({"egg"} if v["diet_class"] == "egg" else set())
        missed = [c for c in kw if c not in stored and not (c == "dairy" and not v["vegan"]) and not (c == "gluten" and not v["gluten_free"])
                  and not (c == "pork" and v["halal_status"] == "not_halal") and not (c in ("meat", "fish") and v["diet_class"] == "non_veg")]
        packs = by_variant.get(v["variant_id"], [])
        price_issues = [s["sku_id"] for s in packs
                        if abs(s["price_inr"] - v["price_per_unit_inr"] * s["pack"]["qty"] / (100 if s["pack"]["unit"] in ("g", "ml") else 1))
                        > max(2, 0.25 * s["price_inr"])]
        out.append({"variant_id": v["variant_id"], "name": v["name"], "category": v["category"], "brand": v["brand"],
                    "ingredients": v["ingredient_list"], "diet_class": v["diet_class"], "vegan": v["vegan"], "jain_ok": v["jain_ok"],
                    "satvik_ok": v["satvik_ok"], "gluten_free": v["gluten_free"], "halal": v["halal_status"], "allergens": v["allergens"],
                    "flags": v.get("flags", []), "organic": v["attributes"].get("organic"), "premium": v["attributes"].get("premium"),
                    "packs": [(s["pack"]["qty"], s["pack"]["unit"], s["price_inr"], s["stock_count"]) for s in packs],
                    "keyword_classes": kw, "tags_missing_keyword_class": missed, "price_rule_outliers": price_issues,
                    "pack_count_ok": 1 <= len(packs) <= 3, "stock_ok": all(s["stock_count"] >= 0 for s in packs)})
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    reasons, skus = reason_sample(), sku_sample()
    (OUT / "reason_lines_v1.json").write_text(json.dumps({"seed": SEED, "source": str(E13.relative_to(ROOT)), "rows": reasons},
                                                         indent=1, ensure_ascii=False) + "\n")
    (OUT / "sku_audit_v1.json").write_text(json.dumps({"seed": SEED, "population": 1027, "rows": skus}, indent=1, ensure_ascii=False) + "\n")
    print(len(reasons), "reason lines;", len(skus), "variants;",
          sum(bool(r["tags_missing_keyword_class"]) for r in skus), "with keyword classes missing from tags;",
          sum(bool(r["price_rule_outliers"]) for r in skus), "with price outliers;",
          sum(not r["pack_count_ok"] for r in skus), "bad pack counts")


if __name__ == "__main__":
    main()
