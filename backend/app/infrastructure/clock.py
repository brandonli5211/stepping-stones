"""Clocks for the Clock port, and DEMO_TODAY parsing. Read only by the composition root (app.main)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone

from app.application.ports import Clock


class SystemClock:
    """The real current time, in UTC."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


@dataclass(frozen=True)
class FixedClock:
    """Always the same instant (the demo "today")."""

    instant: datetime

    def now(self) -> datetime:
        return self.instant


def parse_demo_today(value: str) -> datetime:
    """An ISO 8601 date-time with a UTC offset, returned in UTC. Anything else raises ValueError naming the value."""
    message = f"DEMO_TODAY={value} is not an ISO 8601 date-time with a UTC offset"
    try:
        parsed = datetime.fromisoformat(value.strip())
    except ValueError:
        raise ValueError(message) from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(message)
    return parsed.astimezone(timezone.utc)


def clock_from_env(environ: Mapping[str, str]) -> Clock:
    """FixedClock at DEMO_TODAY when it is set and non-blank, else SystemClock."""
    value = (environ.get("DEMO_TODAY") or "").strip()
    return FixedClock(parse_demo_today(value)) if value else SystemClock()
