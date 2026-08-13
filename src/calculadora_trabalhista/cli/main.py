from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console

from ..calculation.engine import CalculationEngine
from ..doctor import run_doctor
from ..ingestion.json_provider import JsonProcessFactsProvider
from ..models import CalculationMode
from ..reports.exporters import export_json, export_markdown, export_xlsx

app = typer.Typer(help="Cálculos trabalhistas determinísticos e auditáveis.", no_args_is_help=True)
console = Console()


@app.command()
def calculate(
    input_path: Path = typer.Argument(..., exists=True, readable=True, help="process_facts.json"),
    output_dir: Path = typer.Option(Path("outputs"), "--output-dir", "-o"),
    mode: CalculationMode = typer.Option(CalculationMode.SIMULATION, "--mode"),
    strict: bool = typer.Option(False, "--strict", help="Falha se houver dados ausentes."),
) -> None:
    """Executa um processo estruturado e gera JSON, Markdown e XLSX."""

    try:
        facts = JsonProcessFactsProvider(input_path).load()
        result = CalculationEngine().calculate(facts, mode)
    except Exception as exc:  # pragma: no cover - mensagem de fronteira CLI
        console.print(f"[red]FAILED[/red] {exc}")
        raise typer.Exit(code=1) from exc
    output_dir.mkdir(parents=True, exist_ok=True)
    export_json(result, output_dir / "calculation_result.json")
    export_markdown(result, output_dir / "Tabela_Pedidos.md")
    table_path, memory_path = export_xlsx(result, output_dir)
    console.print(f"Status: [bold]{result.status.value}[/bold]")
    console.print(f"Total econômico: [bold]{result.total}[/bold]")
    console.print(f"Tabela: {table_path}")
    console.print(f"Memória: {memory_path}")
    if result.missing_information:
        console.print("Dados ausentes:")
        for item in result.missing_information:
            console.print(f"  - {item}")
        if strict:
            raise typer.Exit(code=2)


@app.command()
def doctor() -> None:
    """Verifica Python, dependências, schemas, skills e tabelas."""

    ok, lines = run_doctor()
    for line in lines:
        console.print(line)
    if not ok:
        raise typer.Exit(code=1)


@app.command()
def validate() -> None:
    """Valida hashes/fontes declaradas e sincronização das skills."""

    root = Path.cwd()
    errors: list[str] = []
    for path in (
        root / "schemas/process_facts.schema.json",
        root / "schemas/calculation_result.schema.json",
    ):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            errors.append(f"schema inválido: {path} ({exc})")
    canonical = root / "skill/calculos-trabalhistas/SKILL.md"
    for adapter in (
        root / ".agents/skills/calculos-trabalhistas/SKILL.md",
        root / ".claude/skills/calculos-trabalhistas/SKILL.md",
    ):
        if (
            not canonical.exists()
            or not adapter.exists()
            or canonical.read_bytes() != adapter.read_bytes()
        ):
            errors.append(f"skill divergente: {adapter}")
    sources = root / "data/official/sources.json"
    if not sources.exists():
        errors.append("data/official/sources.json ausente")
    if errors:
        for error in errors:
            console.print(f"[red]FAIL[/red] {error}")
        raise typer.Exit(code=1)
    console.print("[green]OK[/green] schemas, fontes e adaptadores íntegros")


@app.command()
def demo(output_dir: Path = typer.Option(Path("outputs/demo"), "--output-dir", "-o")) -> None:
    """Executa o caso sintético distribuído com o repositório."""

    fixture = (
        Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "process_facts_synthetic.json"
    )
    if not fixture.exists():
        console.print(f"[red]Fixture não encontrado:[/red] {fixture}")
        raise typer.Exit(code=1)
    calculate(fixture, output_dir, CalculationMode.SIMULATION, False)


if __name__ == "__main__":  # pragma: no cover
    app()
