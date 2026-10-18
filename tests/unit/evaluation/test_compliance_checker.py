"""E7 independent checker (Evaluation Plan §4 E7; Data Model §9). The canaries prove the checker can fail."""
import ast
from pathlib import Path

from backend.evaluation.compliance import load_variants, violations
from backend.session.levers import LeverSet

V = load_variants()
PERSONA = {
    "pure_veg": LeverSet(diet="Pure Veg (Strict)").model_dump(),
    "jain": LeverSet(diet="Jain (No Root Veggies / Pure Veg)", faith="Jain (Strict Root-Free)").model_dump(),
    "halal": LeverSet(faith="Muslim (Strict Halal Only)").model_dump(),
    "vegan": LeverSet(diet="Pure Veg (Strict)", specialized_diets=["Vegan"]).model_dump(),
    "default": LeverSet().model_dump(),
}


def named(text):
    return next(v for v in V.values() if v["name"].lower().startswith(text.lower()))


def test_checker_never_imports_the_engine_eligibility():
    tree = ast.parse(Path("src/backend/evaluation/compliance.py").read_text())
    mods = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | \
           {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not any(m and m.startswith("backend.engine") for m in mods)


def test_forbidden_items_per_persona():
    chicken, onion, paneer, pork, wine, honey = (named("Chicken (") , named("Onion ("), named("Paneer ("),
                                                  named("Pork ("), named("Wine ("), named("Honey ("))
    assert violations(chicken, PERSONA["pure_veg"]) and violations(chicken, PERSONA["jain"])
    assert violations(onion, PERSONA["jain"]) and not violations(onion, PERSONA["pure_veg"])
    assert violations(paneer, PERSONA["vegan"]) and not violations(paneer, PERSONA["jain"])
    assert violations(pork, PERSONA["halal"]) and violations(wine, PERSONA["halal"])
    assert violations(honey, PERSONA["vegan"]) and not violations(honey, PERSONA["jain"])  # §9: honey allowed for Jain
    assert not any(violations(v, PERSONA["default"]) for v in (chicken, onion, pork, wine))


def test_canary_mis_tagged_variant_is_caught_by_keywords():
    fake = {**named("Tofu ("), "name": "Tofu (Firm)", "ingredient_list": ["tofu", "chicken stock"]}  # tags still say vegan
    assert fake["vegan"] and violations(fake, PERSONA["vegan"]) and violations(fake, PERSONA["pure_veg"])


def test_plant_products_are_not_flagged():
    for name in ("Plant milk (Soy)", "Peanut butter (Creamy)", "Garam masala (No onion no garlic)"):
        v = next(x for x in V.values() if x["name"] == name)
        assert not violations(v, PERSONA["vegan"] if "milk" in name or "butter" in name else PERSONA["jain"]), name
