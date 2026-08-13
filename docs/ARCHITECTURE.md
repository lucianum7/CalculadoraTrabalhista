# Arquitetura

`ProcessFacts` valida a entrada. `CalculationEngine` calcula somente parâmetros informados. `ReflectionGraph` aplica arestas habilitadas. `audit_result` recomputa invariantes independentemente. `reports` gera a tabela Magnum e a memória em três formatos.

A camada de agente é opcional: o motor não importa SDK de OpenAI, Anthropic ou Google.
