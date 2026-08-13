from datetime import date

from calculadora_trabalhista.periods import (
    active_days_in_month,
    competence,
    iter_competences,
    parse_competence,
)


def test_competences_are_inclusive() -> None:
    values = list(iter_competences(date(2025, 11, 15), date(2026, 1, 2)))
    assert [competence(item) for item in values] == ["2025-11", "2025-12", "2026-01"]
    assert parse_competence("2025-02") == date(2025, 2, 1)
    assert active_days_in_month(date(2025, 2, 10), date(2025, 2, 20), date(2025, 2, 1)) == 11
