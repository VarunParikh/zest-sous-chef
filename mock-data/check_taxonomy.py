"""Taxonomy validator (draft of V1-V4): terms exist, variants unique by ingredient list, counts. Run: python3 mock-data/check_taxonomy.py"""
import csv, glob, pathlib, sys, collections
here = pathlib.Path(__file__).parent
lex = {r["term"]: r for r in csv.DictReader(open(here/"ingredient_lexicon.csv"))}
alias = {a: t for t, r in lex.items() for a in (r["aliases"].split("|") if r["aliases"] else [])}
rank = {"vegan":0,"vegetarian":1,"egg":2,"non_veg":3}
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
            key = tuple(sorted(items)) + (('organic',) if 'o' in flags else ())
            if key in seen: dup.append((bid, vn, seen[key]))
            seen[key] = vn
print(f"base products: {nb}  variants: {nv}")
print("missing terms:", len(missing)); [print("  ", t, sorted(set(b))[:4]) for t, b in sorted(missing.items())]
print("duplicate ingredient lists within a base:", len(dup)); [print("  ", d) for d in dup]
sys.exit(1 if missing or dup else 0)
