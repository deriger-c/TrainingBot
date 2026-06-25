from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def now_local(timezone_name: str) -> datetime:
    return datetime.now(ZoneInfo(timezone_name))


def today_iso(timezone_name: str) -> str:
    return now_local(timezone_name).strftime("%Y-%m-%d")


def current_time_hhmm(timezone_name: str) -> str:
    return now_local(timezone_name).strftime("%H:%M")


def current_timestamp(timezone_name: str) -> str:
    return now_local(timezone_name).strftime("%Y-%m-%d %H:%M:%S")


def make_session_id(workout_type: str, timezone_name: str) -> str:
    return f"{now_local(timezone_name).strftime('%Y%m%d-%H%M')}-{workout_type}"


def minutes_between(start_hhmm: str, end_hhmm: str, timezone_name: str) -> int:
    today = today_iso(timezone_name)
    start = datetime.fromisoformat(f"{today}T{start_hhmm}:00").replace(tzinfo=ZoneInfo(timezone_name))
    end = datetime.fromisoformat(f"{today}T{end_hhmm}:00").replace(tzinfo=ZoneInfo(timezone_name))
    minutes = int((end - start).total_seconds() // 60)
    return max(minutes, 0)
