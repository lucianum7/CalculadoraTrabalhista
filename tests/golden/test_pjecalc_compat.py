from pathlib import Path

from calculadora_trabalhista.calculation.engine import CalculationEngine
from calculadora_trabalhista.ingestion.json_provider import JsonProcessFactsProvider
from calculadora_trabalhista.pjecalc_compat.comparator import compare_results


def test_comparator_reports_exact_expected_lines() -> None:
    fixture = Path(__file__).parents[1] / "fixtures" / "process_facts_synthetic.json"
    result = CalculationEngine().calculate(JsonProcessFactsProvider(fixture).load())
    expected = {line.code: str(line.amount) for line in result.lines}
    rows = compare_results(result, expected)
    assert rows and all(row.status == "PASS" for row in rows)
