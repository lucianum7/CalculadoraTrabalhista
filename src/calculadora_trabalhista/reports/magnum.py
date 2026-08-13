"""Padrão Magnum: linhas explícitas, numeradas e sem consolidação de reflexos."""

from __future__ import annotations

from calculadora_trabalhista.models import CalculationLine, CalculationResult
from calculadora_trabalhista.money import format_brl


def _priority(line: CalculationLine) -> tuple[int, int]:
    if line.category == "termination":
        return (1, line.order)
    if line.category == "principal":
        return (2, line.order)
    return (3, line.order)


def ordered_magnum_lines(result: CalculationResult) -> list[CalculationLine]:
    return sorted(result.lines, key=_priority)


def render_magnum_markdown(result: CalculationResult) -> str:
    lines = ordered_magnum_lines(result)
    output = [
        "# Tabela de pedidos — padrão Magnum",
        "",
        f"Status da auditoria: **{result.status.value}**",
        "",
        "| Nº | Verba | Competência | Categoria | Valor | Origem |",
        "|---:|---|---|---|---:|---|",
    ]
    for index, line in enumerate(lines, start=1):
        source = "; ".join(line.source_chain)
        output.append(
            f"| {index} | {line.label} | {line.competence or '—'} | {line.category} | {format_brl(line.amount)} | {source} |"
        )
    output.extend(
        [
            "",
            f"**Principal:** {format_brl(result.totals['principal'])}",
            "",
            f"**Reflexos:** {format_brl(result.totals['reflections'])}",
            "",
            f"**Total econômico:** {format_brl(result.total)}",
            "",
            "## Auditoria",
            "",
        ]
    )
    output.extend(f"- `{item.name}` — {item.status.value}: {item.message}" for item in result.audit)
    if result.missing_information:
        output.extend(["", "## Dados ausentes", ""])
        output.extend(f"- {item}" for item in result.missing_information)
    return "\n".join(output) + "\n"
