"""Exportadores sem efeitos colaterais fora do diretório solicitado."""

from __future__ import annotations

import json
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

from ..models import CalculationResult
from .magnum import ordered_magnum_lines, render_magnum_markdown


def export_json(result: CalculationResult, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def export_markdown(result: CalculationResult, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_magnum_markdown(result), encoding="utf-8")
    return target


def export_xlsx(result: CalculationResult, output_dir: str | Path) -> tuple[Path, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    table_path = directory / "Tabela_Pedidos.xlsx"
    memory_path = directory / "Memoria_Calculo.xlsx"

    table_book = Workbook()
    table = table_book.active
    table.title = "Tabela_Pedidos"
    table.append(["Nº", "Verba", "Competência", "Categoria", "Valor", "Origem"])
    for cell in table[1]:
        cell.font = Font(bold=True)
    for index, line in enumerate(ordered_magnum_lines(result), start=1):
        table.append(
            [
                index,
                line.label,
                line.competence,
                line.category,
                float(line.amount),
                "; ".join(line.source_chain),
            ]
        )
    table.append([])
    table.append(["", "Total econômico", "", "", float(result.total), ""])
    table.freeze_panes = "A2"
    table.column_dimensions["B"].width = 44
    table.column_dimensions["F"].width = 64
    table_book.save(table_path)

    memory_book = Workbook()
    memory = memory_book.active
    memory.title = "Memoria_Calculo"
    memory.append(["Ordem", "Código", "Fórmula", "Valor", "Cadeia de origem", "Base jurídica"])
    for cell in memory[1]:
        cell.font = Font(bold=True)
    for line in result.lines:
        memory.append(
            [
                line.order,
                line.code,
                line.formula,
                float(line.amount),
                "; ".join(line.source_chain),
                line.legal_basis,
            ]
        )
    memory.append([])
    memory.append(["", "", "Total econômico", float(result.total), "", ""])
    memory.freeze_panes = "A2"
    memory.column_dimensions["C"].width = 58
    memory.column_dimensions["E"].width = 64
    memory_book.save(memory_path)
    return table_path, memory_path
