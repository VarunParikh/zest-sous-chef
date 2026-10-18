"""C50: problems in a shown reason line (E13), checked separately from the app's reason validator.

A shown reason fails when it mentions a price or stock, makes a health or medical claim from a
fixed list, or names a catalogue ingredient term that is not an ingredient of the dish.
"""
from __future__ import annotations

import re

from backend.catalogue.seed import Lexicon

PRICE_OR_STOCK = re.compile(r"₹|\brs\.?\b|\binr\b|rupee|\bprice|\bcost|\bcheap|\bdiscount|\boffer\b|\bstock\b|\bsku\b|"
                            r"\bonly \d+|\bleft\b.*\b(in )?stock", re.I)
CLAIMS = ("healthy", "healthier", "cure", "cures", "heal", "immunity", "detox", "weight loss", "low calorie", "low-calorie",
          "nutritious", "medicinal", "diabetic")


def shown_reason_problems(reason: str, dish_terms: set[str], lexicon: Lexicon) -> list[str]:
    text = reason.lower()
    out = []
    if PRICE_OR_STOCK.search(text):
        out.append(f"price_or_stock:{PRICE_OR_STOCK.search(text).group(0)}")
    out += [f"claim:{c}" for c in CLAIMS if re.search(rf"\b{re.escape(c)}\b", text)]
    names = {t: t for t in lexicon.entries} | {a: e.term for e in lexicon.entries.values() for a in e.aliases}
    for name, term in names.items():
        if len(name) > 2 and term not in dish_terms and re.search(rf"\b{re.escape(name)}s?\b", text):
            out.append(f"ingredient:{term}")
    return sorted(set(out), key=out.index)
