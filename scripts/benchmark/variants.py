"""E12 variant scoring sweep (Evaluation Plan §4 E12; ADR-008; FR-113).

The 6 lever-test ingredients (validator V8) with the Settings Panel defaults (P7), swept over
β0 (VALUE_WEIGHT) in {0.15, 0.30, 0.45} plus the shipped value, gourmet {0, 0.5, 1} and organic {0, 0.6, 1}, with
`choose_variant` exactly as the cart uses it. The gate is applied to each β0; the status is
the shipped β0's, read from settings (0.20 since C53; the first E12 run hard-coded 0.30). Deterministic: no model.
Run: .venv/bin/python scripts/benchmark/variants.py [--out DIR]
"""
import itertools

from _common import parser, save

from backend.catalogue.store import load_store
from backend.catalogue.validators import LEVER_TEST
from backend.config import load_settings
from backend.engine.context import build_context
from backend.engine.variants import choose_variant
from backend.evaluation.results import make_result
from backend.evaluation.variant_sweep import IngredientSweep, e12_gate
from backend.session.levers import LeverSet

BETAS = (0.15, 0.30, 0.45)
SHIPPED = load_settings().value_weight
SWEEP = tuple(sorted({*BETAS, SHIPPED}))
LEVELS = {"gourmet": (0.0, 0.5, 1.0), "organic": (0.0, 0.6, 1.0)}


def main():
    args = parser(__doc__).parse_args()
    store, ctx = load_store(), build_context(settings=load_settings(env={"CONTEXT_NOW": "2026-05-16T19:30:00"}, env_file=None))

    def pick(term, beta0, gourmet, organic):
        levers = LeverSet(gourmet_affinity=gourmet, artisanal_organic=organic)
        return choose_variant(term, levers, ctx, store, value_weight=beta0)

    grid, per, gates = {}, [], {}
    for label, term in LEVER_TEST.items():
        for beta0, g, o in itertools.product((0.0, *SWEEP), LEVELS["gourmet"], LEVELS["organic"]):
            c = pick(term, beta0, g, o)
            grid[(label, beta0, g, o)] = c
            per.append({"id": f"{label}|b{beta0}|g{g}|o{o}", "ingredient": label, "beta0": beta0, "gourmet": g, "organic": o,
                        "chosen": c.chosen.variant_id, "chosen_name": c.chosen.name, "beta": c.beta,
                        "organic_variant": c.chosen.attributes.get("organic") == "yes",
                        "premium_variant": c.chosen.attributes.get("premium") == "yes",
                        "eligible": len(c.scored)})
    for beta0 in SWEEP:
        rows = []
        for label in LEVER_TEST:
            ch = lambda g, o, b=beta0: grid[(label, b, g, o)]
            eligible = [v for v, _ in ch(0.5, 0.6).scored]
            cheapest = min(eligible, key=lambda v: v.price_per_unit_inr)
            rows.append(IngredientSweep(
                label,
                organic=(ch(0.5, 0.0).chosen.variant_id, ch(0.5, 1.0).chosen.variant_id),
                gourmet=(ch(0.0, 0.6).chosen.variant_id, ch(1.0, 0.6).chosen.variant_id),
                price=(grid[(label, 0.0, 0.0, 0.6)].chosen.variant_id, ch(0.0, 0.6).chosen.variant_id),
                organic_at_max_beta=ch(0.0, 1.0).chosen.attributes.get("organic") == "yes",
                has_organic=any(v.attributes.get("organic") == "yes" for v in eligible),
                cheapest_at_g0=ch(0.0, 0.6).chosen.price_per_unit_inr == cheapest.price_per_unit_inr,
                premium_at_g1=ch(1.0, 0.6).chosen.attributes.get("premium") == "yes"))
        gates[str(beta0)] = {**e12_gate(rows), "per_ingredient": [r.__dict__ for r in rows]}
    shipped = gates[str(SHIPPED)]
    rejected = [b for b, g in gates.items() if g["price_overrides_organic"]]
    metrics = {"gates_by_beta0": gates, "shipped_beta0": SHIPPED, "rejected_beta0": rejected}
    save(make_result("E12", "variant-sweep", "mock-data/generated/variants.json", "all", metrics, per, [],
                     shipped["status"], notes=f"gate applied to the shipped beta0 {SHIPPED} (from settings); the other values reported. Price effect = "
                     "choice at gourmet 0 with the value term off (beta0 0) vs on; defined before the run"), args.out, args.post_hoc)
    for b, g in gates.items():
        print(b, g["status"], {e: g[e]["k"] for e in ("organic", "gourmet", "price")}, "price_overrides_organic:",
              g["price_overrides_organic"], "cheapest@g0", g["cheapest_at_gourmet_0"]["k"], "premium@g1", g["premium_at_gourmet_1"]["k"])


if __name__ == "__main__":
    main()
