"""Sincroniza a skill canônica para os adaptadores Windows-friendly."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "skill/calculos-trabalhistas/SKILL.md"
ADAPTERS = [
    ROOT / ".agents/skills/calculos-trabalhistas/SKILL.md",
    ROOT / ".claude/skills/calculos-trabalhistas/SKILL.md",
]


def main() -> int:
    content = CANONICAL.read_text(encoding="utf-8")
    for adapter in ADAPTERS:
        adapter.parent.mkdir(parents=True, exist_ok=True)
        adapter.write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
