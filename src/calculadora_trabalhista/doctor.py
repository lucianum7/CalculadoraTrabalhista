"""Verificações locais para instalação e integridade do repositório."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def run_doctor(root: str | Path | None = None) -> tuple[bool, list[str]]:
    base = Path(root or Path.cwd())
    checks: list[tuple[bool, str]] = []
    checks.append(
        (sys.version_info >= (3, 12), f"Python {sys.version_info.major}.{sys.version_info.minor}")
    )
    checks.append((importlib.util.find_spec("decimal") is not None, "Decimal engine"))
    for relative, label in (
        ("schemas/process_facts.schema.json", "Schemas"),
        ("data/official/sources.json", "Official tables"),
        ("skill/calculos-trabalhistas/SKILL.md", "Skill canônica"),
        (".agents/skills/calculos-trabalhistas/SKILL.md", "Skill OpenAI"),
        (".claude/skills/calculos-trabalhistas/SKILL.md", "Skill Claude"),
        ("GEMINI.md", "Gemini context"),
    ):
        checks.append(((base / relative).exists(), label))
    checks.append((importlib.util.find_spec("openpyxl") is not None, "XLSX exporter"))
    checks.append((importlib.util.find_spec("pydantic") is not None, "Pydantic models"))
    ok = all(item[0] for item in checks)
    lines = [f"[{'OK' if passed else 'FAIL'}] {label}" for passed, label in checks]
    lines.append(f"\nSTATUS: {'READY' if ok else 'NOT READY'}")
    return ok, lines
