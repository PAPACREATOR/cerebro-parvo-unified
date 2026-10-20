# Protected provisioning contract (draft)

O provisioning externo só poderá ser reaberto se cumprir todos estes pontos:

1. Sem privilégios de administrador.
2. Sem criação de utilizadores, serviços, tarefas agendadas, regras firewall, PATH global ou políticas do Windows.
3. Escrita limitada a C:\Nexus-Tools e subpastas temporárias sob esse root.
4. Dry-run por defeito; alterações apenas com -Apply explícito.
5. Git/uv/Python são pré-requisitos; o instalador não usa winget nem instala pré-requisitos globais.
6. Repositórios externos sempre fixados a commit auditado.
7. Instalação em staging; só promove para pasta final após verificação.
8. Instalação existente diferente/suja = BLOCKED, nunca overwrite automático.
9. Falha = apagar apenas staging criado nessa execução; instalações anteriores permanecem intactas.
10. Não arrancar ACE-Step, Forge, OpenNotebook ou Avatar durante provisioning.
11. Não descarregar checkpoints/modelos automaticamente sem licença/hash aprovados.
12. Relatório JSON com plano, commits, licenças, ficheiros criados e resultado.
13. Testes reais Windows: dry-run sem efeitos, apply sintético limitado ao root, rollback após falha, repetição idempotente, path traversal/symlink/junction bloqueados.
14. Só depois destes testes o marcador NEXUS_PROTECTED_PROVISIONING_PENDING pode ser removido dos entrypoints específicos.

Este contrato não altera M1–M14 nem a autoridade: ferramentas externas continuam autoridade NONE.