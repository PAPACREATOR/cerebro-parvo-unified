# Sincronização da equipa — 04/10/2026

Pedido humano nesta sessão: «Agora para e consulta o trabalho de equipa consulta tudo sincroniza tudo».
Implementação pausada. Este pedido autoriza a publicação do trabalho local nesta branch de laboratório, levantando o bloqueio anterior de push. Não promove experiências a produção.

## Âmbito verificado

Fetch de todas as branches remotas disponíveis; PRs #7–#13, respetivos comentários/handoffs e Actions associados aos HEADs consultados. Lidos planos e relatórios dos laboratórios, o parser mais recente consultado, diferenças de ficheiros e testes de merge em memória de objetos Git (`merge-tree`, sem alterar branches).

Fotografia de refs e hashes: `SYNC-EQUIPA-2026-10-04.json`. As outras sessões continuam a escrever; resultados abaixo têm commit explícito e não pretendem congelar o trabalho delas. Consulta não significa que outra sessão leu este handoff.

## Mapa comum

| Frente | Commit consultado | Estado e evidência |
|---|---|---|
| Oficial / espelho PC | `1e9e612` | `main` e `pc-full-mirror-20261004` continuam iguais; código novo do PC não recebido por esse espelho |
| Arranque/F013/F014, PR #7 | `6bbf7fe` | Actions Windows/auditoria SUCCESS; também é a ref atual de `integration-lab-20261004` |
| Recovery, PR #8 | `7921fac` | HEAD Windows FAIL por manifesto desatualizado; correção já incorporada na branch bootstrap, não atribuir PASS retroativo à PR #8 |
| Base Lab, PR #9 | `ef69379` | Windows/auditoria SUCCESS; relatório de 1222 casos completos e 16 práticos; PC físico distinto |
| Spiff + Conductor, PR #10 | `829764d` | Actions dedicadas/Windows/auditoria SUCCESS; 5000 casos delimitados, sem prova de todos os contratos multi-passo |
| Desempenho Conductor, PR #11 | `9f1c2b9` | Workflow Spiff+Conductor/P0 SUCCESS, run 37211375610; Windows estava em curso na consulta |
| Verify otimizado, PR #12 | `0067ca3` | FAIL, run 37207356651; caminho da fixture para tools.py inválido, seguido de ausência de status no template |
| Front Door, PR #13 | `6fa3915` → `e6b9140` | Run 37211481235 falhou em L3; L0/L1/L2/shadow passaram e L4 foi skipped. Commits seguintes corrigem pares de intenções e minimizam regras; CI do novo HEAD não confirmado nesta fotografia |
| Alternativa Front Door mínima | `4d91d05` | PT/EN/FR, revisão de ambiguidades; branch alternativa, não fundir silenciosamente com a implementação declarativa da PR #13 |
| Wiki inicial | `b0a82e6` | Executor era placeholder; relatório NOT RUN |
| Wiki complementada, esta sessão | `74f6857` + `713d0c0` locais | 100000 objetos sintéticos; bridge Store/Conductor real: 1098 PASS + regressão 101 PASS Linux; não integração oficial |

## Atualizações importantes para evitar trabalho duplicado

1. O estudo de performance já concluiu que paralelizar `set` muito barato não dá ganho neste ensaio; subprocessos de cola podem custar bastante mais. Não transportar a percentagem de um microbenchmark para o desempenho global do Nexus.
2. `verify` otimizado continua sem PASS. O log mostra `tests/fixtures/../adapters/tools.py` inexistente e depois `dict object has no attribute status`. Diagnóstico para a equipa, sem patch nesta sessão de sincronização.
3. O FAIL L3 consultado era um par `guarda ... guarda ...`, isto é, a mesma intenção tratada pelo teste como conflito. O código posterior já contém correção; repetir gates no HEAD exato antes de fechar a fase.
4. A PR #13 passou entretanto regras para `frontdoor_rules.json` com schema e reaproveitou o adaptador LanguageTool. Também atualizou `integrity.json`. A alternativa mínima usa outro desenho; é preciso comparar comportamento e manutenção, não substituir só por nome de branch.
5. A wiki já possui uma bridge experimental que reaproveita Store.check_candidate/check_commit e Conductor. Não criar outro Store/portão humano. Contexto da bancada atual está limitado a 6000 caracteres; selecionar fontes e fixar hashes.
6. F009 é um contrato de família multimédia, não um schema geral de pedidos/conhecimento. Pode inspirar o molde, mas a ligação Front Door/wiki precisa de contrato próprio, sem contornar schemas.

## Fronteira comum antes de continuar a programar

Entrada humana → parser sem autoridade → intenção/pedido estruturado → Kernel seleciona processo e escopo → contexto verificado → executor → resultado candidato → proveniência → recuperação/navegação → portão humano quando aplicável.

Preservar separadamente: texto original, interpretação do parser, referências de contexto, ID/hash do processo realmente executado, resultado e decisão humana. O JSON atual do request não aceita contexto arbitrário; a extensão tem de ser acordada e testada uma única vez pela equipa.

Divisão proposta para próxima etapa, sem disparar agentes ou tarefas nesta sessão:
- Frente de linguagem: fechar gates do parser e molde, conservar original.
- Frente wiki: fechar contrato de seleção/contexto/proveniência, conservar domínios.
- Kernel: ponto único de validação/dispatch/persistência; evitar modificações concorrentes em Host/Store/schemas/manifesto.
- Performance: só aceitar otimização após equivalência e teste real.

## Sincronização executada e limites

As refs foram atualizadas localmente. Nossa branch é publicada com código, documentação e evidência; nenhuma branch alheia é sobrescrita. Os testes `merge-tree` dos pares consultados não mostraram conflito textual, mas isso não demonstra integração funcional; as branches continuam separadas.

Git CLI consegue ler o repositório público, mas o push falhou por ausência de credenciais na linha de comandos. Publicação utiliza o conector GitHub autenticado; os commits remotos podem ter SHAs diferentes, devendo a igualdade das árvores de ficheiros ser verificada. Os IDs locais acima são preservados como genealogia.

Não houve merge em main, promoção no PC, eliminação, alteração da arquitetura ou reinício de implementação. Drive/PC não foram inspecionados nesta sessão; o espelho remoto disponível continua sem o snapshot local prometido.
