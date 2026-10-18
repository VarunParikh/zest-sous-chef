"""Mood flow (block 2.3 next commit)."""
from __future__ import annotations


def mood_turn(session, text, result, deps, out) -> None:
    from backend.flows.chat import say

    out.messages.append(say(session, "MSG-UNSUPPORTED"))
