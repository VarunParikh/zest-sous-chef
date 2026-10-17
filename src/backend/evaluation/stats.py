"""Proportions with Wilson 95% intervals (Evaluation Plan §2.5; Wilson 1927)."""
from __future__ import annotations

import math

Z = 1.959964


def wilson(k: int, n: int, z: float = Z) -> tuple[float, float] | None:
    if n == 0:
        return None
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def proportion(k: int, n: int) -> dict:
    ci = wilson(k, n)
    return {"k": k, "n": n, "rate": (k / n) if n else None, "ci95": list(ci) if ci else None}
