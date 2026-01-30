from datetime import datetime, date
from zoneinfo import ZoneInfo


def date_key_for_timezone(tz_name: str) -> str:
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d")


def diff_days(start_date_key: str, date_key: str) -> int:
    start_date = date.fromisoformat(start_date_key)
    current_date = date.fromisoformat(date_key)
    return (current_date - start_date).days
