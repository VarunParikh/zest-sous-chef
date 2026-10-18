"""Transcript chain for YouTube links (FR-20, 22, 24; API Spec §6.3; `mock-data/transcripts/index.json`).

Order: live fetch (`youtube-transcript-api`, when `LIVE_TRANSCRIPTS` is on and within
`TIMEOUT_TRANSCRIPT_S`), then the own-written fixture for that video id, then the video
title saved in `mock-data/videos.json`; otherwise `TranscriptUnavailable` (the paste prompt).
The returned text is data: the caller screens it with the guard and spotlights it.
"""
from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
from pathlib import Path

from backend.catalogue.seed import MOCK

TRANSCRIPTS = MOCK / "transcripts"
URL = re.compile(r"(?:https?://|www\.)\S+", re.I)
YOUTUBE = re.compile(
    r"^(?:https?://)?(?:(?:www\.|m\.)?youtube\.com/watch\?(?:\S*?&)?v=|youtu\.be/)([A-Za-z0-9_-]{11})(?:[&?#/]\S*)?$", re.I)
TIMESTAMP = re.compile(r"\[?\(?\b\d{1,2}:\d{2}(?::\d{2})?\b\)?\]?")
NOISE = re.compile(r"\b(sponsor\w*|subscribe|use code|link in (the )?description|like and share|hit the bell)\b", re.I)


class TranscriptUnavailable(LookupError):
    pass


@dataclass(frozen=True)
class Transcript:
    source: str  # live | fixture | title
    text: str
    title: str | None
    video_id: str


def find_url(text: str) -> str | None:
    m = URL.search(text)
    return m.group(0) if m else None


def video_id(text: str) -> str | None:
    """Only youtube.com/watch and youtu.be links count (FR-24)."""
    url = find_url(text)
    m = YOUTUBE.match(url.rstrip(".,!?)")) if url else None
    return m.group(1) if m else None


def clean(text: str, cap: int) -> str:
    """Drop timestamps and sponsor or subscribe lines, then cap the length (Agent Design §4)."""
    kept = []
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", text):
        if not sentence.strip() or sentence.lstrip().startswith("[") and sentence.rstrip().endswith("]"):
            continue
        if NOISE.search(sentence):
            continue
        kept.append(TIMESTAMP.sub("", sentence).strip())
    return re.sub(r"\s+", " ", " ".join(s for s in kept if s)).strip()[:cap]


def live_fetch(video: str, timeout: float) -> str:
    from youtube_transcript_api import YouTubeTranscriptApi

    fetched = YouTubeTranscriptApi().fetch(video, languages=["en", "en-IN", "hi"])
    return " ".join(s.text for s in fetched)


def _fixture_text(path: Path) -> str:
    lines = path.read_text().splitlines()
    body = [ln for ln in lines if not ln.startswith("[OWN-WRITTEN") and not re.match(r"^Video V\d+ \(", ln)]
    return "\n".join(body)


class TranscriptChain:
    def __init__(self, live=None, fixtures: dict[str, Path] | None = None, titles: dict[str, str] | None = None,
                 timeout_s: float = 10, cap: int = 6000):
        self.live, self.fixtures, self.titles = live, fixtures or {}, titles or {}
        self.timeout_s, self.cap = timeout_s, cap

    def _live(self, vid: str) -> str | None:
        if self.live is None:
            return None
        pool = ThreadPoolExecutor(max_workers=1)
        try:
            return pool.submit(self.live, vid, self.timeout_s).result(timeout=self.timeout_s)
        except FutureTimeout:
            return None
        except Exception:  # noqa: BLE001  any live failure falls through to the fixture (FR-20)
            return None
        finally:
            pool.shutdown(wait=False, cancel_futures=True)

    def fetch(self, vid: str) -> Transcript:
        title = self.titles.get(vid)
        text = self._live(vid)
        if text and clean(text, self.cap):
            return Transcript("live", clean(text, self.cap), title, vid)
        if vid in self.fixtures:
            return Transcript("fixture", clean(_fixture_text(self.fixtures[vid]), self.cap), title, vid)
        if title:
            return Transcript("title", clean(title, self.cap), title, vid)
        raise TranscriptUnavailable(vid)


def default_chain(live=live_fetch, fixtures: dict | None = None, titles: dict | None = None, timeout_s: float = 10,
                  cap: int = 6000) -> TranscriptChain:
    if fixtures is None:
        index = json.loads((TRANSCRIPTS / "index.json").read_text())["fixtures"]
        fixtures = {vid: TRANSCRIPTS / f["file"] for vid, f in index.items()}
    if titles is None:
        titles = {v["youtube_id"]: v["title"] for v in json.loads((MOCK / "videos.json").read_text())["videos"]}
    return TranscriptChain(live, fixtures, titles, timeout_s, cap)
