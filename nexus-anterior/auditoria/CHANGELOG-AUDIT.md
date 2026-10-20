# CHANGELOG — Auditoria de Trabalho

## Ciclo 0 — 2026-10-07
- Problema: Os ficheiros obrigatórios de estado persistente definidos pelo contrato atual não existiam na branch de trabalho.
- Causa: O estado operacional anterior era mantido noutro documento e o contrato atual introduz três artefactos específicos.
- Hipótese: Criar os três ficheiros sem alterar arquitetura nem código permite retomar de forma verificável e independente da conversa.
- Ficheiros alterados: `auditoria/WORK_STATE.md`, `auditoria/TEST_MATRIX.md`, `auditoria/CHANGELOG-AUDIT.md`.
- Teste criado/alterado: Nenhum; ciclo de bootstrap documental.
- Comando executado: Inspeção GitHub REST da branch, árvore, PR #23, documentos de estado e commits.
- Resultado: Branch `lab/windows-full-install-20261006` confirmada 124 commits à frente do HEAD da PR #23 e como descendente direto dessa baseline; ficheiros de estado obrigatórios ausentes.
- Revisão do diff: Apenas três novos documentos de auditoria; sem alteração de runtime.
- Regressões: NÃO EXECUTADAS neste ciclo documental.
- Decisão: ACEITE.
- Próxima ação: Diagnóstico do núcleo real e execução dos testes relacionados antes de qualquer correção de código.
