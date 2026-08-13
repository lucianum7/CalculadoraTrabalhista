"""Utilitários de competência e calendários, sem suposições jurídicas."""

from __future__ import annotations

import calendar
from collections.abc import Iterator
from datetime import date, timedelta
from decimal import Decimal


def month_start(value: date) -> date:
    return value.replace(day=1)


def month_end(value: date) -> date:
    return value.replace(day=calendar.monthrange(value.year, value.month)[1])


def competence(value: date) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def parse_competence(value: str) -> date:
    try:
        year, month = (int(part) for part in value.split("-"))
        return date(year, month, 1)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Competência inválida: {value!r}; esperado AAAA-MM") from exc


def iter_competences(start: date, end: date) -> Iterator[date]:
    """Itera meses inclusivos entre duas datas."""

    current = month_start(start)
    limit = month_start(end)
    while current <= limit:
        yield current
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)


def days_inclusive(start: date, end: date) -> int:
    if end < start:
        return 0
    return (end - start).days + 1


def active_days_in_month(start: date, end: date, month: date) -> int:
    left = max(start, month_start(month))
    right = min(end, month_end(month))
    return days_inclusive(left, right)


def proportional_twelfths(start: date, end: date) -> Decimal:
    """Retorna avos aproximados por mês efetivamente alcançado no intervalo.

    A engine mantém a decisão jurídica explícita; esta função apenas conta
    competências inclusivas e é usada quando o plano informa que o critério
    mensal é aplicável.
    """

    return Decimal(sum(1 for _ in iter_competences(start, end)))


def date_range(start: date, end: date) -> Iterator[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)
