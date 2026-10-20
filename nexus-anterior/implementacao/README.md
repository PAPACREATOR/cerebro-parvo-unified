# Implementação candidata, não release

O diretório candidata-2026-09-27 contém os nove ficheiros do ZIP revisto exatamente como recebidos. README, TEST_RESULTS e REVISAO_ADVERSARIAL internos são afirmações e resultados da fonte, preservados; a evidência desta sessão está em [auditoria](../auditoria/RESULTADOS.md).

As funções cobrem partes dos 26 contratos de importação. Não implementam toda a arquitetura M1–M14 nem todos os critérios de cada IMP. A suite fornecida tem 34 testes e foi reproduzida; IMP-001 permanece parcial. As funções materialize e delete_authorized_original bloqueiam deliberadamente.

[Estado corrente](../STATUS.md) prevalece para o que foi realmente verificado nesta sessão. Não modificar a cópia preservada para fazer desaparecer falhas históricas; iniciar a implementação de trabalho na microtarefa autorizada, mantendo origem e diff.
