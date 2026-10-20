# REVISÃO ADVERSARIAL — CÉREBRO

Data: 2026-09-27

## Método
Os testes originais não foram usados como prova suficiente. Foi criada uma bateria adversarial separada, baseada nos contratos/invariantes, destinada a fazer a implementação falhar.

## Primeira ronda adversarial
Resultado antes das correções: **10 FAIL / 11 PASS**.

Falhas reais encontradas:
1. Retry da quarentena aceitava ficheiro preexistente com bytes diferentes.
2. IDs correlacionados não eram validados como UUID.
3. Reutilização de attachment_id não exigia prova da mesma operação.
4. ZIP corrompido podia ser classificado como ZIP válido.
5. Envelope externo podia injetar campo de autoridade.
6. Classificador podia devolver string arbitrária em vez de ContentClass.
7. Creative não verificava coerência operation_id ↔ attachment.
8. Proveniência aceitava ferramenta sem identidade/versão.
9. Evidência contraditória de commit podia resultar em COMMITTED.
10. Era possível aprovar proposta de eliminação cujo alvo não estava resolvido/existente.

Todas foram corrigidas sem remover os testes que as descobriram.

## Segunda ronda
Foram adicionados testes de:
- mutação da origem entre RECEIVE e VALIDATE;
- limites exatos de tamanho;
- vazio;
- duplicação sem eliminação;
- extensão enganadora;
- ambiguidade de adaptador;
- correlação incompleta;
- bloqueio de IMP-019;
- REVIEW não apresentado como importado;
- precedência de RECOVERY_REQUIRED;
- autorização não extensível;
- bloqueio de IMP-026.

## Resultado atual
[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m                                       [100%][0m
[32m[32m[1m34 passed[0m[32m in 0.06s[0m[0m

## O que este resultado NÃO prova
Não prova os 26 IMPs completos nem integração real com Activepieces/Second-Brain/LibreOffice/Zotero. IMP-019/G10 e IMP-026 continuam deliberadamente bloqueados porque a especificação ainda contém decisões POR DEFINIR. Também não foram ainda executados testes reais de crash de processo/energia, SQLite+filesystem, concorrência multiprocesso ou Activepieces real.

## Estado responsável
- Código inicial: revisto e endurecido.
- Testes unitários/contrato locais: PASS.
- Testes adversariais locais: PASS.
- Integração externa: NOT RUN.
- Crash/recovery real: NOT RUN.
- M1–M14 end-to-end: NOT RUN.
- Sistema completo: NÃO FECHADO.

FAIL/SKIP/NOT RUN não são contados como PASS.
