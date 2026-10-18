"""Seed consistency checks (draft of validators V1-V3; superseded by validate.py, kept as a cross-check). Run: python3 mock-data/check_seed.py
Ingredient items are term:qty:unit, with an optional fourth field `opt` for non-essential lines."""
import csv, sys, pathlib
here = pathlib.Path(__file__).parent
lex = {r["term"]: r for r in csv.DictReader(open(here/"ingredient_lexicon.csv"))}
alias = {a: t for t, r in lex.items() for a in (r["aliases"].split("|") if r["aliases"] else [])}
rank = {"vegan": 0, "vegetarian": 1, "egg": 2, "non_veg": 3}
missing, bad = {}, []
dishes = list(csv.DictReader(open(here/"dishes.csv")))
for d in dishes:
    worst = "vegan"
    for it in d["ingredients"].split(";"):
        t = it.split(":")[0]
        t = alias.get(t, t)
        if t not in lex:
            missing.setdefault(t, []).append(d["dish_id"]); continue
        f = lex[t]["diet_class_floor"]
        if rank[f] > rank[worst]: worst = f
    if worst != d["claimed_diet"]:
        bad.append((d["dish_id"], d["name"], d["claimed_diet"], worst))
import glob
cat = set()
for f in glob.glob(str(here/"taxonomy"/"0*.txt")):
    for line in open(f):
        if not line.strip(): continue
        b = line.strip().split("|"); cat.add(alias.get(b[3], b[3]))
        for v in b[7].split(";"):
            for e in v.split("~")[1].split(","):
                e = e.strip().lstrip("!")  # `!term` replaces the base term (C68)
                if e and not e.startswith("="): cat.add(alias.get(e, e))
UNAVAILABLE_BY_DESIGN = {"D35": {"sushi rice", "nori", "wasabi"}}
uncovered = []
for d in dishes:
    for it in d["ingredients"].split(";"):
        t = alias.get(it.split(":")[0], it.split(":")[0])
        if t not in cat and t not in UNAVAILABLE_BY_DESIGN.get(d["dish_id"], set()):
            uncovered.append((d["dish_id"], t))
print("dish ingredients with no catalogue product (excluding by-design gaps):", len(uncovered)); [print("  ", u) for u in uncovered]
print(f"dishes: {len(dishes)}  lexicon terms: {len(lex)}")
print("missing terms:", len(missing)); [print("  ", t, v) for t, v in sorted(missing.items())]
print("diet mismatches:", len(bad)); [print("  ", b) for b in bad]
sys.exit(1 if missing or bad or uncovered else 0)
