"""Shared local-time and alternating-week rules for views and reminders."""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def local_now(user, now=None):
    try:
        zone = ZoneInfo(user.timezone)
    except (ZoneInfoNotFoundError, ValueError):
        zone = ZoneInfo("UTC")
    return (now or datetime.now(timezone.utc)).astimezone(zone)


def week_parity(day, offset=0):
    return "numerator" if (day.isocalendar().week + offset) % 2 else "denominator"


def lesson_occurs(lesson, day, user):
    return lesson.day_of_week == day.isoweekday() and lesson.parity in (
        "all",
        week_parity(day, user.week_parity_offset),
    )
