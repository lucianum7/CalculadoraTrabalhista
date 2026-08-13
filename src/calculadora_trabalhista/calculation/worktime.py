"""Cálculo de jornada a partir de marcações informadas."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from ..models import Timecard
from ..money import quantize_money


def _as_datetime(day: date, value: time) -> datetime:
    return datetime.combine(day, value)


def segment_minutes(day: date, start: time, end: time) -> int:
    begin = _as_datetime(day, start)
    finish = _as_datetime(day, end)
    if finish <= begin:
        finish += timedelta(days=1)
    return int((finish - begin).total_seconds() // 60)


def _overlap_minutes(
    start: datetime, end: datetime, window_start: datetime, window_end: datetime
) -> int:
    left, right = max(start, window_start), min(end, window_end)
    return max(0, int((right - left).total_seconds() // 60))


def night_minutes(day: date, start: time, end: time) -> int:
    begin = _as_datetime(day, start)
    finish = _as_datetime(day, end)
    if finish <= begin:
        finish += timedelta(days=1)
    total = 0
    for offset in range(-1, 3):
        cursor = day + timedelta(days=offset)
        total += _overlap_minutes(
            begin,
            finish,
            _as_datetime(cursor, time(22, 0)),
            _as_datetime(cursor + timedelta(days=1), time(5, 0)),
        )
    return total


def summarize_timecard(timecard: Timecard) -> dict[str, Decimal | int | str]:
    worked = 0
    night = 0
    for segment in timecard.segments:
        minutes = segment_minutes(timecard.date, segment.start, segment.end)
        worked += max(0, minutes - segment.break_minutes)
        night += max(
            0, night_minutes(timecard.date, segment.start, segment.end) - segment.break_minutes
        )
    return {
        "date": timecard.date.isoformat(),
        "worked_minutes": worked,
        "night_minutes": night,
        "worked_hours": quantize_money(Decimal(worked) / Decimal(60)),
        "night_hours": quantize_money(Decimal(night) / Decimal(60)),
    }


def overtime_hours(timecards: list[Timecard], expected_daily_minutes: int) -> Decimal:
    """Calcula horas acima da jornada diária explicitamente informada."""

    if expected_daily_minutes < 0:
        raise ValueError("expected_daily_minutes não pode ser negativo")
    minutes = 0
    for timecard in timecards:
        summary = summarize_timecard(timecard)
        minutes += max(0, int(summary["worked_minutes"]) - expected_daily_minutes)
    return quantize_money(Decimal(minutes) / Decimal(60))
