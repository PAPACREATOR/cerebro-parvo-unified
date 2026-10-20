# Matriz de auditoria — visão congelada vs Nexus atual vs Work

Data: 2026-10-04. Esta matriz é documental. Não altera leis nem arquitetura.

| Contrato / visão | Nexus atual | Work PR #7 | Estado | Ação |
|---|---|---|---|---|
| Humano é autoridade máxima | Human Gate ligado a conteúdo/run/destino | preservado | ALINHADO | NÃO TOCAR |
| Creative antes de Canonical | Store.accept escreve Creative; promote escreve Canonical | preservado e testado | ALINHADO | NÃO TOCAR |
| Sem promoção automática | policy + promote exigem HumanDecision | regressões e F013 | ALINHADO | NÃO TOCAR |
| Sem eliminação automática por similaridade | delete bloqueado; protótipo nem expõe eliminação | sem regressão observada | ALINHADO | NÃO TOCAR |
| Markdown/YAML/JSON separados por função | leis + processes + schemas | preservado | ALINHADO | NÃO TOCAR |
| Kernel/Store possui persistência/recovery | Store possui estado e reconciliação Canonical | Work melhorou startup e proveniência; janela de crash externa ainda parcial | PARCIAL | T01–T04 |
| Conductor é executor efémero | adapter sem provider/registry; output+trace | preservado | ALINHADO | NÃO dar memória ao executor |
| IA apenas delimitada | interpret separado; restantes processos proíbem ai_calls | CI não prova modelo local | PARCIAL | testar capability real mais tarde |
| Proveniência ida e volta | check_input/check_candidate/check_commit | F013 + reverse-flow + Windows | ALINHADO no circuito coberto | expandir por capability |
| Restart não fabrica passado | reverse-flow proíbe reexecução na leitura | Work cobre leitura/restart; crash após output antes de accept ainda não | PARCIAL | T01 |
| Instância única por dados | antes pendente | F011 adiciona lock + exclusive port; CI PASS | ALINHADO | repetir no PC LAB |
| Hash Windows em ambiente reduzido | process_environment + workflows | F012 Windows PASS | ALINHADO | repetir no PC LAB |
| Resultado volta ao original | valida hashes e referências | F013 Windows + regressão | ALINHADO | expandir a cada capability |
| Segurança por fases | ambiente reduzido, paths, hashes, gate | ACL/conta real ainda não ligada ao Host | PARCIAL | T08 |
| Windows real como destino | GitHub runner é Windows, mas não é o PC real | docs distinguem runner de instalação pessoal | PARCIAL | C:\Nexus-Lab |
| Lab separado de produção | definido em PR #7/comentários | branch integration-lab criada | PREPARADO | criar/testar C:\Nexus-Lab no PC |
| Spiff | existe apenas no estado local histórico, não no GitHub Work | equivalência pendente | PENDENTE | comparar só routing/loops/gates; nunca persistência |
| 100000 testes úteis | ainda não | plano registado | PENDENTE | depois de contratos críticos |
| Windows + homelab | ainda não integrado | sem circuito completo | PENDENTE | capabilities uma a uma |
| Telemóvel cliente / PC servidor | fase final | não implementado | PENDENTE | depois da integração estável |
| Encriptação/hardening global | fundamentos presentes; camada final não | não concluído | PENDENTE | fase final |

## Regra operacional

Cada linha PENDENTE/PARCIAL é tratada por microprocesso:
`auditar -> reproduzir FAIL -> corrigir mínimo -> ida -> volta -> falha/restart/bypass -> Windows LAB -> registar -> próximo`.

Linhas ALINHADAS e já provadas são protegidas contra alterações não necessárias.
