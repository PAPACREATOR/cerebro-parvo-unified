# Plano de testes — Front Door Nexus ponta-a-ponta

Data: 2026-10-04
Branch: `lab-e2e-frontdoor-20261004`

Objetivo: provar a entrada humana desde texto bruto até Kernel/result/proveniência, sem dar autoridade ao parser, ELIZA, Spiff ou Conductor.

## Princípio

Não contar apenas testes felizes. A matriz inclui:
- pedidos bons;
- pedidos maus;
- ambiguidades;
- erros ortográficos;
- Unicode;
- anexos;
- limites exatos e +1;
- comandos embebidos como dados;
- prompt injection;
- Markdown/YAML/JSON adversarial;
- capability proibida;
- processo inexistente;
- timeout/falha externa;
- restart/replay;
- proveniência inversa;
- Human Gate;
- adulteração.

## Fases e volume inicial

| Fase | Casos | Conteúdo |
|---|---:|---|
| L0 | 1 000 | 7 prefixos explícitos, espaços, Unicode, caixa, anexos |
| L1 | 2 000 | linguagem natural válida e variações simples |
| L2 | 1 500 | ambiguidades e pedidos incompletos |
| L3 | 2 000 | entradas adversariais/maliciosas |
| L4 | 1 000 | limites, malformed UTF-8/JSON/Markdown, tamanho |
| L5 | 1 500 | round-trip texto -> parser -> Markdown -> JSON -> pedido Nexus |
| L6 | 1 000 | E2E Kernel/Store/result/proveniência/restart em amostra barata |
| **Total inicial** | **10 000** | antes dos testes práticos pesados |

Os testes reais pesados (PowerShell, LibreOffice, LanguageTool, Notebook, Windows Lab) são uma camada separada e menor.

## Classificações esperadas

Cada caso termina em uma destas classes:
- `RESOLVED`
- `UNRESOLVED`
- `BLOCKED`
- `FAIL`

Nunca converter ambiguidade em RESOLVED por adivinhação.

## IDA

`texto original -> parser -> intenção -> Markdown -> JSON -> Kernel -> executor -> resultado -> Creative`

## VOLTA

`Creative/result -> proveniência -> processo/hash -> pedido JSON -> Markdown -> texto original/hash`

## Regras

1. O original é preservado byte-for-byte.
2. Prefixo explícito vence inferência.
3. Texto que contém prefixos como dados não pode virar comando.
4. Parser/ELIZA nunca escolhe credenciais, permissões, Canonical ou Human Gate.
5. Backend é resolvido pelo Kernel.
6. Se ELIZA não souber, devolve UNRESOLVED.
7. Replay nunca volta a reinterpretar texto para fabricar passado.
8. IA não é fallback automático.
9. Cada FAIL gera relatório com seed/case_id/input/esperado/observado.
10. Uma fase só avança depois de PASS.

## Ordem de implementação

1. contrato + testes L0;
2. parser mínimo;
3. L1/L2;
4. ELIZA mínima;
5. L3/L4;
6. objeto Markdown;
7. JSON de execução;
8. ligação ao Host/Kernel;
9. L5/L6;
10. testes práticos Windows;
11. só depois UI final.


## Regra de implementação mínima

- Python apenas como cola pequena, validação de fronteira e testes.
- Não criar novo motor de workflows em Python.
- Não duplicar funções já cobertas por Conductor, Spiff, LanguageTool ou leitores Markdown existentes.
- Regras de linguagem devem ser preferencialmente declarativas e auditáveis.
- LanguageTool só fornece sugestões/shadow; não altera o original.
- Tradutor local só entra como capability opcional para idioma diferente de português, depois de prova de necessidade.
- Markdown/YAML/JSON continuam a transportar estrutura; o Kernel continua a decidir autoridade.
