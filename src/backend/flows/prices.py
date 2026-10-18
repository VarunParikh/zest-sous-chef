"""Reply price gate (FR-79; AC-14; Agent Design §5 step 6).

Every rupee amount in a reply must equal the catalogue value. An amount within
30 characters after a known item name (or "total" / "subtotal") is replaced by
the catalogue value; any other amount is removed, never shown unverified.
"""
from __future__ import annotations

import re

AMOUNT = re.compile(r"(?:₹|\bRs\.?)\s?(\d[\d,]*)")
WINDOW = 30


def correct_prices(text: str, known: dict[str, int]) -> tuple[str, list[tuple]]:
    names = sorted(known, key=len, reverse=True)
    fixes, out, last = [], [], 0
    for m in AMOUNT.finditer(text):
        shown = int(m.group(1).replace(",", ""))
        before = text[max(0, m.start() - WINDOW - 40):m.start()].lower()
        name, best = None, -1
        for n in names:  # the nearest known name ending within the window before the amount
            i = before.rfind(n.lower())
            if i >= 0 and len(before) - (i + len(n)) <= WINDOW and i > best:
                name, best = n, i
        out.append(text[last:m.start()])
        if name is None:
            fixes.append((None, shown, None))
            out.append("")
        else:
            if shown != known[name]:
                fixes.append((name, shown, known[name]))
            out.append(f"₹{known[name]}")
        last = m.end()
    out.append(text[last:])
    result = "".join(out)
    if any(f[0] is None for f in fixes):
        result = re.sub(r"\s+([.!?,])", r"\1", re.sub(r"\s{2,}", " ", result)).strip()
    return result, fixes
