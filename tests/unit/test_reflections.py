from decimal import Decimal

from calculadora_trabalhista.calculation.reflections import ReflectionGraph


def test_reflection_methods() -> None:
    graph = ReflectionGraph.from_config(
        [
            {
                "source": "overtime",
                "target": "vacations",
                "enabled": True,
                "calculation_method": "twelfth",
            },
            {"source": "overtime", "target": "fgts", "enabled": True, "calculation_method": "fgts"},
        ]
    )
    assert graph.calculate(Decimal("1200"), graph.edges[0], {}) == Decimal("100.00")
    assert graph.calculate(Decimal("1200"), graph.edges[1], {"fgts_rate": "0.08"}) == Decimal(
        "96.00"
    )
    assert not graph.has_cycle()
