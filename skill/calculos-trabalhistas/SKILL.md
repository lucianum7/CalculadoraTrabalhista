---
name: calculos-trabalhistas
description: >
  Analisa processos trabalhistas e realiza cálculos de verbas, diferenças,
  jornadas, reflexos, FGTS, rescisão, encargos, atualização, liquidação e
  auditoria. Use quando houver pedido de cálculo trabalhista, liquidação,
  tabela de pedidos, memória de cálculo ou conferência conceitual de PJe-Calc.
---

# CalculadoraTrabalhista

Use esta skill para coordenar interpretação documental e o motor local. A IA pode ler, classificar, extrair e escolher regras; toda aritmética monetária deve ser executada pelo Python em `Decimal`.

## Regras invioláveis

1. Nunca invente salário, jornada, divisor, índice, percentual, feriado, pagamento, fato ou reflexo.
2. Preserve a proveniência de cada fato (`document`, `page`, `source_excerpt`, `status`, `confidence`).
3. Não transforme `AUSENTE` em zero. Informe dados faltantes e use `--strict` quando o cálculo não puder prosseguir com segurança.
4. Cada regra deve indicar fonte oficial, vigência e base jurídica. PJe-Calc é somente referência metodológica independente.
5. Reflexos são arestas explícitas em `calculation_parameters.reflection_graph`; nunca habilite todos automaticamente.
6. Antes de concluir, execute `calculadora-trabalhista doctor`, `validate` e a auditoria do resultado.

## Fluxo

1. Identifique documentos, decisões, pedidos, conflitos e dados ausentes.
2. Normalize fatos em `process_facts.json` conforme `schemas/process_facts.schema.json`.
3. Crie um plano com modo `INITIAL_CLAIM`, `LIQUIDATION`, `EXECUTION`, `AUDIT` ou `SIMULATION`.
4. Execute:

   ```bash
   calculadora-trabalhista calculate process_facts.json --mode SIMULATION --output-dir outputs/caso
   ```

5. Leia `calculation_result.json`, `Tabela_Pedidos.md`, `Tabela_Pedidos.xlsx` e `Memoria_Calculo.xlsx`.
6. Explique a cadeia `documento → página → fato → regra → parâmetro → fórmula → competência → resultado → reflexos → total`.

## Padrão de resposta

Relate resumo contratual, documentos, parâmetros, conflitos, pedidos, memória por competência, deduções, encargos, tabela Magnum, total econômico, auditoria, dados ausentes e fontes. Diferencie fato confirmado, derivado, estimado e calculado. Nunca chame um resultado de `AUDITED` se houver erro ou divergência não resolvida.

## Limites

O projeto é independente e não possui vínculo, chancela ou afiliação com CSJT, TST ou PJe-Calc. O motor não substitui advogado, perito ou validação judicial. Tabelas tributárias e índices históricos devem ser fornecidos com fonte e vigência antes de uma liquidação real.
