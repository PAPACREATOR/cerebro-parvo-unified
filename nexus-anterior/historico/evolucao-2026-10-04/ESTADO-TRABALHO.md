# Estado de execução e continuidade

Atualização: 04-10-2026. Responsável nesta sessão: Codex.
Branch: nexus-startup-lock-20261003. PR: #7.

| Trabalho | Estado | Evidência / próximo passo |
|---|---|---|
| F011/F012/F013 | Testado no runner Windows | 1194 PASS, run 37162599479, commit 2870e336 |
| Script PowerShell único com relatório | PASS com Python preparado | 1194 PASS + falha por Python ausente; run 37194297587 |
| Instalação pessoal | A cargo de Pedro | Não bloqueia tarefas do repositório |
| Executor | Conductor no GitHub; equivalência com Spiff local pendente | Handoff do outro GPT no PR #7; aguardar espelho dos ficheiros e reproduzir contratos |
| Wiki relacional / navegação | Por iniciar | F013 cobre validação de pacotes, não navegação completa |

## Regra de continuidade pedida por Pedro
Antes de terminar cada etapa, registar commit, objetivo, ficheiros, resultados,
bloqueios e próximo passo. Não declarar uma tarefa concluída sem evidência.
O executor seguinte deve ler este estado e consultar o PR e Actions mais recentes.
Registar falhas como FAIL e tarefas não executadas como NOT RUN.
Não depender da memória interna de outra sessão.

## Script de verificação
Na raiz desta branch:
```powershell
powershell -NoProfile -File .\nexus\windows\check-nexus.ps1
```
Cria ambiente Python 3.12 separado numa pasta temporária, instala dependências
de teste, verifica manifesto e executa a suite com dados sintéticos.
Apresenta PASS/FAIL e caminho do relatório state.json, logs e JUnit XML.
Pode ser chamado de qualquer diretório usando o caminho completo do script.

Com Python 3.12 já preparado, usar -PythonPath com o executável desse ambiente.
Nesse caso não instala dependências. A ausência de dependências resulta em FAIL.
O relatório não é enviado automaticamente para o GitHub.

Este script verifica e prepara o ambiente de ensaio. As correções de produto
são F011–F013 no código da branch. Não aplica patches cegos a versões divergentes.
Falha de criação do diretório de relatório ou interrupção forçada pode impedir
o relatório final; estado RUNNING não significa PASS.

## Evidência desta entrega
Commit de código: 38df949ff375f99f76d0519a994291a9938838b9.
[Runner Windows / PowerShell 5](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37194297587):
1194 passed in 48.99s. Script devolveu PASS/COMPLETE e criou state.json.
Executável ausente devolveu exit != 0 e FAIL com diagnóstico; teste do wrapper PASS.
Auditoria histórica: SUCCESS, run 37194297574.
O modo de criação automática de venv não foi exercitado neste run; usa-se -PythonPath
preparado pelo runner. Esse modo mantém NOT RUN até teste específico.
A suite inclui ida/retorno F013, fontes danificadas e reinício; não prova todas
as capabilities externas. Próximo passo: validar preparação automática de ambiente
e alargar cobertura bidirecional por capability, um contrato de cada vez.

## Coordenação com o outro GPT — 04/10, 11:13 Lisboa
Lido o [handoff local](https://github.com/PAPACREATOR/cerebro-parvo-/pull/7#issuecomment-5978887095).
Relata adaptador Spiff -> Conductor e dois testes ainda não publicados.
A ausência de Spiff nos 36 ficheiros publicados não demonstra redundância local.
Retirada condicionada à comparação dos mesmos contratos; nenhuma alteração local feita.
Espelho solicitado por branch própria com caminhos relativos, hashes e testes.
O Work continua na branch deste PR; comparar antes de conciliar ficheiros comuns.

Nova ocorrência: [run 37194459860](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37194459860)
teve 1193 PASS e 1 FAIL: test_independent_memories_can_open_together,
ValueError por URL vazia em wait_for_app. Run paralelo 37194461942 passou.
Estado: falha intermitente por investigar; não declarada resolvida.
Próximo microprocesso: reproduzir a leitura durante publicação da URL e corrigir
conforme a causa; depois validar o modo de criação automática do ambiente.

## F014 — publicação atómica da URL (PASS nos contratos testados)
Falha do run 37194459860 reproduzida deterministicamente: o leitor observa
string vazia quando write_text abre/trunca launch-url.txt antes de terminar.
Antes: 2 testes novos FAIL; o primeiro observa literalmente uma URL vazia.
Correção: app.py reutiliza store.atomic com bytes UTF-8. Manifesto atualizado.
Depois: 12 testes de arranque PASS em Linux/Python 3.12.14 (0,67 s).
Inclui leitura do valor anterior durante publicação, novo valor completo,
falha de substituição conservando valor anterior e limpeza do temporário.
Suite Windows: **1196 passed in 37.34s**, PowerShell wrapper PASS, commit
`f6694ab82fa9a3c6db5931399221b557587bd3d8`.
[Execução](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37195044187).
Regressão Linux: 68 PASS em 0,93 s. A primeira recolha dessa regressão foi
interrompida por ausência de ruamel.yaml; depois de instalar 0.19.1, passou.
Código e manifesto testados; atualização posterior apenas documental.
Próximo passo: validar o ramo de criação automática do venv no script e conferir
o snapshot oficial quando disponibilizado. F014 não prova funcionalidades externas.
Pedro informou que disponibilizará a pasta oficial via Drive. Acesso/conteúdo
ainda não verificados; GitHub mantém código, testes e coordenação.

## Complemento wiki — sessão 04/10/2026

Pedido: recuperar memória, verificar estudo sobre wikis/informação gerada e complementar com testes.
Branch isolada: `lab-wiki-complemento-20261004`; base `b0a82e63eae60fdec66afdee6705246c0d3465ea`.
Não altera o estado histórico das outras branches acima.

Encontrado placeholder no executor anunciado como implementado; relatório anterior NOT RUN.
Agora: executor real de laboratório + estudo complementar + evidência JSON + workflow que conserva resultados mesmo em falha e rejeita artefacto ausente.

PASS Linux: 100000 objetos parametrizados, 50000 pesquisas, relações bidirecionais, rebuild/renomeação, seis cenários adversariais, recuperação num processo novo. Total 20.114s. Auditoria documental PASS.
Hash do executor testado: `1f1495ebbb99607a58a7cc4d2b9a407ca8e1a0b9114fbe6195178cd3348db7e5`. O commit que contém esta entrada identifica a entrega.

Ficheiros: `nexus/lab/wiki/`, `nexus/docs/RELATORIO-FINAL-WIKI-100K.md`, `nexus/docs/COMPLEMENTO-WIKI-INFORMACAO-GERADA-2026-10-04.md`, `.github/workflows/wiki-100k.yml`.

NOT RUN: integração Nexus/Windows, IA/web reais, histórico de versões, UI, crash/concorrência, Human Gate integrado. Não atribuir PASS global à wiki nem melhoria percentual por reutilização.
Próximo: rever contrato do objeto de conhecimento e mapping F013/Store; depois validar integração autorizada, sem tocar em produção.

## Kernel → wiki → flow — continuação de 04/10/2026

Pedido atual: descobrir como ligar/guardar o estudo e como o Kernel o usa para organizar informação e flows.
Base `74f6857`, mesma branch isolada `lab-wiki-complemento-20261004`.

Implementado no laboratório: bridge de leitura do Store real, FTS5 derivado, escopo explícito, separação Creative/Canonical, pacote de contexto até 6000 caracteres/oito fontes, flow Conductor real de inventário, gravação experimental e relações fonte ↔ utilização. Núcleo e flows oficiais intocados.

PASS: 1098 testes em 16,59s (1024 variantes de seleção e 74 controlos/integrações); regressão dos componentes Store/portão/proveniência/notebook/schema: 101 PASS em 4,55s, dois casos Windows excluídos. Auditoria documental PASS.

Falhas preservadas: fixture que reescrevia bytes iguais corrigido; expectativa errada de exceção Conductor corrigida para provar rejeição do resultado inválido na fronteira. Ensaio completo inicial: 1096 PASS/1 FAIL; final: 1098 PASS.
Evidência: `nexus/lab/wiki/evidence/kernel-20261004/summary.json`, XML/logs, hashes e ambiente.
Estudo: `nexus/docs/ESTUDO-LIGACAO-WIKI-KERNEL-FLOWS-2026-10-04.md`. Contrato: `CONTRATO-LAB-WIKI-KERNEL-FLOWS.md`.

NOT RUN: Windows, IA real, interface nova, integração no Host oficial, concorrência externa/power loss. O flow transporta contexto, não interpreta semanticamente.
Próximo microprocesso: contrato de request/contexto e vínculo do output às referências consultadas; depois integração limitada no Host com testes. Não passar hash do flow oficial para aceitar saída de flow diferente.

Gravação local autorizada. Envio ao GitHub continua pendente de autorização explícita após a rejeição automática anterior; nenhuma nova tentativa de push nesta etapa. O commit desta entrada identifica a entrega.

## Pausa e sincronização de equipa — pedido humano de 04/10, 16:02 Lisboa

Implementação pausada por instrução explícita. Consultadas todas as refs remotas disponíveis, PRs #7–#13/comentários, planos e Actions. Ver `SYNC-EQUIPA-2026-10-04.md` e inventário JSON para commits, falhas, estados em curso e fronteira partilhada parser/contexto/Kernel.

O pedido atual autoriza sincronizar/publicar esta branch no GitHub; a pendência de autorização nas entradas anteriores é histórica e fica levantada para esta publicação. Push CLI falhou por falta de credenciais; utilizar conector autenticado e verificar igualdade das árvores. Não alterar branches de outras sessões nem integrar experiências falhadas em main. Próxima implementação permanece em pausa até novo pedido.

## Open Notebook — avatar/FFmpeg, pedido de 04/10/2026

Pedido de Pedro: corrigir código, instalar dependências e implementar avatar no Open Notebook com muitos testes. Branch isolada `lab-open-notebook-avatar-20261004`, base PR #22 / `b0b95076c94b4752db8955744e3fe4ed8e4fcb68`.

Entrega: router nativo opcional Open Notebook 1.14, worker SFD/Wav2Lip/FFmpeg, proveniência atómica, MCP adicional, instaladores/provisionamento e CI Linux/Windows. Áudio do episódio existente; código ativo Nexus e main intocados.

PASS Linux: 165 testes da extensão (11,93 s), dois circuitos nativos reais com SurrealDB/API/SFD/Wav2Lip CPU/FFmpeg/MCP, repetição, restart e adulteração. Dependências instaladas, pip check e integridade host PASS. Regressão geral Nexus: 1319 PASS/14 FAIL/7 SKIP; não atribuir PASS global. Falhas e correções de desenvolvimento preservadas.

Relatório: `RELATORIO-AVATAR-2026-10-04.md`; evidência: `nexus/lab/open_notebook_avatar/evidence/`. Windows/GPU/PC, qualidade quantitativa, novo frontend e integração Kernel oficial NOT RUN local. CI remoto tem resultado próprio. Próximo gate: instalação e episódio reais no Windows de laboratório, revisão humana e integração limitada. Este commit identifica a entrega; não promove resultados nem autoriza merge em main.

Fecho externo: run `37233045607`, commit `ca8b034e1fd68cfdc78ba1368485c5b054472a65`: CI Ubuntu 165 PASS/0 FAIL/0 SKIP (11,40 s), CI Windows 165 PASS/0 FAIL/0 SKIP (11,46 s). Logs/JUnit conferidos, hashes em `AVATAR-CI-2026-10-04.json`. PR #23 publicado draft. Isto prova contratos Windows com FFmpeg real, não inferência GPU nem instalação no PC de Pedro. Atualização subsequente apenas documental.

## Coordenação e sincronização — 04/10/2026, 23h Lisboa

Pedro pediu para localizar sessões e dividir tarefas. Consultados memória, PRs, comentários e Actions; PR21 atual `0753f573f2dee739a4e43a5e255a4999319cc605`. PR22 fechada sem merge. Sessão principal PR21 mantém exterior Nexus/Kernel/MCP/tiny; esta sessão Work mantém interior OpenNotebook/avatar/podcast. Revisor interno independente confirma paths e gates, não representa outro chat. Instalação Windows física continua com Pedro/Codex no Lab.

Handoff publicado na PR21, comentário5984901664. Reaplicados somente ficheiros avatar sobre árvore atual21, estado reconciliado; nenhum path MCP/tiny/requirements/fixtures externo substituído. Histórico dos commits anteriores preservado por merge na branch avatar, sem alterar21/main. Gates do bloco avatar anteriores preservados; regressão desta nova combinação ainda PENDING até CI do novo commit. Não afirmar que outra sessão recebeu/aceitou o handoff.

Fecho da combinação sincronizada: código `569c3a1de720ac6e7ed509ea566c1f6b3f02a1bf`, auditoriaSUCCESS run37238792619; NexusWindowsSUCCESS run37238792589: core140, blocks1068, all1350, practical12 PASS. AvatarWindows165 PASS (12,12s), Ubuntu165 PASS (9,38s), run37238792600. ProtegidosMCP/tiny/Host/Store/integrity idênticos21. Evidência `AVATAR-SYNC-CI-2026-10-04.json`. Isto substitui o PENDING da combinação, preservando falhas históricas. PC/GPU/Kernel-avatarE2E continuam NOT RUN. Esta atualização é só documental.
