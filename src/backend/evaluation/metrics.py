"""Structural metrics only (Evaluation Plan §2.3): no model grades a model."""
from __future__ import annotations


def recall_at(ranked: list[str], relevant: set[str], k: int) -> float:
    """1.0 if any relevant item is in the top k (a hit), else 0.0."""
    return 1.0 if relevant & set(ranked[:k]) else 0.0


def mrr(ranked: list[str], relevant: set[str]) -> float:
    for i, item in enumerate(ranked, start=1):
        if item in relevant:
            return 1.0 / i
    return 0.0


def f1(predicted: set[str], expected: set[str]) -> float:
    if not predicted and not expected:
        return 1.0
    tp = len(predicted & expected)
    if tp == 0:
        return 0.0
    precision, recall = tp / len(predicted), tp / len(expected)
    return 2 * precision * recall / (precision + recall)
