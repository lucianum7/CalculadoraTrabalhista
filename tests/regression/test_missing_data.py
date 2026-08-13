from decimal import Decimal

from calculadora_trabalhista.calculation.engine import CalculationEngine
from calculadora_trabalhista.models import CalculationMode, Claim, ProcessFacts, SalaryEntry


def test_missing_divisor_never_becomes_zero() -> None:
    facts = ProcessFacts(
        salary_history=[SalaryEntry(competence="2025-01", base_salary=Decimal("3000"))],
        claims=[Claim(code="overtime", label="Horas extras")],
        calculation_parameters={"overtime_hours_by_competence": {"2025-01": "10"}},
    )
    result = CalculationEngine().calculate(facts, CalculationMode.SIMULATION)
    assert result.lines == []
    assert "divisor: necessário para calcular horas extras" in result.missing_information
