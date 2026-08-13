from datetime import date, time

from calculadora_trabalhista.calculation.worktime import (
    night_minutes,
    segment_minutes,
    summarize_timecard,
)
from calculadora_trabalhista.models import Timecard, WorkSegment


def test_segment_crossing_midnight() -> None:
    assert segment_minutes(date(2025, 1, 1), time(22), time(2)) == 240
    assert night_minutes(date(2025, 1, 1), time(22), time(2)) == 240


def test_multiple_marks_and_break() -> None:
    card = Timecard(
        date=date(2025, 1, 1),
        segments=[
            WorkSegment(start=time(8), end=time(12), break_minutes=0),
            WorkSegment(start=time(13), end=time(18), break_minutes=0),
        ],
    )
    summary = summarize_timecard(card)
    assert summary["worked_minutes"] == 540
    assert summary["worked_hours"] == 9
