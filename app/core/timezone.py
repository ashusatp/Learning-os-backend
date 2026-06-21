from datetime import datetime, timezone, timedelta

from zoneinfo import ZoneInfo

from app.core.config import configs

USER_TZ = ZoneInfo(configs.TIMEZONE)


def now_in_user_tz() -> datetime:
    """Current time in user's timezone (tz-aware)."""
    return datetime.now(timezone.utc).astimezone(USER_TZ)


def today_start_utc() -> datetime:
    """Start of today (00:00) in user's timezone, converted to UTC."""
    local_now = now_in_user_tz()
    local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return local_start.astimezone(timezone.utc)


def today_end_utc() -> datetime:
    """End of today (23:59:59) in user's timezone, converted to UTC."""
    local_now = now_in_user_tz()
    local_end = local_now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return local_end.astimezone(timezone.utc)


def yesterday_start_utc() -> datetime:
    """Start of yesterday (00:00) in user's timezone, converted to UTC."""
    local_now = now_in_user_tz()
    local_yesterday = (local_now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return local_yesterday.astimezone(timezone.utc)


def yesterday_end_utc() -> datetime:
    """End of yesterday (23:59:59) in user's timezone, converted to UTC."""
    local_now = now_in_user_tz()
    local_yesterday = (local_now - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
    return local_yesterday.astimezone(timezone.utc)


def to_user_date(utc_dt: datetime):
    """Convert a UTC datetime to a date in user's timezone."""
    return utc_dt.astimezone(USER_TZ).date()
