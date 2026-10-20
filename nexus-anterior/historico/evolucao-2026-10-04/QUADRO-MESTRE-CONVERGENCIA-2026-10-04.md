# Nexus — Quadro mestre de convergência

Data: 2026-10-04  
Branch: `integration-convergence-20261004`

## Regra

Limpar, organizar e juntar sem perder avanços.

- Não apagar branches/PRs históricos usados como evidência.
- Não alterar leis/arquitetura congeladas.
- Não substituir código já PASS por outra solução sem FAIL reproduzido.
- Cada camada integrada mantém os seus testes originais.
- A nova baseline só nasce depois de todas as suites passarem juntas.
- `C:\Nexus` continua intocado; convergência é GitHub/Lab.

## Linha de proveniência

`#7 Windows baseline -> #8 recovery/hardening -> #9 Lab por fases -> #10 Spiff+Conductor`

A partir de #10:

- `#11` performance/flows Conductor;
- `#13` Front Door/LanguageTool.

Esta branch converge #11 + #13 sobre #10, preservando toda a linha anterior.

## Comparação por camada

| Camada | Origem | Evidência antes da convergência | Estado | Decisão |
|---|---|---|---|---|
| Windows/startup/locks | #7 | Auditoria + Windows PASS | VALIDADO | preservar |
| Recovery/checkpoints | #8/#9 | PREPARED/EXECUTING/RESULT_ACCEPTED; recovery seguro | VALIDADO na linha #9+ | preservar |
| Human Gate/Creative/Canonical | #7/#8/#9 | regressões + 100k determinístico | VALIDADO no escopo coberto | preservar |
| Lab por fases | #9 | core 140; blocks 1075; all 1222; practical 18 | PASS | preservar |
| Spiff + Conductor | #10 | 5000/5000 casos conjuntos | PASS | integrar como opcional/experimental |
| Performance Conductor | #11 | 4 benchmarks PASS | PASS | integrar evidência; sem otimização cega |
| Front Door | #13 | L0-L4 + LT shadow PASS | PASS | integrar |
| LanguageTool shadow | #13 | original preservado; shadow sem autoridade | PASS | integrar |
| Markdown -> JSON -> Kernel | futuro L5 | não executado | NOT RUN | próximo depois da convergência |
| Kernel E2E/restart Front Door | futuro L6 | não executado | NOT RUN | depois de L5 |
| Windows PC físico | C:\Nexus-Lab | ainda sem evidência nesta branch | NOT RUN | gate posterior |
| Hardening/encriptação/móvel | final | não iniciado | NOT RUN | só no fim |

## Resultados já comprovados

### Lab #9
- core: 140 PASS
- blocks: 1075 PASS
- all: 1222 PASS
- practical: 18 PASS
- PowerShell wrapper: PASS

### Spiff + Conductor #10
- S0: PASS
- S1: 1000/1000 ida
- S2: 1000/1000 volta
- S3: 1000/1000 limites
- S4: 1000/1000 classificações
- S5: 1000/1000 stress
- total: 5000/5000

### Performance #11
- 5 set -> 1 multi-set: sem ganho relevante (~-1.5%)
- parallel em trabalho interno barato: pior (~-5%)
- foreach concorrente: ganho pequeno (~7%)
- subprocesso script -> set interno: ~95% menos tempo, ~20x
- regra: manter subprocesso quando representa ferramenta/método independente; retirar apenas glue trivial

### Front Door #13
- L0 prefixos: PASS
- L1/L2 linguagem/ambiguidades: PASS
- LanguageTool shadow: PASS
- L3 adversarial: PASS
- L4 limites/malformed: PASS
- Python Front Door reduzido para matcher pequeno; regras declarativas JSON + schema
- tradutor completo não entra nesta fase

## Sobreposição e conflitos

| Ficheiro/área | #11 | #13 | Risco |
|---|---|---|---|
| Kernel/Store | não altera | não altera | baixo |
| Spiff tests | altera/adiciona | não altera | baixo |
| Conductor perf | adiciona | não altera | baixo |
| Front Door | não altera | adiciona | baixo |
| LanguageTool adapter | não altera | altera | médio: integrity/regressão |
| integrity.json | não altera | altera | médio: validar |
| workflows CI | Spiff workflow | Front Door workflow | baixo |
| leis/policy | não altera | não altera | nenhum |

Conclusão: a convergência é sobretudo um problema de **regressão conjunta**, não de conflito conceptual.

## Matriz de autoridade

| Componente | Pode decidir | Não pode decidir |
|---|---|---|
| Kernel/Store | estado, política, capability, limites, recovery, Human Gate | — |
| Spiff | lógica efémera do agente dentro do contrato | persistência, IA permitida, Canonical, recovery |
| Conductor | execução efémera da capability/flow | memória Nexus, política, Human Gate |
| Front Door/ELIZA | intenção candidata / UNRESOLVED | backend, permissão, promoção |
| LanguageTool | sugestões/shadow | alterar original, criar autoridade |
| Markdown | molde auditável | executar |
| YAML | processo versionado | autoridade humana |
| JSON | envelope de execução | decidir política |

## Gate de convergência

A branch só passa a baseline se, no mesmo HEAD:

1. Auditoria = PASS;
2. Nexus Windows = PASS;
3. core/blocks/all/practical = PASS;
4. Spiff + Conductor S0-S5 = PASS;
5. 5000/5000 = PASS;
6. benchmarks Conductor = PASS;
7. Front Door L0-L4/LT = PASS;
8. integrity = PASS;
9. nenhuma lei/arquitetura alterada;
10. nenhum PASS anterior perdido.

Depois:
- marcar esta branch como única base de continuação do Lab;
- manter PRs anteriores como arquivo/evidência;
- retomar L5 Markdown/JSON;
- retomar L6 E2E/restart;
- só depois levar ao `C:\Nexus-Lab` físico.
