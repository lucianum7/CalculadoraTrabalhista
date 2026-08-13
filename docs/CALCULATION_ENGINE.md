# Engine de cálculo

Valores monetários são convertidos por `money.to_decimal` e arredondados em `quantize_money` com `ROUND_HALF_UP` e duas casas. Floats são rejeitados.

Para horas extras, a fórmula é:

```text
valor-hora = remuneração da competência / divisor informado
devido = valor-hora × (1 + adicional) × horas informadas
diferença = max(0, devido − pago informado)
```

Rescisão usa os dias, avos e aviso declarados no plano. FGTS é competência a competência e deduz o recolhido informado. Cada linha aponta para salário, parâmetro e/ou documento.

Reflexos usam `ReflectionGraph`: `twelfth`, `third_of_twelfth`, `fgts`, `fgts_fine`, `notice`, `factor` e `identity`. Nenhuma aresta é criada automaticamente.
