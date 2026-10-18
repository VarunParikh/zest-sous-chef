"""Sessions in memory (Data Model §8.2; FR-01, FR-02; ADR-007).

A session holds a deep copy of the levers taken at creation. Reads return a
fresh copy, so nothing outside can change it, and the engine is only ever
called with that snapshot (`Session.recommend_dishes`). The server keeps no
other lever state: the client owns the panel (API Spec §1).
"""
from __future__ import annotations

import secrets
import threading
from collections.abc import Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone

from backend.cart.models import Cart
from backend.session.levers import LeverSet, persona_label, snapshot_hash


class SessionNotFound(LookupError):
    pass


class SessionBusy(RuntimeError):
    """Another turn or cart change is in progress for this session (FR-102)."""


@dataclass
class Session:
    session_id: str
    _snapshot: LeverSet
    snapshot_hash: str
    persona_label: str
    created_at: datetime
    messages: list = field(default_factory=list)
    cart: Cart = field(default_factory=Cart)
    pending: dict = field(default_factory=dict)  # confirm and substitution ids awaiting a tap
    undo_stack: list = field(default_factory=list)
    suggestions: dict = field(default_factory=dict)  # suggestion_id -> record
    orders: dict = field(default_factory=dict)  # idempotency key -> Order
    videos: dict = field(default_factory=dict)  # youtube id -> cart_dish_id (FR-24 duplicates)
    photo_consent: bool = False  # opt-in Gemini notice accepted (FR-50)
    open_dish_id: str | None = None  # the text recipe dish still taking ingredients (FR-30)
    last_addon: object = None  # {anchor, rec} of the latest add-on suggestion (FR-119)
    last_recommendation: object = None  # pool, scores and inspector rows of the latest suggestion (FR-115)
    _turns: int = 0
    _messages: int = 0
    _ids: dict = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @property
    def snapshot(self) -> LeverSet:
        return self._snapshot.model_copy(deep=True)

    def next_turn_id(self) -> str:
        self._turns += 1
        return f"t_{self._turns:04d}"

    def next_message_id(self) -> str:
        self._messages += 1
        return f"m_{self._messages}"

    def next_id(self, prefix: str) -> str:
        """Session-scoped ids: cd_1, l_1, sg_1, ..."""
        self._ids[prefix] = self._ids.get(prefix, 0) + 1
        return f"{prefix}_{self._ids[prefix]}"

    @contextmanager
    def busy(self):
        """Non-blocking per-session lock: a second mutation while one runs raises SessionBusy (FR-102)."""
        if not self._lock.acquire(blocking=False):
            raise SessionBusy(self.session_id)
        try:
            yield self
        finally:
            self._lock.release()

    def recommend_dishes(self, query: str, ctx, store, retriever, tracer=None, display: int = 3):
        """FR-02: the engine sees this session's snapshot and nothing else."""
        from backend.engine.recommend import recommend_dishes

        return recommend_dishes(query, self.snapshot, ctx, store, retriever, tracer, self.session_id, display)


class SessionStore:
    def __init__(self, tracer=None, presets: Mapping[str, LeverSet] | None = None):
        self._sessions: dict[str, Session] = {}
        self._tracer = tracer
        self._presets = presets or {}

    def __len__(self) -> int:
        return len(self._sessions)

    def create(self, levers: LeverSet) -> Session:
        snap = LeverSet.model_validate(levers.model_dump())
        sid = f"s_{secrets.token_hex(8)}"
        s = Session(sid, snap, snapshot_hash(snap), persona_label(snap, self._presets), datetime.now(timezone.utc))
        self._sessions[sid] = s
        if self._tracer is not None:
            self._tracer.emit("session_started", sid)
            self._tracer.emit("lever_snapshot_applied", sid, snapshot_hash=s.snapshot_hash, persona_label=s.persona_label)
        return s

    def get(self, session_id: str) -> Session:
        try:
            return self._sessions[session_id]
        except KeyError:
            raise SessionNotFound(session_id) from None

    def delete(self, session_id: str) -> None:
        if self._sessions.pop(session_id, None) is None:
            raise SessionNotFound(session_id)
