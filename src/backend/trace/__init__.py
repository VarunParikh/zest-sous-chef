"""Local JSONL trace (US-35; NFR-06; data model §11; security note S-07).

One line per event: `ts`, `session_id`, `event`, `data`. Only the events in the
data model are accepted. Every string is cut to 120 characters, and bytes,
data URIs and base64 runs are replaced, so no image and no long user text
ever reaches the file. The file lives in the git-ignored `logs/` folder.
"""
from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EVENTS = frozenset({
    "session_started", "lever_snapshot_applied", "intent_classified", "retrieval_candidates",
    "guardrail_filtered", "llm_call", "suggestion_shown", "suggestion_accepted",
    "suggestion_dismissed", "cart_mutated", "fallback_used", "checkout_placed",
})
MAX_TEXT = 120
REMOVED = "[removed]"
_BASE64_RUN = re.compile(r"[A-Za-z0-9+/=_-]{64,}")


def _looks_encoded(value: str) -> bool:
    """A long run mixing upper, lower and digits: base64-like payload, not prose."""
    return any(
        re.search(r"[A-Z]", run) and re.search(r"[a-z]", run) and re.search(r"[0-9]", run)
        for run in _BASE64_RUN.findall(value)
    )


def _clean(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray, memoryview)):
        return REMOVED
    if isinstance(value, str):
        if value.startswith("data:") or _looks_encoded(value):
            return REMOVED
        return value[:MAX_TEXT]
    if isinstance(value, dict):
        return {str(k)[:MAX_TEXT]: _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_clean(v) for v in value]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _clean(str(value))


class Tracer:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def emit(self, event: str, session_id: str | None, **data: Any) -> None:
        if event not in EVENTS:
            raise ValueError(f"unknown trace event: {event!r}")
        record = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "session_id": _clean(session_id),
            "event": event,
            "data": _clean(data),
        }
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
