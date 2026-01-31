from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo


def date_key_for_timezone(tz_name: str) -> str:
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d")


def diff_days(start_date_key: str, date_key: str) -> int:
    start_date = date.fromisoformat(start_date_key)
    current_date = date.fromisoformat(date_key)
    return (current_date - start_date).days


def add_days(date_key: str, days: int) -> str:
    base = date.fromisoformat(date_key)
    return (base + timedelta(days=days)).strftime("%Y-%m-%d")


def date_key_for_day_index(start_date_key: str, day_index: int) -> str:
    return add_days(start_date_key, day_index - 1)
