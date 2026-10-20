# Plano de implementação

**Nota de âmbito corrigida (2026-09-22):** Pedro confirmou que o alvo atual é **F4 deste roteiro técnico — IA efémera sem ação**, após F-1 e F0–F3. `PLANO-DE-TAREFAS-POR-FASE.md` define o protótipo técnico limitado F4. F5–F9 ficam como backlog; o “Alpha completo” histórico não é a entrega atual. A numeração funcional do documento 04 é histórica para este objetivo.

## F-1 — Fundação

- Repositório Git local, rollback e estado operacional.
- Python 3.12 isolado e testes locais.
- Regras permanentes do Cline e proteção de fontes confidenciais.
- Inventário verificado de ferramentas; sem reinstalar o que já funciona.

## F0 — Esqueleto determinístico

1. Evento versionado e serialização canónica.
2. Estado e transição pura, sem relógio ou aleatoriedade implícitos.
3. Event log append-only e idempotência central por `event_id`.
4. Snapshot e restart.
5. Replay de 10 000 eventos com igualdade de hash.
6. Casos: duplicado, inválido, fora de ordem, corrupção, crash durante escrita e alteração de configuração.

## F1–F9

- F1: cognição determinística.
- F2: memórias, Logseq, Final Vault e truth maintenance.
- F3: Activepieces, staging e outbox/retry.
- F4: IA efémera somente leitura.
- F5: capacidades temporárias, sandbox e teste de execução indireta via componente confiável.
- F6: ciclo contínuo, actionability gate, urgência e feedback de confirmação. Meta inicial a validar: pelo menos 80% das intervenções aceites num conjunto de avaliação definido antes do teste.
- F7: domínios e adaptador Logseq fino, sem acoplar o núcleo à interface.
- F8: integração e stress prolongado.
- F9: Alpha completa.

Cada fase inclui toda a regressão anterior. Uma fase não avança com testes falhados.

## Primeira vertical

Depois de F0 básico: uma entrada controlada gera evento, sofre transição determinística, grava estado e produz resultado observável. IA, Logseq, Activepieces e SQLCipher não entram nesta primeira tarefa.
