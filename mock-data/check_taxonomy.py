"""Taxonomy validator (draft of V1-V4): terms exist, variants unique by ingredient list, counts. Run: python3 mock-data/check_taxonomy.py"""
import csv, glob, pathlib, sys, collections
here = pathlib.Path(__file__).parent
lex = {r["term"]: r for r in csv.DictReader(open(here/"ingredient_lexicon.csv"))}
alias = {a: t for t, r in lex.items() for a in (r["aliases"].split("|") if r["aliases"] else [])}
rank = {"vegan":0,"vegetarian":1,"egg":2,"non_veg":3}
INV = {v:k for k,v in rank.items()}
def floor(items):
    w = 0
    for i, t in enumerate(items):
        if t.startswith("=") or t == "-": continue
        r = lex[alias.get(t, t)]
        if i == 0 and "variants decide" in r["notes"]: continue  # base term floor ignored; extras decide
        w = max(w, rank[r["diet_class_floor"]])
    return INV[w]
claims = collections.Counter(); contradictions = []
missing = collections.defaultdict(list); dup = []; nb = nv = 0; ids = set()
for f in sorted(glob.glob(str(here/"taxonomy"/"0*.txt"))):
    for line in open(f):
        line = line.strip()
        if not line: continue
        bid, cat, name, term, unit, packs, ppu, variants = line.split("|")
        if bid in ids: print("duplicate base id", bid)
        ids.add(bid); nb += 1
        seen = {}
        for v in variants.split(";"):
            vn, extras, mult, flags = v.split("~"); nv += 1
            items = [term] + [e.strip() for e in extras.split(",") if e.strip()]
            for t in items:
                if t.startswith("=") or t == "-": continue
                t2 = alias.get(t, t)
                if t2 not in lex: missing[t2].append(bid)
            fl = floor(items)
            nm = vn.lower()
            if ("vegan" in nm or "plant" in nm or "dairy-free" in nm) and fl != "vegan": contradictions.append((bid, vn, "named vegan but derives " + fl))
            if ("vegetarian" in nm or "eggless" in nm) and rank[fl] > 1: contradictions.append((bid, vn, "named veg/eggless but derives " + fl))
            key = tuple(sorted(items)) + (('organic',) if 'o' in flags else ())
            if key in seen: dup.append((bid, vn, seen[key]))
            seen[key] = vn
print(f"base products: {nb}  variants: {nv}")
print("missing terms:", len(missing)); [print("  ", t, sorted(set(b))[:4]) for t, b in sorted(missing.items())]
print("duplicate ingredient lists within a base:", len(dup)); [print("  ", d) for d in dup]
print("name-vs-ingredients contradictions:", len(contradictions)); [print("  ", c) for c in contradictions]
sys.exit(1 if missing or dup or contradictions else 0)
