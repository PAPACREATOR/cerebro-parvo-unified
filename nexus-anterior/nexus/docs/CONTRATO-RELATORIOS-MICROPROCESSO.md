# Contrato de relatórios por microprocesso

Data: 2026-10-04

Cada microprocesso Nexus deve deixar um relatório curto e verificável. O relatório é memória técnica; não altera leis nem arquitetura.

## Campos obrigatórios

| Campo | Conteúdo |
|---|---|
| ID | identificador único da tarefa/teste |
| Data | UTC/local quando relevante |
| Branch/commit base | ponto exato antes da alteração |
| Objetivo | contrato a provar |
| Arquitetura afetada | responsabilidades M1–M14/Kernel/capability; ou "nenhuma" |
| Ficheiros lidos | fontes usadas na auditoria |
| Comparação | Nexus atual vs Work/Codex vs contrato esperado |
| FAIL reproduzido | comando/run/teste e resultado exato |
| Causa | causa observada; não hipótese apresentada como facto |
| Correção | alteração mínima aplicada |
| Ida | pedido -> execução -> resultado |
| Volta | resultado -> proveniência -> processo -> input |
| Segurança | bypass/adulteração/permissões/falhas testadas |
| Restart | janela de crash testada e estado após novo Kernel |
| Regressão | contagem PASS/FAIL e run |
| Windows LAB | PASS/FAIL/NOT RUN |
| Limites | o que o PASS não prova |
| Aprendizagem | padrão reutilizável |
| Próximo passo | uma tarefa concreta, sem duplicação |

## Estados

Usar apenas:
- PASS
- FAIL
- BLOCKED
- NOT RUN
- PARTIAL

Não usar "feito" ou "funciona" sem evidência correspondente.

## Regra de comparação

Quando houver duas implementações ou duas vias:
- conservar ambos os resultados;
- comparar por input/hash/versão/estado;
- classificar AGREEMENT / CONFLICT / UNKNOWN / FAIL;
- não escolher silenciosamente um lado.

## Regra de promoção

Um relatório remoto pode marcar `PASS REMOTO`. Só após `C:\Nexus-Lab` repetir o contrato crítico pode ser considerado candidato a `PROMOTABLE` para produção.
