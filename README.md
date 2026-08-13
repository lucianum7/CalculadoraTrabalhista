# CalculadoraTrabalhista

Engine local, multiplataforma e determinística para estruturar fatos e calcular verbas trabalhistas com rastreabilidade por competência. O projeto separa interpretação documental (IA/agente) de matemática financeira (Python + `Decimal`) e exporta memória de cálculo, JSON, Markdown e planilhas no padrão Magnum.

> Este projeto é independente e não possui vínculo, chancela ou afiliação com o Conselho Superior da Justiça do Trabalho, Tribunal Superior do Trabalho ou com o sistema PJe-Calc. PJe-Calc é utilizado apenas como referência metodológica e de validação de cálculos quando aplicável.

## O que já funciona

- Schema Pydantic para `process_facts.json`, com status e proveniência por fato.
- Cálculos por competência de horas extras (percentual/divisor explícitos), integração de variável, verbas rescisórias e FGTS.
- `ReflectionGraph` com arestas habilitadas individualmente, fundamento, vigência e métodos determinísticos.
- Auditoria independente: consistência de períodos, fontes, arredondamento, pagamentos, conflitos, ciclos e duplicidades.
- Manifesto de execução com hashes de fatos, regras, tabelas, configuração e resultado.
- Exportadores `calculation_result.json`, `Tabela_Pedidos.md`, `Tabela_Pedidos.xlsx` e `Memoria_Calculo.xlsx`.
- Skills sincronizadas para OpenAI/Codex, Claude Code e Gemini.

## Instalação

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Verifique a instalação:

```bash
calculadora-trabalhista doctor
calculadora-trabalhista validate
```

## Exemplo sintético

O fixture `tests/fixtures/process_facts_synthetic.json` é fictício e inclui verbas rescisórias, horas extras de 50%, variável e reflexos em férias, 1/3, 13º, FGTS, multa de 40% e aviso.

```bash
calculadora-trabalhista demo --output-dir outputs/demo
```

Para um processo estruturado:

```bash
calculadora-trabalhista calculate process_facts.json \
  --mode LIQUIDATION \
  --output-dir outputs/caso \
  --strict
```

`--strict` encerra com código 2 quando faltam parâmetros. Sem ele, o resultado é marcado como `PARTIAL` e lista os dados ausentes; ausência nunca vira zero silenciosamente.

## Como a cadeia é explicada

Cada linha guarda `source_chain`, fórmula, competência, fundamento e proveniência. A resposta esperada é:

```text
documento → página → fato → regra → parâmetro → fórmula → competência
→ resultado → reflexos → atualização → total
```

## Skills de agentes

- OpenAI/Codex: `skill/calculos-trabalhistas/SKILL.md` (adaptador em `.agents/skills/...`).
- Claude Code: `.claude/skills/calculos-trabalhistas/SKILL.md`.
- Gemini CLI: contexto em `GEMINI.md` e `.agents/skills/...`.

Os adaptadores são cópias geradas por `python scripts/sync_skill_adapters.py`; a CI falha se divergirem.

## Arquitetura

```text
process_facts.json
        │
        ▼
Pydantic + proveniência ──► plano/parâmetros versionados
        │
        ▼
CalculationEngine (Decimal)
  ├─ jornada e horas extras
  ├─ salários/variáveis
  ├─ rescisão e FGTS
  └─ ReflectionGraph
        │
        ▼
auditoria + manifesto ──► JSON / Markdown / XLSX
```

## Fontes e segurança jurídica

O registro de fontes em `data/official/sources.json` aponta para legislação do Planalto e para o serviço PJe-Calc Cidadão do TST. Regras históricas, tabelas tributárias e índices devem ser cadastrados com vigência, data de consulta e hash antes de uma liquidação real. O software não presta aconselhamento jurídico.

## Qualidade

```bash
ruff check .
mypy .
pytest --cov=calculadora_trabalhista
```

O workflow do GitHub testa Linux e Windows, valida os schemas e verifica a sincronização das skills.

## Limitações reais do release 0.1.0

O núcleo não baixa automaticamente índices oficiais, não interpreta PDF/DOCX por OCR e não substitui a escolha jurídica de regras de DSR, adicional noturno, tributos ou atualização monetária. Esses pontos possuem interfaces e dados explícitos para evolução; em caso de ausência o cálculo é parcial/bloqueado.

## Roadmap

`0.2` jornada diária avançada e ingestão documental; `0.3` tabelas históricas de encargos; `0.4` atualização monetária versionada; `0.5` golden tests com memórias de cálculo públicas; `1.0` somente após validação suficiente.

## Licença

MIT. Veja `SECURITY.md`, `CONTRIBUTING.md` e `CODE_OF_CONDUCT.md`.
