# Instruções para agentes

Leia o `README.md` e carregue `skill/calculos-trabalhistas/SKILL.md` sempre que a tarefa envolver cálculo, liquidação, auditoria ou tabela de pedidos trabalhistas.

- Use o motor determinístico; a IA interpreta, o Python calcula.
- Nunca invente salário, jornada, divisor, percentual, índice ou reflexo.
- Preserve `Decimal`, proveniência, vigência das regras e o padrão Magnum.
- Rode `ruff check .`, `mypy .`, `pytest` e `calculadora-trabalhista doctor` antes de concluir.
- Verifique fontes oficiais e atualize a documentação quando alterar uma regra.
