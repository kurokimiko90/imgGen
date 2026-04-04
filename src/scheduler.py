"""
src/scheduler.py - Scheduled time calculation for LevelUp content publishing.

Assigns scheduled_time to Content objects based on account publish_time
and optional interval between posts.
"""

from copy import replace as dc_replace
from dataclasses import replace
from datetime import date, datetime, timedelta
from typing import Optional

from src.content import Content


def calculate_scheduled_time(
    publish_time: str,
    base_date: Optional[date] = None,
) -> datetime:
    """Return the next available publish datetime for *publish_time* (HH:MM).

    If *base_date* is None, defaults to tomorrow.
    If the resulting datetime is in the past, it is rolled to the next day.

    Raises:
        ValueError: If *publish_time* is not in HH:MM format.
    """
    try:
        hour, minute = publish_time.split(":")
        hour, minute = int(hour), int(minute)
    except (ValueError, AttributeError) as exc:
        raise ValueError(
            f"Invalid publish_time format '{publish_time}'. Expected HH:MM."
        ) from exc

    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(
            f"Invalid publish_time values in '{publish_time}'. "
            "Hour must be 0-23, minute 0-59."
        )

    today = date.today()
    target_date = base_date if base_date is not None else today + timedelta(days=1)
    scheduled = datetime(target_date.year, target_date.month, target_date.day, hour, minute)

    # If in the past, roll forward until it's in the future
    while scheduled <= datetime.now():
        scheduled += timedelta(days=1)

    return scheduled


def assign_scheduled_times(
    contents: list[Content],
    publish_time: str,
    base_date: Optional[date] = None,
    interval_minutes: int = 60,
) -> list[Content]:
    """Assign scheduled_time to each Content in *contents*.

    Each item is offset by *interval_minutes* from the previous one.
    Returns a new list of Content objects (original objects are not mutated).
    """
    first_time = calculate_scheduled_time(publish_time, base_date)
    result: list[Content] = []
    for i, content in enumerate(contents):
        scheduled = first_time + timedelta(minutes=interval_minutes * i)
        result.append(replace(content, scheduled_time=scheduled))
    return result
