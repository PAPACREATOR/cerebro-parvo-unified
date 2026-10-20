# Nexus — ponto de situação atual

## Retoma de 11-10-2026 — ligação existente e resultado desconhecido

Base desta frente: `main` `e3833856ed8ebc8947c4229344bab3be3f54654a`, com a PR #57 integrada. A árvore integrada é idêntica à candidata `e9fc98a`; os três workflows pós-merge (Windows, Auditoria e CodeQL) passaram no próprio `e383385`, com checkout conferido nos cinco jobs. A prova completa anterior de 10 workflows/21 jobs, Writer real e Chrome Windows/Linux permanece na PR #57.

Pedido humano atual: continuar, reler o que foi estudado/testado e aproveitar a ligação Folha → aprovação humana → Host/Kernel → função → resultado quando essa ligação estiver provada. Não acrescentar um roteador/framework para duplicar funções existentes. A releitura das decisões de 11/10 mantém Pyperplan rejeitado e MAF/LangGraph apenas em estudo/bancada, com integração por aprovar. Não foram reinstalados motores nem recuperadas bancadas eliminadas.

Microprocesso atual, em branch própria `fix/gateway-result-unknown-20261011`: reproduzir o alerta da issue #39 sobre perda de resposta HTTP. A ausência de resposta após `confirm-run` ou `approve` não prova ausência de execução/promoção. O gateway dizia «Nenhuma operação executada»; a Folha podia ainda sugerir tentar novamente. O contrato exige resultado desconhecido, consulta explícita do histórico e nenhum reenvio automático ou reaproveitamento de ticket.

FAIL-first preservado no commit [`351571579d75c5a8046ce63dc4adb50a663b5b5d`](https://github.com/PAPACREATOR/cerebro-parvo-/commit/351571579d75c5a8046ce63dc4adb50a663b5b5d), sobre os bytes de produção da base: **13 FAIL / 29 PASS Node** e **1 FAIL / 1 PASS Python**. Os sete cenários de transporte usam sockets reais e efeitos sintéticos, incluindo timeout real de 30 segundos, enquadramento truncado e cancelamento; não executam ferramentas. Os seis cenários UI exercitam as duas confirmações e perda de ligação/JSON/resposta UNKNOWN. O E2E Python adicional usa app/Host/Store originais, dados temporários e aprovação humana explícita: a promoção real fica `PASS`, a resposta é cortada pela fronteira de rede e o gateway ainda afirma ausência de operação. Recusa prévia mantém `HUMAN_REQUIRED`; não há monkeypatch do núcleo.

Correção mínima no transporte/apresentação existentes:

- `server.js`: falha de entrega antes dos headers devolve HTTP 503 com `outcome: UNKNOWN` e mensagem humana para consultar o histórico. Depois dos headers, o stream quebrado termina por `node:stream.pipeline`, em vez de deixar a resposta pendurada. Fechar o cliente liberta a ligação de transporte; não cancela uma operação do Host nem a repete.
- `nexus/ui/app.js`: perda de ligação ou JSON truncado em `confirm-run`/`approve`, e resposta de erro UNKNOWN, apresentam «Não foi possível confirmar o resultado. Consulta os trabalhos anteriores antes de repetir o pedido». Os tickets consumidos continuam consumidos, o material humano é conservado e nenhum reenvio é acrescentado. UNKNOWN descreve a entrega HTTP; não altera o estado persistido nem concede aprovação.
- Testes: sete cenários de rede, seis cenários UI e um E2E adicional de promoção real/recusa/reconciliação sem replay; o workflow existente inclui a nova suite de falhas. A verificação estática antiga exigia literalmente `.pipe()`: a regressão preservou **1 FAIL / 111 PASS / 1 SKIP** até atualizar essa asserção para `pipeline()`. O contrato de autoridade e os testes funcionais permanecem exigidos.

Após correção: **42 PASS Node**, dois smoke UI PASS e **112 PASS / 1 SKIP** na seleção Python de fronteira única, gateway/Host real, pesquisa HTTP, Writer/pré-execução, portões genéricos, escolha de capacidades e sintaxe. O skip corresponde ao gate exclusivo de Windows. O E2E gateway/Host teve **2 PASS** e está incluído na seleção, não se soma como prova independente. Integridade: **40 hashes conformes**, mesmas entradas, só `ui/app.js` atualizado; nenhum ficheiro de produção Python ou dependência alterado.

Primeiro candidato remoto [`0a2e3ceb9e078f2e46b7053a1601e58f2b03f6ab`](https://github.com/PAPACREATOR/cerebro-parvo-/commit/0a2e3ceb9e078f2e46b7053a1601e58f2b03f6ab), [PR #58](https://github.com/PAPACREATOR/cerebro-parvo-/pull/58): gates funcionais concluídos verdes, mas o [check CodeQL separado](https://github.com/PAPACREATOR/cerebro-parvo-/runs/114501716137) ficou **FAIL**, apesar do workflow de análise SUCCESS. Anotações: `Partial server-side request forgery` na chamada HTTP do novo servidor de falha do teste e `HTTP Response Splitting` na cópia do Content-Type. O resumo indica um alerta crítico e um médio. Este candidato não tem PASS global e não foi integrado.

Correção da fixture, sem supressões: caminhos/métodos escolhidos de cinco rotas concretas do teste, incluindo o run criado pelo Store original; Content-Type fixo por tipo de resposta, sem copiar headers recebidos. Acrescentadas recusas diretas de URI absoluta, travessia, query extra e método fora da rota, sem efeitos nem promoção. Mantidos os bytes/status do Host, a perda real da resposta aprovada, a consulta do histórico e a recusa de replay. Após esta alteração, a seleção Python repetiu **112 PASS / 1 SKIP**. A produção de `server.js`, Folha e todos os 40 hashes permanece idêntica ao primeiro candidato; apenas teste e este registo mudam. Referências primárias: [SSRF parcial](https://codeql.github.com/codeql-query-help/python/py-partial-ssrf/) e [response splitting](https://codeql.github.com/codeql-query-help/python/py-http-response-splitting/). A confirmação estática da correção depende do novo CI.

Próximo gate: publicar a correção isolada e conferir todos os workflows e check runs aplicáveis, incluindo o check CodeQL separado, e o checkout real no mesmo SHA antes do merge autorizado pelo pedido humano «se der verde push e merge». A prova remota e o estado de integração serão registados na PR, sem criar outro commit apenas para mudar o SHA do relatório. Kernel, Host, Store, contratos, políticas, MCP e adaptadores permanecem intactos. A issue #39 continua aberta, com revisão independente por provar. A prova de falha real cobre a promoção pelo Host; os efeitos nos testes de execução/timeout Node são sintéticos. Não afirmar geração multimédia real, segurança do PC ou produção completa dos quatro produtos a partir destes gates. Pesquisa/produção final e controlo autorizado das proteções do Windows continuam pendentes em fases próprias.

## Folha limpa e preparação dos quatro produtos — retoma de 11-10-2026

Prioridade humana recebida às 20:45 de Lisboa: abrir uma folha vazia, reduzir os controlos e organizar Texto, Podcast, Música e Curta pelo trabalho anterior à geração. Este pedido passa à frente da revisão geral de sintaxe/contratos preparada na PR #54. A fase documental daquela PR tem seis workflows SUCCESS no SHA `85bed0097eaa8dff279e58339c230126c9ae501b`, continua isolada e sem merge.

Base inicial desta fase de interface: `b798d7bf441efb7c9af9ab1da924b5b04310f23c`. Na retoma de 11-10, conferiu-se a integração da PR #55 e reconciliou-se a branch própria `ui/folha-limpa-preparacao-20261010` com a main `fc3c48a5cb9a594ae4de0fc790fd586147d91de4`. O gateway e a pesquisa autenticada já integrados foram preservados. O ZIP enviado foi lido como referência e preservado. Não foi editada a frente de outra sessão.

Pedido humano reforçado às 09:55 de Lisboa: entregar primeiro o relatório; o utilizador vê apenas a Folha, o processo humano e os resultados. Não mostrar ferramentas ou detalhes internos na interface. A pesquisa apresenta trabalhos aprovados/rascunhos, sem nomes de processos ou IDs. A revisão conserva pedido, ficheiro e conteúdo humano; tickets, hashes e diagnósticos continuam na evidência original. Os dois portões humanos permanecem distintos e obrigatórios.

### Contrato e implementação desta fase

- Arranque: página branca, editor vazio, sem exemplos, cartões, histórico aberto, chamadas de API ou botões visíveis. O menu discreto conserva nova folha, anexar, retomar preparação e histórico. Os controlos do pedido aparecem após escrita ou anexo.
- Preparação: pedido de criação → produto reconhecido ou escolha humana em caso de ambiguidade → brief → Ideia → Pesquisa → Plano → Guião/texto → plano de Produção → revisão da preparação. Objetivo, público, tema e formato são exigidos antes de rever a primeira etapa; os outros campos conservam tom, duração, data de corte e fontes permitidas.
- Material: notas e fontes são entradas humanas. Mudar pedido, brief, fonte ou material anterior retira as revisões posteriores e conserva o texto. O rascunho pode ser retomado e exportado como JSON; a exportação declara `produced: false`. Revisão de preparação não cria uma aprovação Kernel nem publica em Canonical.
- Continuação: reenviar a folha em preparação conserva brief, notas, revisões e etapa atual; o mesmo pedido retoma também a preparação depois de consultar outro resultado. «Nova folha» permite começar outro trabalho. Na revisão final, uma regressão nova reproduziu 1 FAIL local sobre `cf1e522`: o botão principal podia reiniciar o rascunho. Foi corrigido apenas no script UI e acrescentada prova no Chrome real; os portões e o runtime não mudaram.
- Ferramentas: os dez comandos registados continuam a usar interpretação, ticket pré-execução, confirmação humana, Host e segunda decisão de aprovação. Os nomes dos programas foram retirados dos controlos; pedido e ficheiro ficam na revisão. Apresentação dos resultados traduz apenas rodapés/metadados fixos emitidos pelos adaptadores, preservando conteúdo livre, ficheiros descarregados e binding do original. Respostas tardias não substituem uma nova folha nem abrem uma aprovação antiga.
- Persistência de trabalho: preparação em `sessionStorage` quando disponível, com fallback em memória se o navegador impedir armazenamento. Este fallback conserva uma sessão previamente fornecida pelo Host, mas nunca inventa credenciais ou aprovação. Fechar a sessão do navegador pode perder o rascunho; exportar conserva uma cópia. Os bytes dos anexos não são guardados neste rascunho da interface.

### Reconciliação do transporte e integridade

Na base inicial `b798d7b`, `server.js` fabricava runs, relatórios e PDF sem Host. Entretanto a PR #55 corrigiu essa fronteira e integrou pesquisa FTS5 autenticada. A solução experimental desta fase foi retirada e reutiliza-se o `server.js` da main byte a byte: transporte exclusivamente loopback, backend Python explícito (`NEXUS_BACKEND_PORT`), sem execução, memória ou aprovação própria. A rota de pesquisa da main foi conservada, alterando somente a apresentação humana. Nenhuma rota direta ou credencial automática foi acrescentada.

O manifesto foi atualizado apenas para os três assets UI alterados, preservando os hashes Python integrados pela PR #55. Nenhum ficheiro Python foi modificado: Kernel, Host, Store, contratos, política, adaptadores e binding humano conservam os bytes da main `fc3c48a`. O servidor Node não substitui a instalação nativa do Nexus.

### Prova e limites

Prova local inicial antes da reconciliação: 27 PASS Node; 88 PASS / 1 SKIP Windows nos gates Python relacionados; 4 PASS na auditoria de sintaxe/JSON. Estas contagens pertencem à árvore inicial, não provam a árvore reconciliada. Na árvore reconciliada: 29 PASS Node (23 preparação/revisão e 6 transporte), mais os dois smoke existentes; 116 PASS / 1 SKIP Windows nos gates Python de seleção, execução, memória/Host, sintaxe e documentação. O E2E Node → app Python → Host/Store correu localmente com o gateway integrado. Verificação documental: 47 ficheiros preservados, 84 ligações válidas. Os 40 hashes passam; só os três hashes UI mudaram; Python, gateway e histórico permanecem byte a byte iguais à base. As regressões novas cobrem conservação do trabalho ao continuar, apresentação dos resultados, evidência preservada e revisão sem detalhes de ferramentas. A prova remota da árvore final fica na PR; ensaios e subconjuntos não se somam como inputs distintos.

Validação visual local: NOT RUN; não há Chrome instalado utilizável. Foi acrescentado ao CI existente um teste Chrome real por HTTP servido pela aplicação Python original, em Windows/Linux, com dados temporários, para arranque vazio, quatro briefs, seis etapas, exportação, retoma, largura pequena e ausência de chamadas a ferramentas durante preparação. As imagens e o resultado remoto ficam nos artefactos e na PR desta fase. Antes de declarar esta fase verde, conferir todos os workflows aplicáveis e o checkout do mesmo SHA; sem merge nesta fase.

**Continua pendente:** pesquisa automática com fontes/factos verificados; ligação de OpenNotebook/Zotero/LanguageTool à preparação; estudo comparativo de Local Deep Research e GPT Researcher; produção final DOCX/PDF, áudio, música e MP4 a partir desse trabalho. Os produtores atuais de planos não foram transformados em geradores. A fase seguinte deve avaliar pesquisa delimitada e compatibilidade dos contratos num contexto separado, antes de instalar motores ou lhes entregar dados.

## Histórico anterior preservado

As secções seguintes conservam as decisões e a evidência das datas indicadas; não substituem a prioridade e a base acima.

## Convergência técnica Work — 08-10-2026

Pedido corrente: convergir a PR #32 num único produto Windows, seguindo #31, #32, #34 e #33. Work altera código/testes e regista operação; a PR #34 conserva arquitetura/documentação/auditoria. Os relatórios datados abaixo continuam como história; não validam o HEAD corrente.

Candidato único: [PR #32](https://github.com/PAPACREATOR/cerebro-parvo-/pull/32), branch `cleanup/llamacpp-only-20261007`, base `lab/windows-full-install-20261006` (`90683cd3744db074c4ea3b3c170aad6218f2b8ed`). Esta retoma parte do HEAD `a13d316117024ffc7923bcfc49d5517e8184828e`, que fixou o checkout do Front Door Lab. A correção anterior de interpretação foi `dfbd7c9b7d3b48ef5af82f0979e3c896939ee22b`, depois do baseline `b4d50ab8469cf60dfa3228c7c34ef9a1285ac827`. O HEAD exato e a matriz concluída de workflows devem ser conferidos no comentário de continuação da PR: um novo commit exige repetir todos os gates aplicáveis. **Sem PASS global enquanto existir um FAIL ou gate por executar. Sem merge em main.**

`main` observado: `aeeb6f662a8282b3793708aa3e6782ef20d2d0ca` (mudança documental externa; não houve merge do candidato). PR #31: `628359cb4dfc363734894e0724eba25fb164acd8`; PR #34: `2c91ad036f94c03777183d60b4c977a4ee9dc68e`. Nenhuma PR sucessora encontrada na recuperação de 08-10. #31 fornece genealogia dos contratos transacionais; não foi transplantado outro Kernel. Os apontamentos CodeQL dessa PR sobre `Path`/`tmp_name` não usados permanecem documentados como dívida estática histórica, sem FAIL funcional que justifique tocar nessa implementação.

### Ciclo Work — interpretação conservadora antes da integração

Pedro confirmou a divisão por repositórios: Work mantém a PR #32; Codex mantém
`nexus-writer-lab`; a Folha funcional mantém `nexus-folha-lab`. Clonar, comparar e
testar numa cópia Work é autorizado; editar os laboratórios dos outros ou copiar
automaticamente os seus patches não é. O checkout local antigo, incluindo dois
testes não rastreados, foi preservado; alterações preparadas numa worktree isolada.

Fontes recuperadas: Front Door E2E histórica `7006184d1148faeefae2ba5b27a41a0d0e4dec60`
e Folha `116b2dcea97e7bc8b5ace414e3f53243ff770bd6`. Parser, regras e schema do
baseline b4d50ab são idênticos aos da branch E2E histórica; não era necessário
transplantá-los. A Folha forneceu a proteção inicial de negações/citações, adaptada
e testada no Work, sem copiar o seu servidor, UI, IA ou backend.

FAIL-first: commit `184954f29722b2c0e9fe832aaee6b7f86fa2cb3f` acrescentou 28 casos; execução contra o parser anterior
produziu **22 FAIL / 6 PASS**. «Não guarda esta nota» e instruções citadas tornavam-se
RESOLVED. A primeira adaptação isolada passou esses casos, mas a revisão encontrou
outros FAILs: uma hint tiny escolhia arbitrariamente entre intenções determinísticas
conflituosas; uma sombra corrigida conflituosa também podia ser sobreposta; citações
incompletas com 100.000 caracteres excediam o orçamento de teste de 5 s.

Correção mínima: regras de clarificação declarativas no JSON/schema existentes;
negações/citações e conflitos ficam UNRESOLVED/ASK_HUMAN; LanguageTool/tiny não
apagam essa recusa nem escolhem uma das ações incompatíveis. A expressão de citação
não atravessa outro marcador de abertura, evitando o custo quadrático observado.
Prefixos explícitos, original UTF-8 e funcionamento sem IA mantidos.

Primeira regressão local Python 3.12/Linux: **213 PASS**, incluindo os 33 novos casos,
100K de ambiguidade, round trips de linguagem, contratos/sintaxe, Store, startup e
morte real em criação/Canonical. **4 PASS** adicionais no HTTP/Host real comprovam
recusa de propostas naturais sem correspondência autorizada, zero runs/ferramentas
e zero Creative/Canonical. Essas contagens não provam 217 inputs distintos nem
Windows/PC; as matrizes internas e repetições não são somáveis.

Host/Store/Kernel/M1–M14, sandbox, Writer, runner, manifesto ativo, instalação e UI
ficaram byte-a-byte iguais ao baseline. O selo ativo continua válido. Front Door
continua **NOT INTEGRATED**: estas mudanças corrigem interpretação testada, sem a
transformar num novo caminho de execução. O HTTP sem process continua a devolver
403, uma recusa segura que comprova o bloqueio de integração.

Gates seguintes: repetir os oito workflows principais e o Front Door Lab, aplicável
à alteração do parser, no HEAD final. Conferir checkout real, regressões,
confinamento, crash/recovery e E2E existentes. Não transferir resultados de outro
SHA. Writer real conserva o FAIL independente; o diagnóstico permanece no
laboratório Codex, sem sobreposição de alterações.

FAIL de auditoria reproduzível: o run Front Door Lab `37827787132`, associado a
`78b52f7675cbab41b28e6739ea6ec819f120dfdc`, marcou SUCCESS mas o log do job
`113484985250` mostrou checkout do merge sintético
`234020318bfb94ec49844a87ac4fe00b7ebd3d58`. Esse resultado não valida o candidato.
Correção mínima no workflow existente: fixar `pull_request.head.sha`/`github.sha`,
como nos outros oito gates, sem mudar comandos, limites ou cobertura. A repetição
dos nove workflows deve verificar o SHA nos logs, além do estado da API.

Bloqueio contratual da Folha: não existe correspondência aprovada entre intenções
e operações, nem integração da confirmação pré-execução exigida pelo seu contrato.
Próximo passo para arquitetura/auditoria: rever uma correspondência mínima para a
operação verify já existente, com anexo explícito e confirmação da operação e dos
bytes apresentados; nenhuma tradução automática das sete intenções para dez
processos. Só depois provar frase natural → Host → Creative → Human Gate → Canonical
e restart. O fallback técnico não satisfaz a aceitação normal definida em #33.
PC físico, serviços/modelos instalados e power-loss continuam NOT RUN.

### Retoma Work — citações sem fecho, 08-10-2026

Retomada a segunda revisão da interpretação conservadora, preparada no checkout
anterior. A retoma preservou os checkouts anteriores e os laboratórios
Codex/Folha, trabalhando numa cópia isolada de a13d316.

FAIL-first preservado em `e9b2489471e5513f70c25641b071f4b598094e5d`: três
citações abertas com «, “ e aspas ASCII tornavam-se comandos positivos. Os mesmos
casos foram testados no parser e contra uma hint tiny: **6 FAIL / 33 PASS** em
0,66 s. A árvore desse commit foi conferida contra a árvore local reproduzida.

Correção mínima: uma expressão declarativa em `frontdoor_rules.json` aceita o
fim do texto como limite da citação. A expressão continua sem atravessar outro
marcador de abertura. Nenhum motor, mapeamento de processo ou autoridade foi criado.
Após a correção: **39 PASS** focais em 0,56 s; **189 PASS** na regressão local em
28,71 s, incluindo os quatro testes HTTP/Host de recusa, prefixos, LanguageTool,
ambiguidade 100K, round trips 20K, contratos/sintaxe, Store, startup e morte real;
**17 PASS** adicionais no contrato tiny loopback em 1,78 s. O gate focal é parte
da regressão e não deve ser somado. O servidor loopback é uma fixture, não um
modelo instalado. Comandos e contagens XML ficam registados no comentário de continuação.

O selo ativo foi verificado. Host/Store/Kernel, runner, sandbox, UI, Writer,
manifesto e instalação continuam idênticos ao baseline. Apenas a regra, os três
casos no teste existente e este ponto operacional mudam. A Front Door continua
**NOT INTEGRATED**; recusa HTTP não prova aceitação natural no produto.

Matriz anterior em a13d316: **7 SUCCESS / 2 FAIL**, em nove workflows. Confinement
Server 2022 teve timeout de 15 s numa invocação PowerShell de recusa de instalação
(19 outros testes desse passo passaram); Server 2025 passou. Writer Windows teve
**2 FAIL / 5 PASS**, por timeout de 45 s em book/convert_pdf dentro de LPAC. Os
logs confirmam o checkout de a13d316. Estes resultados não são transferidos para
o novo HEAD: repetir os nove gates e verificar o SHA nos logs. Não aumentar
prazos/permissões, nem incorporar trabalho dos laboratórios alheios para fabricar
PASS. A matriz final e qualquer bloqueio real ficam nos comentários #32/#33.

### Ciclos e provas por SHA

| Alteração | FAIL preservado e correção mínima | Evidência |
|---|---|---|
| Startup, `5a0559c` | Dois testes interceptavam os.replace embora Windows publique por _replace_durable/MoveFileExW. Passaram a observar e falhar na fronteira durável real; bytes antigos/novos completos e ausência de temporários mantidos. Runtime intacto. | Seis workflows então aplicáveis SUCCESS no mesmo SHA: auditoria, compatibilidade, crash, confinement, Windows, Integration. [Windows 37770378941](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37770378941); [Integration 37770378926](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37770378926). |
| Contratos, `4b89dd0` / `6d96a96` | A/B das dez capacidades, morte real antes/depois da publicação Canonical, consistência e bootstrap funcional. Peer CLI inicial exigia leitura de uma pasta Windows protegida; substituído por PE C nativo, sem essa concessão. | FAILs e relatórios nos comentários #32. Peers não provam instalações reais de Java/Writer/modelos. |
| Binding, `2c928f7` | Bootstrap: 3 FAIL/5 PASS antes; launcher com Git real: 8 FAIL/8 PASS antes. Autorização explícita, SHA/origin/checkout limpo, binding externo expected_head, BOM PowerShell e renovação explícita. | Launcher 16 PASS após; bootstrap 8 PASS em cada Windows. Mantidos helpers/entrada existentes; bundle completo opcional. |
| Stdio LPAC, `5ae70d2` | A/B expôs PermissionError: nul em Java/Writer. Pipe/EOF vazio substituiu DEVNULL, conservando prazo, erro e kill da árvore. | Mesmos resultados/bytes passam; selo atualizado só para adapters afetados. Nenhuma concessão ao NUL global. |
| A/B, `80976b5` | Redução medida sem presumir um único processo adicional: A/B 4/2 nas rotas Python, 6/4 nos peers CLI. | [Confinement 37777486939](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37777486939): 31 PASS por Windows. [Writer 37777486997](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37777486997): timeout real no Host/LPAC; PASS global recusado. |
| Via direta, `7fe89c3` | Três contratos FAIL-first: importação MCP obrigatória, segunda sandbox no runner e dependências core. Após A/B verde, B passou a ser o runner selado. | Local 94 PASS/20 gates Windows NOT RUN. A/B 10/10; novo Host completo 8/10, dois FAILs PDF; [Confinement 37780160271](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37780160271). |
| Diagnóstico, `a7bc403` | Binding estrutural residual procurava pin MCP no core; corrigido mantendo o critério em requirements-mcp. Diagnóstico limitado dos FAILs Host e probe nativa IPC Writer. | Contratos locais afetados 10 PASS. Novo SHA exige nova prova. XML Writer preservado também em FAIL. |

Contagens de funções, operações e inputs não são somáveis: suites sobrepõem-se e repetições por OS/SHA não acrescentam inputs distintos. Morte de processo não equivale a corte de energia/disco físico.

Correção seguinte dos peers: o diagnóstico em a7bc403 mostrou WinError 5 ao consultar soffice.com. A fixture colocou o executável diretamente numa pasta pytest privada, pelo que a raiz de leitura calculada era o diretório pai de pytest. O peer passa ao layout LibreOffice/program, com a raiz própria esperada pelo adapter. Apenas teste alterado; ACL/token/Host/Store conservados. Repetição nativa PENDENTE neste commit.

Auditoria do SHA efetivamente testado: os logs de checkout mostravam refs/pull/32/merge e um SHA de merge sintético, mesmo com os runs associados ao HEAD candidato. Os oito workflows passam a fixar ref no pull_request.head.sha (ou github.sha fora de PR). A repetição seguinte verifica o próprio commit candidato; os resultados anteriores ficam associados aos seus runs/árvores, sem serem transferidos ao novo SHA.

Atualização de provas em a2d76ff: confinement concluiu nos dois Windows, incluindo 41 PASS por job (A/B + dez capacidades Host/Human Gate/Canonical/restart) e bootstrap 8 PASS. Windows 2022 precisou de repetição por timeout de vswhere antes dos peers; log original conservado, limites intactos. Writer instalado repetiu 2 FAIL/5 PASS. Legacy pipe foi recusado com WinError 5, LOCAL funcionou; a fonte 26.2.6.2 usa legacy. O ponto interno preciso do timeout continua inferência, não rastreio completo.

Regressão Windows: Core 140, Blocks 1079 e Practical 79 PASS; suite completa interrompida pelo limite do job de 15 min após 1525 PASS/12 SKIP. CANCELLED não é PASS. As suites passam a jobs separados com os mesmos comandos/limites, sem retirar testes. Novo HEAD exige repetir os oito workflows antes da matriz final em #32/#33.

Continuação em `d7798a4`: auditoria, CodeQL, crash/recovery, compatibilidade, confinement nos dois Windows e os seis jobs de integração concluíram SUCCESS. Confinement repetiu os 41 testes nativos por OS. Writer repetiu 2 FAIL/5 PASS; limites/fronteira intactos. A regressão standard isolada também foi CANCELLED aos 15 min, após 1530 PASS/12 SKIP (interrupção observada em ssl.py, sem prova de FAIL funcional). [Run e XML preservados](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37785435070).

Correção apenas da distribuição CI: os mesmos 64 módulos standard são enumerados e repartidos por índice par/ímpar em dois jobs Windows. União = 64, interseção = 0; as seis exclusões de volume existentes mantêm os gates dedicados. Não se reduz cobertura nem se aumenta prazo. Log por teste, vinte durações e XML por partição permitem localizar uma eventual demora individual. Novo HEAD deve repetir os oito workflows; o PASS de uma partição não valida a outra nem o Writer.

### Runtime e redundâncias justificadas

A Folha conserva dez processos explícitos da política. **Front Door natural/tiny com sete intenções: NOT INTEGRATED**; não existe mapa 7→10 aprovado nesta convergência. A seleção explícita é o protótipo autorizado; não foi inventado router novo.

Host é o único dono de launch/LPAC/AppContainer SID/Job/deny roots/timeout. O runner faz dispatch fixo para adapters existentes, recusa execução Windows fora dessa fronteira, valida JSON/schema/bytes e devolve `nexus/python-direct`. Não há modelo, rede ou segredo no filho; o broker confiado entrega snapshots delimitados. Fingerprint continua fixado antes da execução e verificado pelo Store. Alterar runner muda o fingerprint; pedidos pendentes antigos exigem reconciliação explícita. Canonical comprometido é verificado sem repetir ferramentas.

Retirados da via interna: relay cliente/servidor MCP, importação obrigatória do SDK e segundo dono de sandbox execute_confined. MCP externo, ferramentas e testes reais de protocolo permanecem; baseline A só em `tests/_mcp_baseline.py`. `requirements.txt` contém jsonschema; `requirements-mcp.txt` fixa MCP/trio; requirements-test inclui ambos. Preparar o core instala dependências de teste para executar gates; MCP não é importação necessária ao runtime.

Mantidos: SHA-256 Windows CNG + Python/hashlib independentes; selo Host e binding externo ao Git; validações independentes runner/Store/UI/policy/schema; bytes originais e proveniência inversa; Creative/Canonical separados; HumanDecision ligada ao hash; atomicidade Windows WRITE_THROUGH e crash/restart/idempotência. PS/.NET é diagnóstico externo, sem substituir CNG. **Host/Store, M1–M14 e lógica do Kernel não foram alterados.**

Ficheiros centrais: adapters/runner.py, languagetool.py, office.py, integrity.json e requirements; windows/bootstrap-nexus-local.ps1, sync-nexus-code.ps1, nexus-launcher.py e binding no instalador completo; testes startup/A-B/consistência/crash/dependências/bootstrap/launcher/Writer e workflows. História de FAILs e candidato A/B preservada no Git/GitHub.

### Entrada humana e limites

Na raiz de checkout oficial, depois de conferir o SHA candidato:

```powershell
$accepted = git rev-parse HEAD
powershell.exe -NoProfile -File nexus/windows/bootstrap-nexus-local.ps1 -RepoRoot (Get-Location).Path -ExpectedHead $accepted -AuthorizePrepare
```

Bootstrap core existente: confere origin, Git limpo e HEAD esperado, reutiliza preparação/inventário/plano e copia launcher para fora do repositório com expected_head. Nexus.lnk usa esse binding; HEAD diferente ou ficheiros alterados recusam arranque. Aceitar atualização exige repetir bootstrap com novo SHA explícito. Não executar preparação como se os FAILs atuais fossem release aprovada.

Instalador completo/bundle cerca de 70 GiB é opcional e dependente da aceitação física; não foi executado. Provisioning protegido, modelos/GPU, contas/serviços/perfis Windows e PC de Pedro: **NOT RUN**. CI usa runners descartáveis e dados sintéticos.

### Bloqueios e continuação

PDF pelos peers no novo Host passou a repetição completa em a2d76ff após corrigir a fixture; LibreOffice 26.2.6 instalado excede 45 s dentro da fronteira existente, embora Writer fora dela passe. Stdout/stderr Writer vazios em 7fe89c3, sem PDF/proposta promovida. IPC Win32 incompatível com AppContainer é hipótese; a observação legacy/LOCAL deve ser confrontada com binário/fontes da mesma versão antes de atribuir causa.

Próximo ciclo: fechar a regressão repartida e toda a matriz no mesmo HEAD, manter Writer a falhar enquanto não existir solução equivalente dentro da fronteira aprovada; repetir auditoria, sintaxe, unitários, integração/stress, segurança, crash/recovery, bootstrap/launcher e E2E no mesmo HEAD. Registar matriz e bloqueios reais em #32 e #33. Nenhum prazo/permissão aumentado para fabricar PASS.

## Atualização documental e capacidades — 06-10-2026

- Constituição e arquitetura ativa reconciliadas com Kernel/Host/Store + MCP;
- Activepieces/Conductor/Spiff preservados como genealogia, não runtime;
- planos/instalação/matriz de compatibilidade atualizados;
- F001–F008 e F011–F013 marcados com interpretação atual sem apagar evidência histórica;
- LibreOffice atual continua limitado a DOCX/ODT → PDF;
- Writer editorial completo passou a ter contrato próprio em `CAPABILITY-WRITER-EDITORIAL.md`, ainda **NOT IMPLEMENTED**;
- arquitetura M1–M14 não foi alterada.

Este é o único documento de estado operacional corrente em `nexus/docs`.
Estados antigos, filas, handoffs e quadros temporários foram removidos da árvore ativa; continuam recuperáveis pelo histórico Git e pelos PRs/comentários.

## Relatório corrente — 06-10-2026

Pedido humano: corrigir e testar sem alterar a estrutura, e escrever o ponto de situação. **Protótipo funcional integrado e validado no CI em e579af5; provisioning não protegido recusado; instalação protegida e aceitação no PC ainda por concluir.** Arquitetura M1–M14, responsabilidades Kernel/Host/Store, Creative/Human Gate/Canonical e caminhos existentes preservados.

Runtime com gates Nexus/Host/MCP/Avatar e recusa de provisioning confirmados: `e579af5f599942efe717142936ba8f611c19b969`. Esta atualização final altera só este relatório; o código testado permanece igual. PR #23 draft, branch lab-open-notebook-avatar-20261004. Baseline/base e main não foram promovidas.

| Bloco | Números observados | Resultado/evidência |
|---|---|---|
| Windows Server 2022 e 2025, fronteira nativa | **10.000 operações filesystem recusadas**, zero ERROR; cofres sintéticos, HKCU, loopback disponível e filho DENIED; trabalho atribuído funciona | **PASS**, [run 37444721963](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37444721963) |
| Autoridade Host/Store | **10.000 inputs**, quatro famílias de 2.500, sem dados alterados nem aprovação forjada | **PASS**, mesmo run |
| Host real | 22 alvos proibidos DENIED + dois controlos positivos | **24 PASS**, mesmo run |
| Retorno e recuperação | 76 funções/contratos | **76 PASS**, mesmo run |
| Hash independente CNG | Sete vetores, incluindo vazio, NUL, Unicode, chunk e 2 MiB | **PASS**, mesmo run |
| Concorrência | 500 substituições atómicas com quatro leitores | **PASS**, mesmo run |
| Listagem de dependências | Pasta listável, ficheiro selecionado legível, outro ficheiro DENIED e DACL original intacta | **PASS**, mesmo run |
| Provisioning | **18 critérios PASS** por OS: nove com sentinelas e nove invocações reais sem sentinelas; flags não contornam a recusa | Mesmo run; recusa, não instalação funcional |
| Regressão Nexus completa | **1.386 PASS**; Core 140, Blocks 1.068 e Practical 40 também PASS | [Windows 37444722019](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37444722019) |
| MCP real e OpenNotebook | **1.000 chamadas MCP reais + inventário 33 tools**; A–G PASS, regressão 1.386 PASS | [Integration 37444721856](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37444721856) |
| Avatar | **Windows 168 PASS, zero SKIP** em 97,73 s; Linux 165 PASS, três critérios só Windows não aplicáveis; timeout 1,86 s < 3 s | [Run 37444721936](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37444721936) |

Não somar estas linhas: funções pytest, inputs e operações são unidades diferentes, e as suites sobrepõem-se. Repetição por OS ou por SHA não aumenta o número de inputs distintos.

Correções implementadas: validação ASCII da sessão; launcher Windows com LPAC/DACL/Job e ausência de fallback; snapshot privado separado do Store; stdio MCP em pipes LOCAL/eventos sem rede; CNG para verificação independente; avatar Windows ligado ao launcher existente para codecs, PIL e worker. O conflito de dependências no CI Avatar foi corrigido instalando apenas o jsonschema consumido pelo selo do Host nesse ambiente; as versões Nexus permanecem fixadas.

O Host limita os processos que lança. Os ensaios não são uma auditoria de todo o Windows nem confinam retroativamente OpenNotebook/ACE/Forge ou outros backends já iniciados fora desse launcher. Modelos/GPU, instalação protegida no PC e limpeza de perfis/ACL em crash: **NOT RUN/PENDENTES**. A inferência aprendida é substituída nos contratos Avatar deste run. Os instaladores Windows, o setup global histórico e o provision de modelos recusam antes de efeitos enquanto a instalação protegida não está implementada. O ambiente já instalado continua testável por check-nexus.ps1.

PC de Pedro, contas, serviços, políticas e ficheiros pessoais não foram alterados. Nenhum PASS de CI é convertido em perfeição universal, instalação física ou release. Etapa atual concluída no repositório: corrigir o âmbito/arranque Avatar, comprovar recusa do provisioning e fechar regressão. Próximo trabalho pendente: provisioning protegido, limpeza após crash do Host e aceitação de modelos/GPU no Windows real. Não executar os instaladores bloqueados como se fossem PASS.

Microcontrato Avatar/Host, 06-10: FFmpeg/ffprobe só necessitam de leitura do diretório do executável e dependências selecionadas; não devem ler o Python/Nexus do Host. Em cc3d1be, [run 37437120425](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37437120425), o FFmpeg real copiou o input atribuído mas também leu Lib/this.py fora do trabalho: **1 FAIL em 37,85 s**; regressão Windows seguinte NOT RUN por esse FAIL. O job anterior de 48a7215 foi CANCELLED no limite de 20 min, sem XML final; não é PASS e a causa desse tempo não está provada. Correção mínima neste commit: codecs recebem apenas diretório do executável e dependências explícitas; só processos Python recebem os caminhos Python/Nexus necessários. Nenhuma alteração de estrutura, capacidade de rede, token, Job ou portão humano. Em b3752b3, [run 37438100330](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37438100330), o mesmo contrato Windows passou: leitura atribuída funciona e a leitura do Host é recusada. Suite completa ainda em curso. Dado o CANCELLED anterior, o CI passa a executar o teste de timeout existente no início e a conservar nomes/durações; não aumenta limites nem enfraquece testes.


Microcontrato de timeout Python, 06-10: em 2f39016, [run 37438868791](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37438868791), o mesmo FFmpeg PASS em 0,15 s, mas o teste existente de timeout terminou em 18,99 s, acima de três segundos: **1 FAIL / 1 PASS**, regressão Windows seguinte NOT RUN. Não aumentar o limite do teste. Correção deste commit: o launcher distingue leitura do diretório sem herança da leitura dos descendentes; Python recebe ficheiros/DLLs e biblioteca padrão, com pacotes externos só quando selecionados. PIL recebe apenas PIL e a sua dependência XML presente; os pacotes do modelo são explícitos no worker. O worker lê os ficheiros Nexus necessários à verificação da fronteira, sem concessão recursiva de todo o Nexus. O import jsonschema passa para validate: inspecionar o token não deve carregar o validador de dados nem exigir os seus pacotes. Selo atualizado para os dois ficheiros core alterados. Um controlo nativo exige listar uma pasta, ler um ficheiro selecionado e recusar outro ficheiro na mesma pasta. Sem alteração de estrutura, rede, token, Job, limites ou decisão humana. Repetição dos quatro critérios Avatar iniciais, regressão integral e gates Nexus: **PENDENTES**.

Repetição em 722814e, [Avatar 37440409335](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37440409335): **1 FAIL / 3 PASS**. Timeout 45,54 s; pipeline de vídeo/retorno/idempotência PASS, worker direto recusado e worker confinado --help PASS, leitura FFmpeg não atribuída recusada. A restrição funcional passou mas a tentativa não resolveu a demora; não ocultar o agravamento. [Confinamento 37440409636](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37440409636): ambos Windows PASS, incluindo novo contrato de listagem sem leitura, 10.000 operações recusadas, 10.000 inputs, Host 24 e retorno 76. Correção seguinte usa SetSecurityInfo por handle MAXIMUM_ALLOWED só para diretórios sem herança, também na revogação. É o comportamento documentado que evita propagação aos filhos, sem proteger/desproteger DACL humana nem dar o handle ao filho. Concessões recursivas mantêm SetNamedSecurityInfo. O controlo acrescenta DACL do ficheiro não atribuído intacta. Fonte primária e alternativa escolhida: [Microsoft SetSecurityInfo](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-setsecurityinfo); SetFileSecurity obsoleto e SetKernelObjectSecurity para objetos de filesystem foram descartados. Selo nativo atualizado; timeout de três segundos e regressão mantidos, repetição PENDENTE.

Repetição em 7726709, [Avatar 37441690692](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37441690692): **Windows 168 PASS, zero SKIP, 63,93 s**; quatro critérios iniciais PASS em 5,32 s. Timeout **1,74 s < 3 s**, pipeline/retorno/idempotência 2,25 s e worker nativo 0,74 s. Linux 165 PASS, três critérios exclusivamente Windows não aplicáveis. [Confinamento 37441690714](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37441690714), [Nexus Windows 37441690741](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37441690741) e [Integration 37441690748](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37441690748): SUCCESS. A distinção de ACL ficou testada e a demora anterior foi resolvida sem aumentar permissões, timeout ou limite de CI.

Próximo microcontrato, dono Host, 06-10: provisioning não validado deve recusar antes de diretórios, processos, instalação, downloads ou conta global, incluindo flags de salto. Entradas revistas: os três instaladores Windows, o descarregador de modelos (CLI/função) e setup-isolation.ps1 histórico, que ainda podia criar conta/pastas globais com elevação. Este commit acrescenta primeiro nove critérios com os entrypoints reais e sentinelas de side effects; fonte ainda sem alteração. As sentinelas impedem a alteração global no ensaio, e não constituem prova de confinamento. Baseline esperada FAIL, resultado PENDENTE. Após recusa incondicional, repetir com e sem sentinelas: só isso prova recusa real, não instalação funcional. Estrutura preservada e implementação histórica retida; nenhum script físico executado no PC de Pedro.

Regressão do runtime 7726709 em 6ba7ea7 (só testes/documentação), [Avatar 37442921072](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37442921072): primeira chamada timeout **3,64 s > 3 s**, vídeo/retorno/idempotência PASS em 1,85 s, worker nativo PASS e FFmpeg restrito PASS; **1 FAIL / 3 PASS**. O primeiro PASS de 1,74 s não é prova de estabilidade do arranque. Os imports Nexus e a ligação de protótipos DLL passam para a inicialização do serviço, sem criar tarefa, perfil, processo ou ACL. O selo continua verificado em cada chamada e não há fallback. O mesmo limite de três segundos e a suite integral mantêm-se; repetição PENDENTE.

Baseline provisioning, [Confinamento 37442920985](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37442920985): **9 FAIL** em Server 2025, sentinelas observadas em New-Item, Get-Command, Resolve-Path, Read-Host e mkdir do descarregador. Original e pasta não criada invariáveis. Outros gates Native/Host/retorno PASS. Falha esperada do contrato, não nove ataques bem sucedidos no PC. A mesma recusa deve ser comprovada depois sem sentinelas.

Contenção do provisioning, 06-10: os três instaladores e o setup histórico recusam imediatamente, antes de resolver caminhos, perguntar credenciais, criar pastas, instalar ou lançar programas. O descarregador recusa no início de provision em Windows, cobrindo CLI e função, antes de gdown, mkdir ou HTTP. Flags de salto não contornam o bloqueio; nenhuma criação de conta global nem política adicional. Fonte histórica preservada sem execução e caminhos inalterados. Repetição com as nove sentinelas originais e nove invocações reais sem sentinelas = **18 critérios PENDENTES**. Isto implementa recusa segura; **não implementa nem aprova instalação protegida funcional**. check-nexus.ps1 continua disponível para um ambiente já instalado. Correção do arranque Avatar em validação simultânea, com o teste <3 s mantido.

Fecho desta etapa, 06-10, e579af5: [Confinamento 37444721963](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37444721963) SUCCESS nos dois Windows: 10.000 operações DENIED/zero ERROR, 10.000 inputs PASS, 24 Host PASS, 76 retorno PASS, sete vetores CNG PASS, ACL do ficheiro não atribuído intacta e **18 recusas PASS** (6,36 s em 2025; 7,56 s em 2022). [Windows 37444722019](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37444722019): Core 140, Blocks 1.068, All **1.386** em 229,15 s, Practical 40 e wrapper PASS; erro de prerequisites é controlo negativo deliberado. [Integration 37444721856](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37444721856): A–G PASS, MCP real 1.000/inventário 33, regressão **1.386** em 234,98 s. [Avatar 37444721936](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37444721936): Windows **168 PASS**, Linux 165 PASS com três critérios Windows não aplicáveis; primeira chamada timeout **1,86 s < 3 s**. O mesmo ajuste de arranque passou antes em 2c53611, timeout 2,40 s e Windows 168 PASS. Auditoria SUCCESS. Não somar repetições, OS, inputs, operações e funções. Nenhum modelo aprendido/GPU real é coberto pela substituição do modelo usada nestes contratos.

Resultado: há um núcleo funcional e uma extensão Avatar tecnicamente validada como protótipo. Falhas de leitura ampla e propagação de ACL foram corrigidas; a inicialização deixa de pesar na primeira chamada temporizada, sem autoexecutar ferramenta. O provisioning não validado está contido por recusa real, inclusive chamada direta do descarregador e setup que criava conta global. Uma recusa segura não equivale a instalação funcional. Estrutura e M1–M14 preservados; Human Gate continua obrigatório; nenhuma alteração no PC de Pedro, merge ou release. Este commit de fecho modifica somente o relatório, e conserva toda a sequência FAIL/correção/PASS abaixo e acima.

## Fonte de verdade operacional

- PR ativa: **#23 — CURRENT BASELINE**.
- Branch de continuação: `lab-open-notebook-avatar-20261004`.
- Kernel/Host/Store são a autoridade do sistema.
- MCP é transporte determinístico.
- OpenNotebook, LanguageTool, LibreOffice, ACE-Step, Forge e restantes integrações são ferramentas externas.
- Creative precede Canonical.
- Promoção para Canonical exige decisão humana explícita.
- Tiny/IA não recebe autoridade de sistema.
- Duplicação exata é a única base para eliminação automática; semântica/similaridade apenas sinaliza revisão.

## Correção e 10.000 ataques — implementação em validação, 05-10-2026

Pedido humano: resolver e testar 10.000 casos. Contrato do microprocesso, dono Host (sem alterar M1–M14): lançar somente um comando selecionado pelo Host, com inputs delimitados, identidade Windows de tarefa, direitos de leitura dos executáveis e escrita no trabalho, sem direitos sobre Kernel/cofres/dados externos nem capacidades de rede. Criar suspenso; verificar token AppContainer, SID e associação ao Job antes de retomar. O Job termina descendentes e impõe limites. Erros nativos não autorizam fallback. ACLs da identidade de tarefa são revogadas na limpeza sem restaurar/destruir ACLs humanas completas.

USE/ADAPT: mecanismos oficiais AppContainer/SECURITY_CAPABILITIES, DACL e Job Object, chamados por ctypes; sem serviço/conta/administração global novos. A fronteira nativa começa isolada e a ligação ao Host/MCP é feita apenas no candidato draft; não promover uma baseline sem os gates completos. Avatar/instaladores externos são um âmbito separado que também precisa de portão nativo. O teste executa 10.000 operações reais de ficheiros, leitura dos dois cofres sintéticos, descendente, controlo de escrita permitida e tentativa de ligação a um socket loopback realmente disponível. ERROR/timeout/não execução não contam como DENIED. Fontes: [Microsoft AppContainer](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer), [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).

Estado desta etapa: **HOST/MCP/CNG NATIVOS PASS NO CI / AVATAR EM REPETIÇÃO / INSTALAÇÃO PENDENTE / SEM RELEASE**. O gate Host e os sete vetores CNG passam nos dois Windows; os FAILs históricos abaixo são conservados. A aceitação exige comprovar fronteira nativa, gate do Host real, retorno/reinício e regressão no mesmo código. PC de Pedro não foi alterado.

Primeiro ensaio nativo, commit efc5b0e, [run 37364869364](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37364869364): 1 FAIL / 1 PASS. O SID derivado sem perfil não permitiu CreateProcessW (erro 2); os 10.000 ataques não executaram. Corrigida a preparação para perfil efémero por tarefa, com acesso da ferramenta ao armazenamento desse perfil explicitamente negado e limpeza no fim. A pasta de trabalho continua a ser o único destino de filesystem atribuído. Isto não cria uma conta Windows nem dá direitos globais à ferramenta. Repetição obrigatória, ainda sem PASS.

Correção de autoridade: Host.authorize agora exige str ASCII antes de hmac.compare_digest; sessões Unicode falsas passam a Blocked. O método real extraído por AST passou controlo válido + 10.000 sessões inválidas localmente; é prova de componente, não importação completa do Host. Novo test_authority_10000.py testa o Host/Store completo em quatro famílias de 2.500 inputs (sessões, tickets humanos forjados, autoridade em resultados e processos não registados), com snapshots de dados invariantes. Manifesto atualizado para a alteração revista. CI pendente. Os 40.000 inputs antigos preparados noutra cópia continuam NOT RUN; não são estes testes.

O gate Windows passa a testar Windows Server 2022 e 2025 separadamente, sem fail-fast, conservando artefactos por plataforma e os critérios do gate Host. O job 2025 do commit f5596d4 ainda estava em fila sem runner na última consulta; fila não é PASS nem FAIL do código.

Commit 7aed704, [run 37367782434](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37367782434): **10.000 inputs de autoridade PASS em cada Windows** (4 funções pytest; 2.500 casos por função), 1,03 s em Server 2022 e 0,85 s em Server 2025. A fronteira nativa continuou 1 FAIL / 1 PASS por OS: CreateProcessW erro 203 (variável de ambiente não encontrada), antes dos ataques. Nova preparação acrescenta USERPROFILE/APPDATA/LOCALAPPDATA/HOME com valores da área de tarefa, sem herdar o perfil humano. A hipótese de ambiente só passa a causa resolvida após repetição. Gate Host ainda 22 acessos proibidos permitidos; integração continua pendente.

Commit c91ba66, [run 37368326605](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37368326605): o ambiente corrigiu o lançamento; as 10.000 operações realmente executaram. Resultado do teste ainda FAIL: 6.000 recusas Win32 e 4.000 PermissionError sem winerror, classificadas como ERROR; escrita permitida funcionou, rede deu timeout. Nova verificação aceita apenas ACCESS_DENIED Win32 ou errno EACCES/EPERM sem winerror, conserva canários e exige diagnóstico nativo de capacidade de rede em falta, com socket disponível antes/depois. Timeout isolado continua ERROR. Acrescentado alvo sintético com ALL APPLICATION PACKAGES e LPAC opt-out para que esse direito partilhado não alargue a tarefa. A criação exige sucesso do atributo oficial LPAC; token AppContainer/SID/Job são verificados antes de retomar e o efeito LPAC é testado contra o alvo ALL APPLICATION PACKAGES. Resultado pendente neste novo SHA.

Commit adb64f2, [run 37370018066](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37370018066), Server 2022: FAIL antes de retomar. GetTokenInformation classe 46 deu ERROR_INVALID_PARAMETER (87). O header contém a classe, mas isso não prova suporte Win32; removida essa consulta como pré-condição. Mantidos atributo de criação LPAC obrigatório, verificação AppContainer/SID/Job e teste comportamental do direito AAP. Nenhum ataque desse job conta como executado. Repetição pendente.

Integração preparada no candidato: Host lança runner via fronteira nativa; trabalho é snapshot numa pasta efémera separada de Store, com Store explicitamente negado à identidade da tarefa. Só Host regista estado, stdout e artefacto PDF delimitado/hash verificado após terminar o Job. Runner direto também confina. MCP direto usa stdio nativo; o filho de runner herda identidade/Job sem autorização por variável de ambiente. MCP só aceita input.bin da pasta atribuída. Java/LibreOffice diretos recusam execução fora da fronteira; descendentes mantêm os limites.

OpenNotebook: a chamada HTTP fixa e delimitada é feita pelo Host antes da validação isolada; só output/model_id/transformation_id são copiados, sem palavra-passe, sessão ou capacidade de rede. Health ACE/Forge usa o mesmo princípio para GETs fixos sem mutação. Recuperação conserva EXECUTING antes da chamada e usa resultado durável sem repetir ferramentas nem criar aprovação humana. Leitores state/list_runs passam a usar o lock dos escritores, para eliminar a corrida Windows read/os.replace; novo stress faz 500 substituições com quatro leitores (4.000 snapshots + listas), sem promover. A causa de todo PermissionError histórico não é presumida resolvida sem repetir.

O gate de 22 alvos foi adaptado apenas ao novo ponto de lançamento/pasta de trabalho: injeta o mesmo worker hostil, mantém APIs/DACL/token/Job reais, lê as observações do stdout durável e conserva os 24 critérios. Não é substituído por mocks de proteção. Duplos unitários de output/timeout e sentinelas de não reexecução apontam ao novo launcher, separados do gate nativo. Manifesto/fingerprint inclui windows_sandbox.py.

NOT RUN/PENDENTE: resultados do CI deste conjunto, perfil de crash/limpeza, instaladores/launchers externos e confinamento avatar/modelo/GPU físicos. Nenhum desses limites é substituído pelos 10.000 testes de autoridade.

Commit f01ca4a, [run 37370540374](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37370540374), Server 2022: criação/token/Job passou, mas Python terminou com 0xC0000022 (ACCESS_DENIED) sem output, antes do payload. Nenhuma operação desse ensaio conta como PASS. Implementação testa registryRead (capacidade oficial só de leitura), usada pelo arranque LPAC; não dá rede/escrita/COM. A hipótese de conceder SID RO a System32 foi retirada: o launcher deve usar as permissões de leitura de sistema já fornecidas pelo Windows, sem alterar DACLs de Windows/System32 e sem exigir direitos administrativos para isso. A verificação de token exige exatamente registryRead e recusa capacidades adicionais. Acrescentado canário de escrita no registo HKCU sintético, com original invariável. A hipótese de arranque só é resolvida depois da repetição.

Commit 59782b4, [run 37371780308](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37371780308), Server 2025: 10.000 autoridade + stress de snapshots PASS (5 funções, 8,00 s); regressão de retorno 71 PASS / 5 FAIL (arranque LPAC ainda não funcional). MCP direto revelou pasta TEMP em formato Windows 8.3 RUNNER~1 que o guard confundia com redirecionamento. O chamador passa a resolver a pasta efémera criada por si antes de a entregar; não se removem guards de symlink/junction nem se concede uma pasta externa. Gate Host não obtém observações se o payload não executa; isso continua FAIL/NOT PROVEN.

Commit 21c03d5, [run 37372670714](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37372670714), Server 2022: o Python LPAC arrancou e executou o payload; a hipótese registryRead resolve o arranque observado sem alterar System32. O gate nativo ainda FAIL por NameError no finally do socket (criação já recusada); corrigido cleanup apenas se socket existe. Os 10.000 inputs de autoridade + concorrência continuam PASS; regressão 71 PASS / 5 FAIL, com diagnóstico real ModuleNotFoundError: nexus. O pacote passa a carregar diretamente da pasta Nexus RO, sem conceder leitura/listagem ao diretório pai do repositório. Gate Host e MCP agora conservam diagnóstico limitado de arranque; nenhuma ausência de observações conta como confinamento PASS. Repetição pendente no novo SHA.

Commit 3f2f377, [run 37374094031](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37374094031): **10.000 operações reais recusadas PASS em Server 2022 e 2025**, incluindo alvo AAP; leitura Creative/Canonical, escrita HKCU sintética, socket loopback e descendente DENIED; escrita atribuída PASS. 2 funções nativas, 5,26 s em 2022. 10.000 inputs de autoridade + concorrência também PASS. Gate Host FAIL antes das observações: normalização Windows não podia ler a pasta TemporaryDirectory privada ancestral; preparação concede RO apenas a essa árvore efémera. MCP/retorno ainda FAIL: import _overlapped cria socket no próprio arranque, recusado com WSAEACCES. Nova adaptação usa AnyIO/Trio 0.34.0 e pipes LOCAL; os tipos asyncio importam, mas os seus loops são explicitamente recusados. O último probe Winsock de Trio só pode ser ignorado no código/linha observados após IOCP pronto; nenhuma capacidade de rede é acrescentada. CI desta adaptação PENDENTE; não declarar MCP funcional até PASS.

Commit f23f180, [run 37375601558](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37375601558): MCP importa e chega a Trio, mas FAIL no socketpair da fila de reentrada. Substituído esse mecanismo de notificação por evento Win32 anónimo local à tarefa, com espera cooperativa de 10 ms; sem sockets, sem capacidade nova e sem alterar o Host fora da fronteira. Gate Host continuou FAIL na normalização estrita do próprio probe; o guard agora compara cwd real com caminho canónico já verificado pelo Host e conserva o marcador de área descartável e todos os 22 alvos/critério DENIED. Não concede leitura a ancestrais humanos. Diagnóstico limitado do runner conserva a causa para a repetição. Os 10.000 ensaios nativos/autoridade continuam PASS nesse SHA; MCP/retorno aguardam novo resultado.

Commit 8f97e0f, [run 37376277120](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37376277120): **gate Host 24 PASS nos dois Windows** (22 alvos DENIED + controlos positivos); autoridade 26 PASS; 10.000 nativos e 10.000 autoridade PASS; retorno 73 PASS / 3 FAIL, limitado à verificação Windows via PowerShell dentro de LPAC. [Integration 37376277512](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37376277512): 100K Kernel PASS, 100K linguagem PASS, MCP real 1.000 + pacote OpenNotebook (33 tools) PASS (6 funções, 65,22 s), OpenNotebook/Kernel E2E 5 PASS, contrato/parse instalador PASS; health MCP 15 PASS / 2 FAIL por carregar duas vezes a configuração já ativa. Corrigida identidade do módulo bootstrap. A verificação confinada passa a usar Windows CNG/BCrypt SHA256, independente de hashlib, com provider explícito e limite 2 MiB, sem arrancar PowerShell/.NET dentro do LPAC nem conceder novas capacidades. Evidência identifica windows.cng-sha256; o backend .NET histórico permanece distinguido. Sete vetores reais nativos (incluindo vazio, NUL, Unicode e limites de chunk/input) e regressão ainda PENDENTES. Não é PASS do novo backend até repetir.

Commit 990d8cc, [confinamento 37377232938](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37377232938): 10.000 operações nativas PASS, 10.000 inputs de autoridade + concorrência PASS, gate Host 24 PASS e retorno/reinício 76 PASS em ambos os Windows. O job global ainda FAIL por um erro do novo teste: o vetor de bytes NUL recebeu o nome de ficheiro reservado Windows `nul`, em vez de um ficheiro normal. Corrigido para `nul-bytes`, preservando os bytes e as sete comparações CNG/hashlib; repetição pendente. [Integration 37377232769](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37377232769): todos os blocos A–G PASS, incluindo 100K Kernel, 100K linguagem, 1.000 chamadas MCP reais + inventário OpenNotebook, E2E, health 17 e regressão completa 1.386 PASS. [Windows 37377232851](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37377232851): Core 140, Blocks 1.068, All 1.386 e Practical 40 PASS. Contagens sobrepostas; não somar como testes distintos. Isto valida o código no CI, não a instalação/modelos/GPU no PC de Pedro.

Repetição do commit a59e447: os passos nativos/autoridade/gate Host passaram nos dois Windows; resultado global/retorno ainda em curso na publicação da etapa seguinte. Avatar Windows passa a usar o launcher nativo para FFmpeg/ffprobe, descodificação PIL e worker, com cópias de inputs, trabalho privado e dependências RO explícitas. O worker direto exige token/Job reais antes de importar o modelo; Python de inferência usa -I. Sem import Nexus/manifesto válido não há fallback sem proteção. Dois novos ensaios reais Windows verificam recusa de escrita exterior e recusa de worker direto, com controlos positivos. FFmpeg real, contratos e integração router em repetição. Modelo/GPU/PC físicos continuam NOT RUN; os ensaios substituem apenas o modelo aprendido, não o launcher Windows.

Continuação de 06-10-2026, pedido humano: corrigir e testar sem mudar a estrutura. Arquitetura M1–M14, Kernel/Host/Store e diretórios existentes preservados. Commit 7a61290: [confinamento 37378593177](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37378593177) SUCCESS em Server 2022/2025 (10.000 operações nativas, sete vetores CNG, 10.000 autoridade + concorrência, Host 24 e retorno 76). [Windows 37378593246](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37378593246) e [Integration 37378593142](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37378593142) SUCCESS. [Avatar 37378593194](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37378593194) FAIL antes de executar os testes: adicionar requirements Nexus ao ambiente upstream provocou conflito mcp==1.23.2 com fastmcp>=3, dependência transitiva de content-core. Correção mínima: instalar no ambiente Avatar apenas jsonschema==4.26.0, consumido pela verificação de integridade do Host; o launcher Windows é stdlib. Dependências/MCP do Nexus permanecem fixadas no ambiente próprio. Não usar --no-deps nem mudar o upstream para esconder conflito. Avatar real Windows/Linux em repetição; nenhum PASS do modelo/GPU físico é inferido.

## Revisão do código e segurança Windows — 05-10-2026

SHA executável revisto: `dcef003f7c3e93ed8bdfe1730ce5870f1b818e09`. A presente revisão documental não altera esse runtime. Pedido de Pedro: conferir o código real e aproveitar as proteções nativas do Windows nos bastidores, mantendo a Folha simples; não redefinir a arquitetura já fechada.

| Gate observado nesse SHA | Evidência |
|---|---|
| Nexus Windows | [SUCCESS](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37304293988): Core 140, Blocks 1068, All 1386, Practical 40 PASS |
| Integration Stress | [SUCCESS](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37304293836): blocos 100K, MCP, E2E controlado e regressão 1386 PASS |
| Avatar | [SUCCESS](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37304294007): 165 PASS em Windows e 165 em Ubuntu |
| Auditoria | [SUCCESS](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37304293869): 34 históricos e 11 de persistência PASS |
| Confinamento Windows | **[FAIL](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37304294214): 22 acessos proibidos ALLOWED; 2 controlos PASS**. Contratos de autoridade da aplicação: 26 PASS |

As contagens sobrepõem-se e não devem ser somadas. O novo Practical verde não identifica a causa do PermissionError anterior; a falha histórica continua conservada abaixo. O E2E controlado e os ensaios de avatar não substituem backend/modelo/GPU físicos completos. O gate de confinamento correu em runner Windows Server 2025, com alvos sintéticos; não é prova no PC de Pedro.

### O que o código realmente faz

- `host.py::_run` chama `subprocess.Popen` com cwd/env reduzidos e CREATE_NO_WINDOW. Não escolhe conta Nexus/token restrito, não aplica ACL e não associa Job Object. A tool mantém a identidade corrente. O gate hostil confirmou a consequência em 20 operações de escrita e 2 leituras proibidas de ensaio.
- `mcp_client.py::_open_session` usa `stdio_client` com command/args/env. A allowlist limita nomes de tools; não restringe os direitos Windows do servidor. O percurso efetivo é Host → runner → MCP → adaptador → subprocesso ou API externa.
- `adapters/office.py` e `adapters/languagetool.py` lançam os executáveis sem seleção de identidade restrita. Perfil LibreOffice por tarefa, validação de pacotes, heap Java e timeout são controlos reais, mas não isolamento de ficheiros.
- `lab/open_notebook_avatar/notebook_avatar/service.py::command` cria processos e grupos, com limites e captura de output. Não aplica a fronteira Windows do Host. O comentário do código atribui a sandbox de SO à camada externa; essa ligação ainda falta.
- `windows/sync-nexus-pc.ps1` arranca ACE-Step/Forge com Start-Process; `install-media-tools.ps1` pode usar winget e uv python install sem fixar todas as localizações/caches a ToolsRoot. Não há prova de instalação confinada; não foi executado nenhum instalador nesta revisão.
- `instance.py` e `app.py` já usam proteções Windows reais: bloqueio do diretório por msvcrt e exclusividade da porta por SO_EXCLUSIVEADDRUSE. Os gates de arranque passam; estas proteções têm âmbito diferente do isolamento de ferramentas.
- `Host.authorize` passa uma sessão Unicode diretamente a hmac.compare_digest. Ensaio do método real extraído por AST: sessão válida ACCEPTED; falsa ASCII Blocked; falsa Unicode TypeError; tipo errado Blocked. Prova de componente, sem importação/execução completa do Host. Correção local preparada não equivale a correção publicada.

### Contrato preservado e diferença de implementação

O comportamento exigido já está em [F008](F008-ISOLAMENTO-WINDOWS.md) e [Windows como hospedeiro](SCHEMAS-E-WINDOWS.md). A pessoa usa linguagem normal; Kernel/Host/Store aplicam autorização e regras; o Host lança uma tarefa delimitada; o Windows faz cumprir os direitos do processo; o Host verifica o retorno e escreve no destino permitido. A gestão de contas, ACLs, tokens e processos não pertence ao percurso normal da Folha. A pessoa continua a ver decisões humanas materiais quando exigidas.

A evidência [WINDOWS-TWO-FOLDERS](WINDOWS-TWO-FOLDERS-EVIDENCE.json), de 01-10, regista identidade Nexus, escrita permitida e leitura/escrita protegida recusadas. É válida para as duas pastas artificiais. O código atual não integra esse lançamento com credenciais no Host. Não inferir que o PC ou todas as ferramentas continuam protegidos a partir desse ensaio antigo.

**Estado: requisito definido; integração de segurança nativa incompleta; execução confinada FAIL.** Próximo microprocesso: ligar a execução real a uma fronteira Windows verificada, delimitar trabalho versus estado do Host, cobrir descendentes, acesso entre tarefas, rede e bancada/modelo; repetir o gate hostil e regressão sem enfraquecer critérios. Não é necessário redesenhar M1–M14 para reconhecer esta lacuna.

### Trabalho ainda não entregue

- Contenção de emergência e correção de sessão Unicode: preparadas numa cópia local separada, **não publicadas nem validadas no CI**. O HEAD publicado continua a executar como antes. Bloquear execução seria contenção, não PASS de sandbox funcional.
- 40.000 inputs adversariais adicionais: ficheiro local preparado, **NOT RUN**. Não os contar como testes passados nem como 40.000 provas independentes do Windows.
- PC, contas, permissões, serviços e ficheiros pessoais não foram alterados por esta revisão.
- Verificação local da cópia publicada: 29 hashes do manifesto conformes; sintaxe dos 74 ficheiros Python Nexus válida. Estes dois controlos não executam o software nem demonstram segurança de SO.

## Revisão observada em 05-10-2026, 10:09 Lisboa

SHA analisado: `7faead619e14d15e5590f84e1d52ac68d1e58bc4`. A revisão documental posterior não constitui correção do runtime nem transfere PASS para o novo commit.

| Gate | Resultado nesse SHA |
|---|---|
| [Auditoria](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37274701729) | SUCCESS |
| [Integration Stress](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37274701734) | SUCCESS; regressão 1386 PASS |
| [Avatar Windows/Ubuntu](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37274701774) | 165 PASS em cada OS |
| [Nexus Windows](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37274701714) | **FAIL**: Core 140 PASS, Blocks 1068 PASS, All 1386 PASS, Practical **39 PASS / 1 FAIL** |

Falha: `test_real_windows_result_back_to_original_and_folha_after_restart[binary-attachment]`, em `test_reverse_flow.py`. A leitura de `runs/<id>/state.json` em `store.state()` devolveu `PermissionError`; o pedido HTTP terminou em `RemoteDisconnected`. `INTEGRITY=PASS`. Não é o controlo negativo de Python inexistente. Possível acesso concorrente/bloqueio de ficheiro é hipótese, não causa demonstrada.

Próximo gate: diagnosticar/reproduzir esta falha, corrigir minimamente quando a causa estiver identificada e repetir Practical, regressão e E2E. Um rerun verde isolado não prova resolução da causa. **Este SHA não tem PASS global.** As suites sobrepõem-se; não somar contagens.

## Última baseline funcional validada antes da limpeza documental

A baseline funcional `7e1ec9b6ce1804123c1cb4bd198ea2dfff5bd98a` passou duas execuções independentes dos gates principais:

- Kernel stress: 100.000 casos PASS;
- linguagem/ambiguidade: 100.000 casos PASS;
- MCP stdio: 1.000 operações PASS;
- OpenNotebook Kernel E2E: PASS;
- ACE-Step/Forge MCP health: 17 PASS;
- regressão completa: 1386 PASS;
- Core Windows: 140 PASS;
- Blocks: 1068 PASS;
- Practical: 40 PASS;
- avatar OpenNotebook: 165 PASS Windows + 165 PASS Ubuntu;
- auditoria histórica: 34 PASS;
- persistência ativa: 11 PASS.

A limpeza posterior é documental/organizacional. O HEAD resultante só passa a nova baseline depois de repetir os mesmos workflows e regressões.

## PC físico

O repositório já contém `nexus/windows/sync-nexus-pc.ps1` para atualizar uma única árvore Git local, validar o Nexus, instalar ACE-Step/Forge externamente e executar health checks.

O gate físico só fica fechado quando existirem, no PC:

- `C:\Nexus-Tools\pc-bootstrap.json`;
- `C:\Nexus-Tools\media-health.json`.

Sem esses relatórios, CI/GitHub PASS não é apresentado como PASS do hardware local.

## Pendências técnicas ainda reais

1. Fechar o confinamento Windows real acima antes de recomendar instalação/execução no PC; diagnosticar também o PermissionError histórico, mesmo com o Practical atual verde.
2. Fechar o E2E físico OpenNotebook 1.15 + SurrealDB + modelo local + Kernel + Creative + Human Gate + Canonical.
3. Escolher e validar um checkpoint Forge com licença conhecida antes de geração real.
4. Continuar os contratos ainda abertos em #3 (IMP-001) e #4 (G10/IMP-019 + eliminação controlada).
5. Integrar outras ferramentas externas apenas pelo mesmo processo: contrato → FAIL real → correção mínima → regressão → teste prático → E2E.

## Percurso do desenvolvimento

A [genealogia de decisões](../../DECISIONS.md) explica por fase o problema, a alteração, a razão e a evidência: receção/persistência, ferramentas existentes, Folha/bancada, testes Windows, simplificação Python/MCP e multimédia. Datas e resultados históricos não são apresentados como validação do HEAD atual.

## Documentação que permanece por função

### Contratos e fundamentos
- `F001.md` … `F013-PROVENIENCIA-INVERSA.md`
- `FUNDACAO-REVISTA-2026-10-01.md`
- `SCHEMAS-E-WINDOWS.md`
- `CONTRATO-RELATORIOS-MICROPROCESSO.md`
- `REGRA-PYTHON-MINIMO-FRONTDOOR-2026-10-04.md`

### Relatórios/evidência
- `RELATORIO-STRESS-100K-2026-10-04.md`
- `RELATORIO-APRENDIZAGEM-RECOVERY-2026-10-04.md`
- `RELATORIO-LAB-TESTES-POR-FASES-2026-10-04.md`
- `RELATORIO-AVATAR-2026-10-04.md`
- `AVATAR-CI-2026-10-04.json`
- `AVATAR-SYNC-CI-2026-10-04.json`
- `RELATORIO-FINAL-WIKI-100K.md`

### Comparações históricas preservadas
- `RELATORIO-KERNEL-SPIFF-CONDUCTOR-FASE1-2026-10-04.md`
- `RELATORIO-PERFORMANCE-CONDUCTOR-2026-10-04.md`

Estes dois últimos são evidência histórica e não descrevem o runtime ativo.

## Regra de continuidade

Uma alteração só passa a baseline se:
1. o bloco afetado passar;
2. qualquer FAIL for preservado e diagnosticado;
3. a correção mínima passar;
4. regressão completa passar;
5. testes práticos aplicáveis passarem;
6. E2E aplicável passar;
7. a PR #23 for atualizada com o resultado.

Não criar novas cópias de estado/continuidade para cada sessão. Atualizar este documento e a PR #23.

## Organização documental — pedido humano de 05-10-2026

Pedido: resumir, limpar e organizar o repositório. Revisão limitada a README principal, README Nexus, AGENTS, DECISIONS e este documento; sem apagar contratos, relatórios, comparações ou histórico. Corrigidas referências a executor retirado e documento removido; indicação explícita de candidato versus main, princípio versus composição histórica e PASS versus FAIL. PR #23 acompanha a entrega. Não foram alterados runtime, testes, licenças ou regras de autoridade.


### 2026-10-11 — Observação E2E Writer coerente com execução existente

- Ordem humana: resolver Writer antes da unificação/integrações/limpeza e controlo Windows.
- Medição completa do provider117.312 s; runtime tem orçamento existente135 s, mais hashes integrais, cópia e limpeza. O teste antigo abandonava a observação aos90 s, antes do próprio orçamento de execução. FAILs anteriores preservados; não declarar performance90 s cumprida.
- Alterado somente prazo de observação dos testes reais Writer para300 s; verify continua90 s. Não alterados timeouts de produção, LPAC/Job/DACL, hashes, original, aprovação, Canonical ou recovery. Os testes mantêm todas as mesmas asserções.
- Benchmark de enumeração/8workers não adotado: ganho insuficiente para explicar o atraso (1.297->0.375 s; hash10.734->9.672 s), identidade exata confirmada.
- Nova suite real sessão99964 em curso; outputs/writer-observacao-completa-testes.xml quando terminar. Base local já alinhada por fast-forward com main e3833856, preservando alterações. Instalação ativa e GitHub sem publicação destas alterações.


### 2026-10-11 — Writer PASS e combinação com alterações do PC

- Writer/Sandy/hash/cópia: suite37 PASS,0FAIL,442.08 s. Inclui book, convert_pdf e verify->Writer com aprovações separadas e reinício sem repetição. Prazo de observação corrigido300 s; FAILs90 s preservados, sem alegar performance90 s.
- Reconciliação de código:18ficheiros equivalentes,5alterações locais a conservar,11revisões3vias (installer combinou limpo;10conflitos). Preservadas entradas/base/propostas em pasta temporária; instalação ativa intacta.
- Candidato workspace combina revisão inline local com FTS5/preparação GitHub e Writer Sandy. Conteúdo após dois-pontos continua dado; não inicia música/podcast mesmo com essas instruções no corpo. Backend72 PASS; Folha/teclado29 PASS.
- Teclado: primeiro teste legado FAIL preservado. Combinação mantém Ctrl+N/O e único envio Ctrl+Enter; confirmações só avançam com checkbox marcado e botão habilitado. Não expor ferramentas na Folha.
- Regressão Host/Store/entrada/instaladores sessão14785 em curso. Não instalada nem publicada a combinação. Evidência outputs/unificacao-combinacao-etapa.json e relatórios vinculados. Próximo: terminar regressão e aceitação nativa no código combinado antes da ativação preservando dados/configurações.


### 2026-10-11 — Regressão combinada concluída

Host/Store/entrada/instaladores: 191 PASS, zero falhas, 145.08 s. Aceitação nativa Writer sobre a combinação final iniciada (sessão 91008). Primeira tentativa teve erro de preparação: pasta pai de basetemp ausente; log preservado em writer-unificado-final-preparacao.log. Pasta preparada e caminhos explícitos corrigidos. Instalação ativa ainda não atualizada; publicação pendente.


## PC local e laboratorio AI Studio — 10-10-2026

Pedido humano: avaliar o ZIP cerebro-parvo-, substituir a Folha antiga e iniciar com uma folha branca sem botoes, titulos ou menus visiveis. Publicar primeiro o ZIP original no repositorio de estudo separado.

O ZIP original foi enviado integralmente (392 ficheiros) para https://github.com/PAPACREATOR/cerebro-parvo-ai-studio-lab, main, commit efe9b10fb4a138d316596c6ee8cb2dbe892a16f6. O repositorio final continua por escolher; o remoto do projeto existente nao foi alterado.

Integracao local: UI candidata adaptada ao servidor Python real; interpretacao deterministica, proposta e confirmacao vinculada ao pedido. Conservados Store, dados, configurações e execucao Windows atuais. Nao foi adotado o server.js demonstrativo do AI Studio (registos em memoria e operacoes simuladas), nem a mudanca Sandy/Writer. Manifesto de integridade atualizado com os modulos da entrada. A aparencia anterior e conservada exclusivamente no ZIP de recuperacao.

Folha inicial branca e editavel. Ctrl+Enter envia o pedido, Ctrl+O junta um ficheiro, Ctrl+N limpa a folha. Resultados e confirmacoes aparecem depois do pedido. Interpretar uma frase nao significa guardar uma nota nem executar uma ferramenta. Exportacao JSON e historico parcial; o ZIP continua a ser a recuperacao completa.

Evidencia: sintaxe JavaScript e os dois smokes Node PASS. Primeiro ensaio Python: 328 PASS / 1 FAIL com execucao real simultanea a outro teste que partilhava os caminhos do Python; teste real repetido sozinho PASS. O ensaio real independente cobre confirmacao/cancelamento/alteracao/reutilizacao, uma execucao Windows, aprovacao sintetica, reinicio e leitura de copia da memoria. Nao declarar release global a partir destes gates. Relatorios em C:/Nexus/registos/organizacao e testes-reais.

Limites: musica/video/podcast/visual-podcast pela Folha continuam a propor planos; os geradores locais instalados e testados nao ficam ligados automaticamente a frases livres. Testes reais que lancem ferramentas devem correr sequencialmente nesta instalacao; nao foi alterada nesta entrega a gestao concorrente de permissoes entre instancias distintas.


### Remocao do menu manual — 10-10-2026

Pedido humano: retirar as escolhas de ferramentas. Removido o lancador interativo Ferramentas Nexus.cmd; helper de arranque deixa de apresentar escolhas; eliminada da Folha a lista de exemplos por ferramenta. Entrada normal por Abrir Nexus.cmd, folha branca e pedido escrito. Confirmacoes de uma operacao concreta preservadas. Ferramentas, configuracoes, dados e testes nao foram removidos. Originais preservados no mesmo ZIP de recuperacao antes da alteracao. Ligacoes novas por linguagem natural continuam a ser implementadas por percurso, sem declarar todos os geradores integrados.


### Revisao natural sem anexo — 10-10-2026

Entrada Corrige/Corrigir/Reve/Rever este texto: seguida do corpo (ate 6000 caracteres). Revê com acento tambem aceite. O corpo e dado, incluindo perguntas ou instrucoes citadas; nao produz outras operacoes. Misturar corpo e anexo e recusado. API marca fonte inline so apos reconhecimento estrito; a UI mostra o pedido completo na confirmacao, sem nome tecnico, hash ou ficheiro virtual. Confirmacao unica continua ligada ao pedido e ao corpo exato. LanguageTool local executado pelo runner Windows confinado ja existente; sem IA e sem alterar o original. Resultado continua candidato ate decisao humana.

Validacao: 176 testes Python PASS (1 teste nativo deliberadamente separado), teste JS inline PASS, revisao Windows real com um alerta para ezemplo PASS; fonte/pedido/resultados verificados e reinicio sem repeticao nem aprovacao automatica. Relatorio registos/organizacao/revisao-natural-real.json. Helper configuracao/testar-revisao-natural.py usa dados sinteticos isolados. Isto ainda nao liga os geradores multimedia a pedidos inline.


### Arranque automatico dos modelos — 10-10-2026

Entrada Abrir Nexus.cmd inicia o supervisor configuracao/servicos-ia-local.py, incluindo reaberturas. Llama.cpp com os GGUF existentes: nexus-qwen3-1.7b em 127.0.0.1:18081 e nexus-qwen3-embedding-0.6b em 127.0.0.1:18082. CPU por defeito para preservar GPU8GB para geradores. Lock impede duplicacao; portas ocupadas so reutilizadas apos health e alias confirmados. Encerramento so de filhos proprios; sem reinicio automatico apos falha. Estado registos/ia-local-servicos.json, logs por modelo; monitor tolera 2 falhas transitorias. 11 testes de supervisor com mocks PASS. Teste real de arranque ainda depende do relatorio registos/arranque-modelos-teste.json.

Testar Nexus.bat --arranque --automatico testa apenas arranque, modelos carregados, bind local e duplicacao; nao executa pesquisa, podcast, musica nem inferencia. Configuracoes de providers OpenNotebook/Money ainda serao ligadas na fase seguinte; modelos prontos por si so nao provam essas integracoes. TTS Piper por API preparado apenas na copia de trabalho, nao instalado nesta fase.


Validacao final do arranque: PASS. Primeira tentativa identificou --embd-normalize como argumento nao suportado pelo llama-server instalado. Removida essa opcao do supervisor e de cinco invocacoes futuras em instalar-ferramentas.ps1, install-nexus-complete.ps1 e test-post-install.ps1. --embedding, --pooling last e --no-cont-batching confirmados pelo --help local e pelo arranque real. 11 testes do supervisor voltaram a passar. Teste frio em 10-10-2026 21:19:39: ambos os ports inicialmente fechados, entrada normal Nexus iniciou ambos e health/catalogo confirmaram carregamento; reabertura sem PID duplicado e bind 127.0.0.1 PASS. BAT --arranque --automatico exit0 e PASS em 21:21:12. Nenhuma inferencia, pesquisa, podcast ou musica executada nesta fase. Historico Nexus17registos preservado. Estado READY em registos/ia-local-servicos.json; relatorio de teste registos/arranque-modelos-teste.json. CPU0camadasGPU e escolha operacional para partilhar o PC, nao falha de deteccaoCUDA. Integracao efectiva dos providers nas ferramentas ainda e fase seguinte.


### Providers locais Open Notebook — 11-10-2026
Pedido humano: continuar instalacao e configuracao das ferramentas Nexus no PC. Confirmado acesso Windows e instalacao real C:/Nexus; C:/Nexus-Tools ausente. Iniciados supervisores existentes de modelos e Open Notebook. MoneyPrinter config.toml ja aponta para openai em http://127.0.0.1:18081/v1 e nexus-qwen3-1.7b (leitura; geracao MoneyPrinter nao repetida).
Open Notebook: preservado nexus-tiny e todos os providers anteriores. Adicionados via API nativa providers locais distintos de linguagem e embedding, com modelos nexus-qwen3-1.7b e nexus-qwen3-embedding-0.6b. Teste nativo de inferencia PASS; embedding real 1024 dimensoes PASS. Defaults chat/transformation/embedding ligados aos modelos testados; TTS/STT e outros defaults preservados. Configuracao anterior models/defaults guardada em backups/providers-20261011-095729.json. Evidencia: C:/Users/Utilizador/Documents/Codex/2026-10-11/co/outputs/providers-nexus.json.
Cobertura: ligacao real Open Notebook -> provider local -> resultado. Nao valida pesquisa completa, podcast, TTS/STT, nem integracao multimedia por frases livres na Folha. Proximo passo: voz local e teste de percurso completo de pesquisa/podcast; nao declarar todos os percursos integrados.


### Loop de ferramentas e percurso MoneyPrinter — 11-10-2026
Pedido humano: continuar em loop ate todas as ferramentas funcionarem em pleno; esclarecer LibreOffice/APIs dentro do MoneyPrinter. Objetivo de continuidade ativo, sem declarar fecho global.
Bateria real 20261011-095946: nucleo/Folha, revisao pt-PT, OpenNotebook/base/MCP, inferencia local e nova musica ACE-Step PASS. Forge/Deforum falharam inicialmente por servico desligado (10061); depois do arranque, nova imagem Forge, transcricao Speaches e animacao Deforum SUCCEEDED PASS. APIs atuais respondem em loopback: OpenNotebook 5055, linguagem 18081, embedding 18082, Piper 8969, Forge 7861, ACE-Step 8001, Speaches 8002, MoneyPrinter 8501.
Piper: ponte preparada instalada em configuracao/ponte-piper-local.py. Voz portuguesa local real PASS, rejeicoes de falta de auth/modelo/velocidade invalidos PASS. Alias protocolar alloy mapeia explicitamente para a mesma voz portuguesa, exigido pelo teste nativo OpenNotebook; nenhuma voz Alloy instalada. Lock Windows impede duplicacao. Abrir Nexus inicia a ponte tambem em reaberturas; sintaxe validada, duas chamadas de arranque deixaram um unico processo servidor (com launcher Python pai). Backups dos ficheiros alterados preservados.
OpenNotebook: providers TTS Piper e STT Whisper small ligados e testados, defaults anteriores guardados. Perfil Nexus PT local e episodio Nexus PT local curto criados sem modificar perfis existentes. Primeira geracao falhou por concorrencia TTS (429); configurado TTS_BATCH_SIZE=1 no .env, usando mecanismo nativo do podcast_creator, e reiniciado supervisor. Nova geracao command:3plvtfdx7nh9mltz4vxu COMPLETED, episode:kp6lvnh5k65sdllab7tk, MP3 transferido pela API autenticada e descodificado. E sucesso tecnico, nao qualidade editorial: guiao repete e acrescenta frases genericas, requer revisao humana.
Pesquisa local: novo caderno sintetico isolado, ingestao e embedding real, pesquisa textual e vetorial delimitadas ao caderno PASS. Nao equivale a pesquisa Web.
MoneyPrinter: teste nativo test_connection com modelo local PASS. Configurado transporte OpenAI-compatible ja existente na secao chatterbox para Piper pt_PT-tugao-medium, modelo nexus-piper-pt-pt; nao se instalou Chatterbox. Voice mode/voice name disponiveis no UI, reiniciado Streamlit. Whisper small preparado a partir do snapshot local, CPU/int8 para partilhar GPU; sem download novo. Montagem nativa nova com voz via rota configurada, animacao Deforum, musica ACE-Step e legendas Whisper PASS, task 15b68636-72ec-4bd8-878b-73cd3276d817. MP4 com audio/video, SRT nao vazio, zero warnings; frame com legendas inspecionado. Falhas iniciais por materiais/musica fora das pastas permitidas corrigidas com staging local, sem ampliar acessos. Primeiro ensaio de mistura tinha assertion incompleta; evidencia corrigida para FAIL_MUSIC_NOT_MIXED em moneyprinter-primeira-montagem-sem-musica.json. Montagem posterior exige resolucao BGM valida e ausencia de warnings. APIs Forge/ACE nao ficam registadas automaticamente como providers no UI do MoneyPrinter: transferencia testada por ficheiros locais.
Avatar: novo render WSL CPU com imagem sintetica e voz Piper concluido, MP4 descodificado com audio/video. Zotero: extensao LibreOffice registada; percurso real de citacao NOT RUN.
LibreOffice: gates existentes reais 5 PASS / 2 FAIL. Conversao direta/template/roundtrip/export funcionam, mas rotas book e convert_pdf no Host/LPAC falham. Fronteira e autoridade preservadas; nao houve alteracoes Kernel/Host/Store/sandbox. Este e um bloqueio de integracao conhecido, nao resolvido por reinstalar nem por PASS standalone.
Evidencia e artefactos em C:/Users/Utilizador/Documents/Codex/2026-10-11/co/outputs: ferramentas-nexus-verificacao.json, moneyprinter-percurso-real.json, moneyprinter-nexus-teste.mp4, moneyprinter-legendas.srt, podcast-nexus-teste.json/mp3, voz-nexus-testes.json, transcricao-provider-testes.json, pesquisa-local-testes.json, avatar-nexus-teste.mp4. Falhas Writer preservadas em work/writer-real-fixed; relatorios anteriores nao apagados.
Pendencias: Writer confinado; APIs automaticas de imagem/musica no MoneyPrinter e percursos livres pela Folha; pesquisa Web; citacao Zotero; qualidade editorial. Continuar pelos gates restantes, sem designar o conjunto perfeito ou totalmente pronto.


### 2026-10-11 — APIs locais nativas no MoneyPrinter

- PASS: Forge por ponte OpenAI images em 8970, arranque pelo abrir-nexus.py, geração real e 8 rejeições de pedidos inválidos. Configuração nativa MoneyPrinter usa nexus-forge-sd15.
- PASS: ACE-Step HTTP /release_task -> /query_result -> /v1/audio, faixa nova de 10 segundos. Adicionada extensão local app/services/nexus_ace_music.py ao registo nativo de fornecedores, opção Música local ACE-Step no UI e ace_step no CLI. Cópias de segurança preservadas. Sem alterações ao Kernel/Host/Store.
- PASS: tarefa 71bb3b8a-662f-4007-aec5-188cb2ead3e5 produziu MP4 com imagem Forge nova, voz Piper portuguesa, legendas Whisper CPU e música ACE-Step nova pela API, sem warnings e com publicação automática desativada. Evidência moneyprinter-todas-apis-testes.json.
- PASS: limites do adaptador (duração inválida, serviço indisponível, submissão incerta sem duplicação) em ace-adapter-testes.json. Job e hashes persistidos junto do WAV.
- Limites: qualidade editorial/estética não certificada; conversão Writer pela fronteira nativa continua FAIL em book/convert_pdf; Zotero citações e pesquisa Web por testar. Resultados anteriores mantidos.


### 2026-10-11 — Consolidação local em conjunto com GitHub

- Pedido humano: instalação e repositório trabalham em conjunto, preservando dados e trabalho existente; utilizador vê Folha/resultados. Ferramentas e dados devem concentrar-se em C:\Nexus; apagar somente redundâncias comprovadas.
- Arranque: Nexus.lnk na pasta Startup aponta para pythonw/abrir-nexus.py. Entrada Cerebro antiga retirada após backup e verificação de hash. Host foi iniciado após confirmar porta antiga encerrada; reabertura autenticada duas vezes PASS, sem novos runs. Logon após reboot NOT RUN.
- Zotero: biblioteca e perfil copiados/verificados (769+48 ficheiros) para dados/zotero; SQLite quick_check OK. Perfil padrão agora absoluto em C:\Nexus. Processo observado usa ferramentas/zotero e perfil consolidado; API local v3: identificação, items e itemTypes PASS. Biblioteca observada vazia (0 items); citações NÃO testadas. Originais e instalações Program Files ainda preservados, limpeza pendente.
- Windows: humano informou ter desligado SmartScreen/SAC; consulta confirmou SmartScreenEnabled Off e VerifiedAndReputablePolicyState 0. Host não controla estas definições. Pedido de capacidade futura: propor/efetuar alterações autorizadas através do mecanismo administrativo Windows; NOT IMPLEMENTED, sem privilégios permanentes inventados.
- Repositório principal clonado isoladamente no SHA e9fc98aa425e4b5340cd25bdf9c5f113f8a2468d. Suite Writer local inicial: 3 FAIL/1 PASS (observação de 90 s excedida; uma conversão chegou posteriormente a HUMAN_REQUIRED; book terminou launcher129). Diagnóstico direto da mesma solução Sandy: PDF válido, original/hash preservados, saída0 em95.86s; apenas provider, sem Human Gate nesta prova.
- Benchmark conservou identidade exata dos13.992ficheiros: serial130.468s/paralelo10.672s, 4workers. Alteração mínima em branch local/writer-hash-parallel-20261011, não instalada nem publicada; suite completa nova ainda sem PASS. Não transferir PASS remoto para o PC.
- Evidência: outputs/consolidacao-local-etapa-testes.json, writer-unificado-testes.xml, writer-unificado-diagnostico.json, writer-hash-benchmark.json e resultados Zotero/arranque. Próximo: resolver custo da cópia/validação e validar rotas reais, depois integrar com código/configurações locais.


### 2026-10-11 — Medição e cópia limitada do runtime Writer

- Suite anterior terminada: 31 PASS/3 FAIL; os três percursos reais ultrapassaram os 90 s de observação. Não declarar integração pronta.
- Experiência de cópia com 4 workers/32 pedidos pendentes preservou a identidade exata de 13.992 ficheiros. Tempos: hash fonte20.609 s, cópia28.641 s, hash cópia40.219 s; não prova prazo E2E.
- Branch local adiciona cópia paralela limitada, propagação de erros e rejeição de redirecionamentos; conserva verificações completas e portões. Sete testes unitários PASS, incluindo conteúdo/caminhos, erros, diretórios vazios e metadata. Alteração não instalada nem publicada.
- Nova suite real em curso (sessão72860); evidência em writer-copy-parallel-testes.xml quando terminar. Não reiniciar apenas por timeout de observação.
- Pedido humano reafirmado: Host deverá ter acesso autorizado para ativar/desativar proteções conforme perigo. Capacidade ainda NOT IMPLEMENTED. Microsoft confirma reativação de SAC por UI em atualizações recentes; isto não prova API automatizável.


### 2026-10-11 — Retorno Writer e recuperação Zotero

- Nova suite Writer terminou:34 PASS/3 FAIL por observação90 s. Book e convert_pdf chegaram depois a HUMAN_REQUIRED (~124/127 s); FAIL original preservado.
- Nos dois candidatos sintéticos, reabertura, aprovação pelo HTTP Host, original inalterado, PDF em Canonical e restauro do commit PASS, com Writer bloqueado contra repetição. Evidência writer-delayed-return-testes.json; não transforma o prazo90 s em PASS.
- Diagnóstico sem sobreposição: fonte11.563 s/cópia10.812 s/validação cópia31.563 s/validação final10.719 s, total77.671 s. PDF sintético uma página e texto esperado PASS; imagem inspecionada, sem cortes/sobreposições. Teste completo book isolado em curso (sessão72427).
- Zotero tinha encerrado (API connection refused). Criado C:\Nexus\abrir-zotero.ps1 com caminhos fixos para perfil/biblioteca consolidados, deteção de instância e verificação API. Primeiro verificador HTTP incompatível: FAIL preservado; UserAgent próprio/DisableKeepAlive corrigiram. API três rotas200/v3 e reutilização sem novos processos PASS. Citações LibreOffice NOT RUN.
- Evidência adicional: zotero-launcher-testes.json, zotero-api-local-testes.json e histórico, writer-copy-phases.json, writer-pdf-content-testes.json. Instalação ativa Writer ainda não substituída; alteração de código não publicada.


### 2026-10-11 — Correção de âmbito e revisão antes de prosseguir

- Correção humana explícita: Nexus pode orquestrar funções Windows em proveito do Nexus/utilizador. A afirmação anterior do assistente excluindo Windows foi interpretação errada, não decisão humana. Host coordena, pessoa é autoridade final.
- Reconsultados pedidos desta conversa, chats Generalizar fluxo Nexus/Nexus unificação e testes/Prosseguir instalação Nexus, estado operacional e evidência do PC. Não confundir relatórios remotos/Linux sem acesso ao PC com testes locais.
- Estado atual confirmado: SmartScreen Off, SAC0, sessão não administrativa; controlo das proteções pelo Host ainda NOT IMPLEMENTED. Arranque configurado/testado por reabertura, logon real NOT RUN. Zotero API/launcher PASS, citações NOT RUN.
- PR57 já MERGED; main e3833856, árvore idêntica ao e9fc98aa anterior. Referência main obtida na cópia de trabalho. Alterações instaladas inventariadas e preservadas; não aplicar substituição indiscriminada.
- Writer: medição completa117.312 s (hashes12.375/40.969/21.422, cópia14.687, limpeza7.172). A limpeza não é o principal custo. Gate90 s mantém FAIL, mesmo isolado; retorno/aprovação/restauro tardios separados PASS. Não repetir a hipótese de que somente sobreposição explica o atraso.
- Revisão/evidência: outputs/revisao-nexus-windows-unificacao.json. Próximo: resolver Writer, reconciliar main/configurações locais e continuar integrações/controlo Windows autorizado com testes reais; objetivo global permanece incompleto.


### 2026-10-11 — Aceitação final combinada e fontes do Host local

- Código combinado final: Writer nativo 37 PASS/0 FAIL,445.24s; revisão inline/preexecução72 PASS; regressão dirigida191 PASS; Folha/teclado29 PASS. Browser Chrome real PASS:4 produtos/6 etapas,desktop/mobile,restauro e zero chamadas Host na preparação. LanguageTool real PASS com origem exata e reinício sem reexecução.
- Backup dos dados:238ficheiros copiados/verificados e restauro demonstrado; Store novo abriu17pedidos restaurados sem mudar qualquer byte nem executar ferramenta/promover Canonical. Sandy fixado autenticado instalado permanentemente em C:\Nexus\ferramentas\sandy.
- Acrescentadas fontes revistas nexus/windows/local-host:8scripts exatos do PC (entrada única,supervisores IA/OpenNotebook/SurrealWSL,pontes Piper/Forge,Zotero),manifesto e instalador explícito idempotente sem arrancar serviços ou tocar dados/segurança. Patch ACE4caminhos reproduzível contra MoneyPrinter68eb5a68; não enviar config.toml/ambientes/dados/segredos. Validação PowerShell5/7,Python e hashes PASS; instalação pelo pacote NOT RUN. Marcadores públicos locais não são credenciais nem autenticação forte.
- Estudo do anexo:Python coordena motores nativos já existentes; não instalar outra ponte C++ nem reintroduzir Conductor/YAML executor. Health uniforme/identidade de providers e controle Windows autorizado continuam tarefas próprias.
- Histórico local preservado:13entradas,11acrescentadas,2já presentes,zero conflitos. Regressão padrão integral em curso,excluindo6módulos de volume com gates próprios. Ativação aguarda este gate; app/dados ativos preservados. Evidência local outputs/unificacao-combinacao-etapa.json e relatórios individuais.

### 2026-10-11 — Revalidação Windows e remoção autorizada do legado

- Regressão integral inicial preservada:1840 PASS/40 FAIL/20 SKIP. Os FAIL expuseram requisitos opcionais ausentes/incompatíveis no Host e fixtures que disputavam portas dos serviços reais. Instalados os requisitos já fixados:mcp1.23.2,Trio0.34.0,open-notebook-mcp0.2.0 do commit fixado. Não alterada a fronteira de produção.
- Fixtures de testes passam a usar portas efémeras e encaminhamento só de sockets IPv4 loopback explicitamente mapeados; URLs e validações de produção mantêm-se. Revalidação dos8módulos:87 PASS/0 FAIL,1894.75s. Inclui todos os40FAIL anteriores; nenhum convertido em SKIP. Ramo Linux do helper NOT RUN neste PC.
- Nomes de4casos Office agora explícitos, eliminando timestamps ZIP dos identificadores; mesmas entradas e asserções. Módulo completo repetido:26 PASS/1warning intencional de entrada ZIP duplicada.
- Consolidação de execuções, não uma nova execução integral única:1901casos atuais exatamente cobertos,1881 PASS/20 SKIP/0 FAIL. Ficheiros Python de produção e os40selos conservam os bytes do99d1fad; relatórios originais FAIL mantidos. Evidência:unificacao-regressao-consolidacao.json e XMLs integral/corrigida/office-identidades em outputs locais, com hashes dos relatórios/testes/requisitos e versões.
- Humano escolheu instalar localmente por agora; não publicar a branch/commit. Autorizou explicitamente retirar conductor-cli0.1.41. Remoção efetuada apenas desse pacote;331ficheiros registados ausentes,backup e restauro por hash verificados,pip check PASS. Os restantes pacotes não foram desinstalados. Evidência:conductor-legado-remocao-testes.json.
- main evoluiu para0f39fc81(PR58) durante os testes. Alterações de transporte/UI revistas em paralelo; integração e novos gates dirigidos decorrem antes da ativação local. Não transferir o PASS acima para a UI nova sem repetir os seus testes.

### 2026-10-11 — main PR58 combinado e aceitação local antes de ativar

- Merge local40094bd une main0f39fc81 com Writer/inline/teclado e fontes do Host do PC. Resolvidos conflitos conservando ambos os grupos de testes e restantes39selos; apenas selo ui/app.js recalculado para8d47180398c87a39bbf704629b5b2ab66d0a13dd878aae9c7e828fa99d39f2bf. Python de produção conserva os bytes99d1fad. main reconferido por leitura, sem publicar.
- Seleção Python afetada:110 PASS/0 SKIP, incluindo os2E2E reais gateway→Host→Store. Node44 PASS/0 FAIL/0 SKIP,smokes inline/teclado/revisão/pesquisa PASS. Chrome real PASS,0botões iniciais,4briefs/6etapas,desktop/mobile,restauro e0chamadas Host na preparação.
- Primeiro Node43 PASS/1 FAIL na preparação do primeiro gateway, antes de enviar a operação; FAIL preservado em unificacao-pr58-node-primeiro-arranque-FAIL.log. Fixture agora observa readiness por10s entre sondagens; limites HTTP4s,transporte30s,stream truncado<2s e asserções de efeitos/replay inalterados. Não foi diagnosticada a causa exata da lentidão nem alterado prazo de produção.
- Consolidação final explícita de4relatórios Python, não uma execução única:1902casos atuais,1883 PASS/19 SKIP/0 FAIL. Os40FAIL originais foram revalidados; módulo Office completo repetido; classes revalidadas cobrem exatamente a coleção atual. Delta de produção PR58 e hashes/ambiente registados, sem alegar produção integralmente inalterada. Gates de volume6módulos e Writer nativo são próprios, não somados a esta contagem.
- Preparação para ativação local autorizada: clone integral do commit final,binários Sandy/LibreOffice permanentes,backup integral da aplicação anterior com restauro verificado,dados238ficheiros e17pedidos preservados. Relatório de ativação e prova final de serviço devem ser PASS antes de designar esta etapa instalada. Zotero citações,produtos multimédia finais pela Folha e controlo Windows mantêm os limites anteriores.
