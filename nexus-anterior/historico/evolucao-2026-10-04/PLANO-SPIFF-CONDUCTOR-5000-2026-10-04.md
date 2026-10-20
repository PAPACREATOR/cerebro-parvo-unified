# Plano de testes — Kernel + Spiff + Conductor

Data: 2026-10-04
Branch: `lab-spiff-conductor-20261004`

## Princípio

O Kernel manda. Spiff e Conductor são executores efémeros.

Spiff não precisa de saber se a capability é IA, PowerShell, Python ou outra. Recebe uma tarefa fechada. O Kernel é quem conhece política, limites e autoridade.

Nenhum destes testes atribui persistência, Human Gate, Canonical ou recovery a Spiff/Conductor.

## Fases

| Fase | Casos | Objetivo | Gate |
|---|---:|---|---|
| S0 | smoke | importar Spiff 3.2.0 + Conductor e completar uma chamada mínima | PASS antes de escalar |
| S1 | 1000 | ida: Kernel -> Spiff -> Conductor -> resultado | 1000/1000 |
| S2 | 1000 | volta: resultado -> trace -> workflow -> input original | 1000/1000 |
| S3 | 1000 | routing/limites: iterações, timeout lógico, payloads e ordem | 1000/1000 |
| S4 | 1000 | falhas: missing input, conflito, UNKNOWN/FAIL e evidência conservada | 1000/1000 |
| S5 | 1000 | stress determinístico conjunto, repetição com seeds fixas | 1000/1000 |
| **Total** | **5000** | cada caso fecha ida e/ou volta conforme a fase | sem falha crítica |

## Contrato comum

IDA:
`Kernel -> tarefa fechada -> Spiff -> Conductor -> resultado -> Kernel`

VOLTA:
`resultado -> trace -> motor/versão -> workflow/hash -> input/hash -> pedido original`

## Limites Kernel-owned

O Kernel define:
- motor(es) permitidos;
- ordem dos motores;
- máximo de iterações;
- deadline/timeout;
- tamanho de payload;
- capability permitida;
- resultado esperado;
- política de retry;
- estado final.

Spiff/Conductor não podem:
- promover Canonical;
- fabricar Human Gate;
- alterar leis;
- possuir memória Nexus;
- decidir retry global;
- decidir persistência/recovery;
- executar IA se o Kernel não a autorizou.

## Comparação

Para cada caso registar:
- case_id;
- seed;
- input_hash;
- direção;
- motores usados;
- limites;
- output_hash;
- trace;
- resultado;
- duração;
- PASS/FAIL/UNKNOWN;
- diferença entre resultado esperado e observado.

## Regra de progressão

S0 PASS -> S1 -> S2 -> S3 -> S4 -> S5.

Se qualquer fase falhar:
- parar essa fase;
- conservar evidência;
- corrigir apenas a causa;
- repetir a fase;
- não mascarar FAIL com continuação do stress.
