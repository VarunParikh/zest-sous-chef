"""Seed consistency checks (draft of validators V1-V3). Run: python3 mock-data/check_seed.py"""
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
        t, q, u = it.split(":")
        t = alias.get(t, t)
        if t not in lex:
            missing.setdefault(t, []).append(d["dish_id"]); continue
        f = lex[t]["diet_class_floor"]
        if rank[f] > rank[worst]: worst = f
    if worst != d["claimed_diet"]:
        bad.append((d["dish_id"], d["name"], d["claimed_diet"], worst))
print(f"dishes: {len(dishes)}  lexicon terms: {len(lex)}")
print("missing terms:", len(missing)); [print("  ", t, v) for t, v in sorted(missing.items())]
print("diet mismatches:", len(bad)); [print("  ", b) for b in bad]
sys.exit(1 if missing or bad else 0)
