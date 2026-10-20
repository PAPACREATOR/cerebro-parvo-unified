# Nexus — estado de consolidação (11-10-2026)

## Conclusão operacional

O Nexus principal está no repositório `PAPACREATOR/cerebro-parvo-`. Este é o único produto ativo.

A unificação já ocorreu:

- PR #50 integrou a Folha única e a rota Writer/PDF com confirmação pré-execução e Human Gate separado para Creative → Canonical.
- PR #51 unificou a genealogia da `main` com o candidato Nexus, sem reescrever Kernel ou Store.
- PR #53 integrou o roteador genérico de dez capacidades, sempre sob seleção determinística e Human Gate.
- O HEAD atual da `main` inicializa o servidor Folha Nexus como transporte HTTP loopback subordinado ao Host.

## Repositórios

| Repositório | Papel |
|---|---|
| `cerebro-parvo-` | Produto principal e único runtime autoritativo. |
| `cerebro-parvo-ai-studio-lab` | Laboratório secundário do Cérebro Parvo / AI Studio. |
| `nexus-folha-lab` | Laboratório histórico da Folha/ELIZA; não é produto. |
| `nexus-writer-lab` | Laboratório histórico de diagnóstico Writer/LPAC; não é produto. |
| `AI-Studio` | Repositório privado antigo; não é runtime ativo. |

## Issues históricas

As issues abaixo descrevem estados anteriores à unificação e não devem ser tratadas como trabalho pendente sem reavaliação:

- #33 — unificação: executada na prática pelos merges #50, #51 e #53.
- #36 — Writer/LPAC: o diagnóstico avançou no laboratório e a rota produtiva foi integrada pela PR #50.
- #39 — revisão de gates: refere o candidato anterior à unificação.
- #42 — OpenNotebook: decisão já fixada como ferramenta opcional de microprocessos, nunca orquestrador.
- #38 — documentação: a PR #54 trata a reconciliação documental.

## Frentes realmente ativas

1. PR #54 — reconciliar documentação com o estado atual da `main`.
2. PR #55 — memória FTS5 autenticada na Folha via Host, com Creative e Canonical separados.
3. Aceitação física no PC, modelos/GPU, instalação protegida e power-loss: ainda não executadas.

## Regra permanente

Nenhum laboratório tem autoridade sobre Kernel, Host, Store, Human Gate, Creative ou Canonical. Toda a execução passa pelo Nexus principal.