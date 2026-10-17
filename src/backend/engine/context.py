"""Request context and trend multipliers (FR-67; Data Model §6.1, §6.2; C23).

Time and weather come from a Context built from the system clock, or from
CONTEXT_NOW / CONTEXT_WEATHER in config, never from the language model. A frozen
context gives identical trend effects (T-037). Weather labels are mock.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from backend.catalogue.seed import MOCK, DishRecord
from backend.config import Settings
from backend.session.levers import LeverSet

SEASON = {3: "summer", 4: "summer", 5: "summer", 6: "summer", 7: "monsoon", 8: "monsoon", 9: "monsoon",
          11: "winter", 12: "winter", 1: "winter", 2: "winter"}
SEASON_WEATHER = {"summer": "hot", "monsoon": "rain", "winter": "cool"}
FESTIVE_MONTHS = {10, 11}  # mock festive window (Navratri to Diwali)


@dataclass(frozen=True)
class Context:
    now: datetime
    day_type: str  # weekday | weekend
    part_of_day: str  # morning | lunch | afternoon | evening | night
    season: str | None
    weather: str | None  # hot | rain | cool (mock label)
    festive: bool


def _part_of_day(hour: int) -> str:
    if 5 <= hour < 11:
        return "morning"
    if 11 <= hour < 15:
        return "lunch"
    if 15 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 22:
        return "evening"
    return "night"


def build_context(now: datetime | None = None, weather: str | None = None, settings: Settings | None = None) -> Context:
    if now is None and settings is not None and settings.context_now:
        now = datetime.fromisoformat(settings.context_now)
    now = now or datetime.now()
    if weather is None and settings is not None and settings.context_weather:
        weather = settings.context_weather
    season = SEASON.get(now.month)
    return Context(
        now=now,
        day_type="weekend" if now.weekday() >= 5 else "weekday",
        part_of_day=_part_of_day(now.hour),
        season=season,
        weather=weather or SEASON_WEATHER.get(season or ""),
        festive=now.month in FESTIVE_MONTHS,
    )


@lru_cache(maxsize=4)
def load_trends(path: Path = MOCK / "trends.csv") -> tuple[dict, ...]:
    with open(path, newline="") as fh:
        return tuple({**r, "multiplier": float(r["multiplier"])} for r in csv.DictReader(fh))


def _when_matches(when: str, ctx: Context) -> bool:
    if when == "festive_season":
        return ctx.festive
    if when == "navratri":
        return ctx.festive and ctx.now.month in {9, 10}
    if when == "new_year_health":
        return ctx.now.month == 1
    for token in when.split("_"):
        if token in {"weekday", "weekend"} and token != ctx.day_type:
            return False
        if token in {"morning", "lunch", "afternoon", "evening", "night"} and token != ctx.part_of_day:
            return False
        if token in {"summer", "monsoon", "winter"} and token != ctx.season:
            return False
    return True


def _condition_matches(condition: str, ctx: Context) -> bool:
    return condition == "any" or {"cold": "cool"}.get(condition, condition) == ctx.weather


def matching_trends(rec: DishRecord, ctx: Context, trends: tuple[dict, ...]) -> list[dict]:
    d = rec.dish
    targets = {d.dish_id, d.course, *d.mood_tags}
    return [r for r in trends if r["boost_dish_or_mood"] in targets
            and _when_matches(r["when"], ctx) and _condition_matches(r["condition"], ctx)]


def trend_multiplier(rec: DishRecord, ctx: Context, trends: tuple[dict, ...], levers: LeverSet) -> float:
    """Product of matching rows' m_eff = 1 + L × (m − 1); L is the row group's trend slider (1 for `none`)."""
    slider = {"indulgence": levers.trends.weekend_indulgence, "cooling": levers.trends.cooling_drinks}
    m = 1.0
    for r in matching_trends(rec, ctx, trends):
        m *= 1 + slider.get(r["group"], 1.0) * (r["multiplier"] - 1)
    return m
