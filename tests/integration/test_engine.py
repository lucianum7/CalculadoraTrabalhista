from pathlib import Path

from calculadora_trabalhista.calculation.engine import CalculationEngine
from calculadora_trabalhista.ingestion.json_provider import JsonProcessFactsProvider
from calculadora_trabalhista.models import CalculationMode, CalculationStatus


def test_synthetic_engine_has_magnum_lines() -> None:
    fixture = Path(__file__).parents[1] / "fixtures" / "process_facts_synthetic.json"
    facts = JsonProcessFactsProvider(fixture).load()
    result = CalculationEngine().calculate(facts, CalculationMode.SIMULATION)
    assert result.status == CalculationStatus.AUDITED
    labels = [line.label for line in result.lines]
    assert "Verbas rescisórias" not in labels  # claim is metadata, not an invented total line
    assert any(label == "Horas extras 50%" for label in labels)
    assert any(label == "Ref. em multa de 40% do FGTS" for label in labels)
    assert result.manifest is not None
    assert len(result.manifest.facts_hash) == 64
    assert result.total > 0
