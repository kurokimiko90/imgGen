"""tests/test_scheduler.py — Unit tests for src/scheduler.py"""

from datetime import date, datetime, timedelta

import pytest

from src.content import AccountType, Content, ContentStatus
from src.scheduler import assign_scheduled_times, calculate_scheduled_time


def make_content(n: int) -> Content:
    return Content(
        id=str(n),
        account_type=AccountType.A,
        status=ContentStatus.PENDING_REVIEW,
        title=f"標題 {n}",
        body="內文",
    )


def test_calculate_scheduled_time_basic():
    future_date = date.today() + timedelta(days=10)
    result = calculate_scheduled_time("09:00", base_date=future_date)
    assert result.hour == 9
    assert result.minute == 0
    assert result.date() == future_date


def test_calculate_scheduled_time_defaults_to_tomorrow():
    result = calculate_scheduled_time("23:59")
    tomorrow = date.today() + timedelta(days=1)
    assert result.date() == tomorrow


def test_calculate_scheduled_time_past_rolls_to_next_day():
    # Base date = yesterday → rolls forward to today or tomorrow
    yesterday = date.today() - timedelta(days=1)
    result = calculate_scheduled_time("09:00", base_date=yesterday)
    assert result > datetime.now()


def test_assign_scheduled_times_single():
    contents = [make_content(1)]
    future = date.today() + timedelta(days=5)
    result = assign_scheduled_times(contents, "10:00", base_date=future)
    assert len(result) == 1
    assert result[0].scheduled_time is not None
    assert result[0].scheduled_time.hour == 10


def test_assign_scheduled_times_multiple_with_interval():
    contents = [make_content(i) for i in range(3)]
    future = date.today() + timedelta(days=5)
    result = assign_scheduled_times(contents, "09:00", base_date=future, interval_minutes=60)
    times = [c.scheduled_time for c in result]
    assert (times[1] - times[0]).seconds == 3600
    assert (times[2] - times[1]).seconds == 3600


def test_assign_scheduled_times_immutability():
    original = make_content(1)
    future = date.today() + timedelta(days=5)
    result = assign_scheduled_times([original], "12:00", base_date=future)
    assert original.scheduled_time is None
    assert result[0].scheduled_time is not None


def test_calculate_scheduled_time_invalid_format():
    with pytest.raises(ValueError):
        calculate_scheduled_time("25:99")
