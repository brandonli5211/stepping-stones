import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI

from app.infrastructure.clock import FixedClock, SystemClock, clock_from_env, parse_demo_today
from app.main import configure_clock

DEMO = datetime(2026, 10, 9, 23, 59, 59, tzinfo=timezone.utc)
_BACKEND = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("value", ["2026-10-09T23:59:59+00:00", "2026-10-09T23:59:59Z", " 2026-10-09T19:59:59-04:00 "])
def test_parse_demo_today_accepts_offsets_and_returns_utc(value):
    parsed = parse_demo_today(value)
    assert parsed == DEMO
    assert parsed.utcoffset() == timedelta(0)


@pytest.mark.parametrize("value", ["2026-10-09T23:59:59", "2026-10-09", "tomorrow", ""])
def test_parse_demo_today_rejects_missing_offset_or_garbage(value):
    with pytest.raises(ValueError, match=f"DEMO_TODAY={value} is not an ISO 8601 date-time with a UTC offset"):
        parse_demo_today(value)


def test_system_clock_is_aware_utc_and_current():
    before = datetime.now(timezone.utc)
    now = SystemClock().now()
    assert now.tzinfo is not None and now.utcoffset() == timedelta(0)
    assert before <= now <= datetime.now(timezone.utc)


def test_fixed_clock_returns_instant():
    assert FixedClock(DEMO).now() == DEMO


def test_clock_from_env():
    assert isinstance(clock_from_env({}), SystemClock)
    assert isinstance(clock_from_env({"DEMO_TODAY": "   "}), SystemClock)
    assert clock_from_env({"DEMO_TODAY": "2026-10-09T23:59:59+00:00"}) == FixedClock(DEMO)
    with pytest.raises(ValueError):
        clock_from_env({"DEMO_TODAY": "2026-10-09T23:59:59"})


def test_configure_clock_sets_app_state():
    app = FastAPI()
    configure_clock(app, {})
    assert isinstance(app.state.clock, SystemClock)
    configure_clock(app, {"DEMO_TODAY": "2026-10-09T23:59:59+00:00"})
    assert app.state.clock == FixedClock(DEMO)
    with pytest.raises(ValueError):
        configure_clock(FastAPI(), {"DEMO_TODAY": "bad"})


def test_main_app_has_a_clock_after_import():
    import app.main

    assert hasattr(app.main.app.state, "clock")


def test_bad_demo_today_stops_main_from_importing():
    env = {**os.environ, "DEMO_TODAY": "2026-10-09T23:59:59"}
    proc = subprocess.run([sys.executable, "-c", "import app.main"], cwd=_BACKEND, env=env,
                          capture_output=True, text=True, check=False)
    assert proc.returncode != 0
    assert "DEMO_TODAY=2026-10-09T23:59:59 is not an ISO 8601 date-time with a UTC offset" in proc.stderr
