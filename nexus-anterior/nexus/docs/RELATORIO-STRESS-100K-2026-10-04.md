# Relatório — matriz determinística de 100 000 casos

Data: 2026-10-04
Ficheiro de teste: `nexus/tests/test_stress_matrix_100k.py`

## Objetivo

Aumentar cobertura de contratos baratos e determinísticos sem lançar 100 000 processos externos.

## Distribuição

| Família | Casos | Seed | Contrato |
|---|---:|---:|---|
| Comparação bidirecional | 50 000 | 20261004 | A->B e B->A preservam outcome e ambos os lados |
| HumanDecision binding | 30 000 | 20261005 | decisão ligada a item+versão+ação; mismatch rejeitado |
| JSON estrito/roundtrip | 20 000 | 20261006 | roundtrip Unicode/números/listas; chaves duplicadas rejeitadas |
| **Total** | **100 000** | fixas | reproduzível |

## Classificação da comparação

O oracle conserva:
- `agreement`;
- `conflict`;
- `unknown`;
- `failure`.

A ordem A/B pode inverter a evidência, mas não pode alterar o outcome.

## Evidência

A matriz faz parte de `pytest nexus/tests`.

Última regressão após os checkpoints Kernel-owned:
- Windows run `37202434881`;
- **1217 pytest tests PASS**;
- dentro dessa suite, as quatro funções da matriz executam exatamente **100 000 iterações determinísticas**;
- `NEXUS PASS | COMPLETE`;
- PowerShell wrapper PASS.

## O que este PASS prova

- comportamento determinístico do comparador sob grande variedade de hashes/estados;
- binding de aprovação em 30 000 variações;
- parser JSON estrito em 20 000 roundtrips/mutações;
- seeds reproduzíveis.

## O que NÃO prova

- não são 100 000 E2E;
- não são 100 000 processos Conductor;
- não exercitam LibreOffice/Open Notebook/LanguageTool 100 000 vezes;
- não substituem crash real do processo Windows;
- não substituem `C:\Nexus-Lab`;
- não provam homelab, rede, telemóvel ou hardening final.

## Próxima expansão útil

Adicionar famílias de estado Kernel sem transformar o stress em I/O pesado:
- transições permitidas/proibidas;
- idempotência;
- checkpoints;
- combinações de FAIL/BLOCKED/UNKNOWN;
- invariantes Creative/Canonical;
- invariantes de proveniência.

Testes externos pesados continuam numa amostra pequena e representativa.
