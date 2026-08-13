"""Grafo de reflexos com arestas juridicamente habilitadas pelo plano."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ..money import quantize_money, to_decimal


@dataclass(frozen=True)
class ReflectionEdge:
    source: str
    target: str
    enabled: bool
    legal_basis: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    calculation_method: str = "identity"
    factor: Decimal | None = None


class ReflectionGraph:
    """Grafo pequeno e determinístico; não cria arestas por conveniência."""

    def __init__(self, edges: list[ReflectionEdge] | None = None) -> None:
        self.edges = edges or []

    @classmethod
    def from_config(cls, config: list[dict[str, Any]]) -> ReflectionGraph:
        edges: list[ReflectionEdge] = []
        for raw in config:
            edges.append(
                ReflectionEdge(
                    source=str(raw["source"]),
                    target=str(raw["target"]),
                    enabled=bool(raw.get("enabled", False)),
                    legal_basis=raw.get("legal_basis"),
                    valid_from=raw.get("valid_from"),
                    valid_until=raw.get("valid_until"),
                    calculation_method=str(raw.get("calculation_method", "identity")),
                    factor=None if raw.get("factor") is None else to_decimal(raw["factor"]),
                )
            )
        return cls(edges)

    def duplicate_pairs(self) -> list[tuple[str, str]]:
        seen: set[tuple[str, str]] = set()
        duplicates: list[tuple[str, str]] = []
        for edge in self.edges:
            pair = (edge.source, edge.target)
            if pair in seen:
                duplicates.append(pair)
            seen.add(pair)
        return duplicates

    def has_cycle(self) -> bool:
        adjacency: dict[str, set[str]] = {}
        for edge in self.edges:
            if edge.enabled:
                adjacency.setdefault(edge.source, set()).add(edge.target)
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> bool:
            if node in visiting:
                return True
            if node in visited:
                return False
            visiting.add(node)
            if any(visit(next_node) for next_node in adjacency.get(node, set())):
                return True
            visiting.remove(node)
            visited.add(node)
            return False

        return any(visit(node) for node in adjacency)

    def calculate(
        self, source_amount: Decimal, edge: ReflectionEdge, context: dict[str, Any]
    ) -> Decimal:
        method = edge.calculation_method
        if method == "identity":
            factor = edge.factor if edge.factor is not None else Decimal("1")
            return quantize_money(source_amount * factor)
        if method == "twelfth":
            return quantize_money(source_amount / Decimal("12"))
        if method == "third_of_twelfth":
            return quantize_money(source_amount / Decimal("36"))
        if method == "fgts":
            return quantize_money(source_amount * to_decimal(context.get("fgts_rate", "0.08")))
        if method == "fgts_fine":
            fgts_rate = to_decimal(context.get("fgts_rate", "0.08"))
            fine_rate = to_decimal(context.get("fgts_fine_rate", "0.40"))
            return quantize_money(source_amount * fgts_rate * fine_rate)
        if method == "notice":
            days = to_decimal(context["notice_days"])
            return quantize_money(source_amount * days / Decimal("30"))
        if method == "factor":
            if edge.factor is None:
                raise ValueError(f"Aresta {edge.source}->{edge.target} exige factor")
            return quantize_money(source_amount * edge.factor)
        raise ValueError(f"Método de reflexo não suportado: {method}")
