# Auditoria da proposta «arquitetura Lego»

**Correção posterior, 2026-09-22:** Pedro reafirmou os dois cofres e depois esclareceu que há **dois SQLite**, um interno e vivo no cofre final e outro espelhado. A pessoa escreve normalmente no Logseq criativo; Markdown é tratado pelo sistema. As notas abaixo que descrevem SQLite apenas como espelho/indexação ou como base única estão **superadas**; preservam-se como histórico, não regra operacional. Aprovação humana do item/versão continua condição necessária. Ver Constituição v0.3, Arquitetura v0.3 e `ARQUITETURA-CORRIGIDA-2026-09-22.md`.

**Correção de leitura — 2026-09-22, 21:33 Europe/Lisbon:** Pedro reafirmou explicitamente **dois cofres** e pediu releitura das versões. A análise inicial abaixo tomou a frase isolada «Vault final Markdown» como substituição efetiva do Final Vault SQLCipher. Isso foi uma **inferência excessiva do assistente**, não uma decisão confirmada de Pedro. O histórico F01/F02/F03/F04/F05/F07/F09/F12 preserva, com variações, Logseq criativo separado do cofre final SQLite/SQLCipher. O texto Lego recente está em tensão com esse histórico; até decisão expressa, **não fundir os cofres nem revogar SQLCipher**. Ver `MAPA-DE-VERSOES-COFRES-ACTIVEPIECES.md`.

Registo: 2026-09-22, 21:27 Europe/Lisbon. Autor da conceção declarado: Pedro Alexandre Caldas Coelho. Objeto: dois textos recentes de Pedro, incluindo o anexo `590460ce-a570-4dbb-b524-78ccb8496abb`. **Estado: proposta recebida e analisada, não alteração aprovada da Constituição ou Arquitetura anteriores.** O texto do anexo não comprova a data original da formulação das ideias.

## Veredicto curto

A composição de Logseq Classic/File Graph, Markdown, SQLite, Python mínimo, Activepieces e Zotero **é viável em princípio e reduz código próprio**, sobretudo porque Activepieces já tem execução durável de workflows, com checkpoint, retoma e waitpoints. Não é «completamente errada». Mas não é apenas uma simplificação de implementação da versão anterior: **muda a fonte canónica do conhecimento e o modelo de privacidade**, e deixa por decidir onde vive o estado operacional irrecuperável a partir do Markdown. A nova arquitetura não deve substituir silenciosamente a anterior.

## Diferenças materiais, sem apagar versões

| Contrato | Constituição/Arquitetura atuais | Proposta Lego recente | Consequência e decisão pendente |
| --- | --- | --- | --- |
| Fonte canónica | Final Vault SQLite + SQLCipher + FTS5, separado do cofre criativo Logseq. | Vault final Markdown, editado/mostrado por Logseq Classic; SQLite é espelho. | **Conflito estrutural.** Pedro tem de decidir se revoga SQLCipher como Vault final, se conserva dois cofres, ou se há uma terceira formulação. Markdown em disco não é cifrado por SQLCipher; requer proteção própria se for privado. |
| Logseq | Superfície cognitiva e cofre criativo; adaptador fino, potencial suporte file/DB. | Logseq Classic/File Graph escolhido explicitamente; Markdown é fonte de verdade. | Reduz ambiguidade e favorece extração inicial para Markdown. Fixar versão, sintaxe suportada e política de alterações por plugin/sync. Não chamar a DB Graph compatível sem teste. |
| SQLite | Final Vault canónico, cifrado, com proveniência, evidência, confiança e supersession. | Espelho rápido do Markdown + hashes + pequeno estado operacional. | O índice é reconstruível; estado de entregas/aprovações não o é **a menos que** exista diário durável independente. Uma só base pode conter ambas as classes, mas devem ter regras de backup/recuperação diferentes. |
| EventLog/replay | EventLog append-only e replay do estado canónico do núcleo. | Texto recente sugere reconstruir SQLite pelo Vault e usar replay operacional Activepieces. | Durable Execution **não é** replay semântico do Core. Se a exigência de auditoria/replay integral for mantida, precisa de eventos versionados de decisões e inputs não derivados do Markdown. Revogá-la seria mudança estrutural expressa. |
| Activepieces | Integração externa F3, com outbox/retry. | Scheduler, pesquisa, APIs, espera e recuperação de workflows. | Boa redução de código. Mesmo assim, passo em curso pode repetir após crash; operações externas precisam IDs estáveis/idempotência e reconciliação. O run log mantém só o checkpoint mais recente, não o histórico canónico. |
| Zotero | Não constava do núcleo consolidado. | Responsável por PDFs, referências e proveniência bibliográfica. | Candidato maduro. A API local existe, mas só funciona com a aplicação aberta e opção ativada; leitura local não requer autenticação, escrita exige aprovação/chave. Definir se o Zotero entra no protótipo ou fase posterior. |
| Fases | Objetivo confirmado: F4 **técnica = IA efémera sem ação**, após F-1/F0–F3. | Quatro fases novas, nas quais «fase 4» significa capacidades avançadas. | **Colisão de numeração.** Tratar como sequência Lego L1–L4 proposta, sem substituir F0–F4 ou prometer outro alvo. |

## Interfaces reais a fechar

Primeiro ciclo mínimo proposto: `Markdown aprovado → índice SQLite → seleção determinística de 1 tema → pedido Activepieces com ID estável → resultado bruto/Candidate durável → decisão humana → escrita Markdown com proveniência → reindexação`. O Vault não recebe output da Internet, de Zotero, de Activepieces ou de IA sem uma decisão humana registada. A UI concreta de aprovação continua por especificar; não inventar uma parede de botões.

Para evitar um «duplo cérebro», usar as seguintes identidades distintas: `source_id` para nota/ficheiro ou referência Zotero; `candidate_id` para achado; `event_id` para ocorrência/decisão; `correlation_id` para pesquisa/fluxo; `causation_id` para ligação causal. Uma nota idêntica em bytes não é necessariamente a mesma ocorrência nem dispensa proveniência. Nenhum ID deve ser inferido apenas do texto quando isso apagaria eventos legítimos iguais.

## Prova matemática e limites

Se `V` é o conjunto de Markdown aprovado e `I` o índice derivado, o contrato reconstruível é `I = g_v(V)` com uma versão fixa `v` do extrator, ordenação e serialização canónicas. **Isto não prova** `SQLite = g_v(V)`, porque a proposta também põe estado operacional `O` no SQLite: `SQLite = I ⊕ O`. Se a base desaparecer, `I` pode ser refeito; `O` só pode ser recuperado se tiver diário/backup próprio ou se for reconciliado por identificadores com o Activepieces. Chamar o SQLite inteiro de «descartável» seria falso.

Se `F_v` é a transição determinística, para a mesma sequência ordenada e versionada de eventos `E`, regras `R` e configuração `K`, exigir `H(F_v(S_0,E,R,K))` idêntico em duas reconstruções. Inputs de Web, Zotero, Activepieces e IA são observações não determinísticas: o seu conteúdo validado tem de entrar como evento congelado; replay **não** volta a chamar os serviços. O replay de um workflow Activepieces resolve outra pergunta: onde retomar a execução operacional após interrupção.

Para a entrada no Vault: `commit(C,A)` só altera `V` se `A` for aprovação humana válida para `candidate_id`, versão e hash concretos; repetição do mesmo `event_id` não altera `V` pela segunda vez. Um crash entre escrever Markdown e marcar a entrega como concluída exige reconciliação por ID no Markdown, nunca uma segunda nota silenciosa.

A regra proposta `Hash(A)=Hash(B) ∧ A=B ⇒ DELETE_auto` **não é suficiente**: mesmo bytes iguais podem ter caminhos, referências, anexos, permissões, histórico e proveniências diferentes. Hash é filtro de candidatos a duplicado, não autorização de eliminação. Até haver contrato de identidade/referências e cópia recuperável, `DELETE_auto=FALSE`; sugerir ao humano é seguro. Além disso, `A=B` exato torna a igualdade de hash redundante como condição lógica, embora útil como otimização de comparação.

Uma previsão honesta de sucesso não sai da contagem de peças. Para o ciclo completo `P(PASS)=P(L1)×P(L2|L1)×P(L3|L1,L2)×…`; os fatores são desconhecidos enquanto não houver ensaios. Mesmo 30 ciclos independentes sem falha só limitariam aproximadamente a taxa de falha por ciclo a 9,5% no limite superior unilateral de 95% (`1−0,05^(1/30)`); 300 ciclos sem falha dão cerca de 1%. Ensaios repetidos no mesmo cenário não são independentes e sustentam menos. Hoje há **zero** ciclos ponta a ponta testados, portanto nenhuma percentagem calibrada. Estamos perto de uma especificação testável, não de uma garantia de produto funcional.

## Complexidade que sai e complexidade que fica

Sai do código Python: agendamento, filas de workflows, checkpoints de passos, espera/retoma, biblioteca bibliográfica e editor de notas. Fica: identidade/proveniência, normalização e versão do Markdown, seleção de temas, espelho reconstruível, políticas de entrada/consentimento, reconciliação após falhas, proteção de dados, logs/eventos canónicos e testes de ponta a ponta. A redução do código próprio pode ser substancial; o custo total continua `T = T_configuração + T_adaptadores + T_contratos + T_testes + T_operação`. Não há dados de tempo para dizer «x% mais simples».

Os maiores testes falsificáveis são: (1) editar nota e reindexar sem duplicar; (2) destruir só o índice e obter o mesmo hash; (3) matar worker Activepieces a meio e verificar retoma sem duplicar efeitos; (4) repetir webhooks e aprovações com o mesmo ID; (5) interromper entre aprovação e escrita e reconciliar; (6) assegurar que fonte externa sem aprovação não altera o Vault; (7) desligar IA e manter o ciclo; (8) restaurar Zotero/Markdown/estado operacional a partir dos backups adequados. Não executar estes testes sobre o acervo real sem cópia sintética.

## Evidência primária consultada

- [Logseq: diferenças File Graph/DB Graph e APIs](https://github.com/logseq/logseq/blob/master/libs/guides/db_properties_guide.md); [Logseq OG/File Graph](https://github.com/logseq/og); [SDK de plugins](https://github.com/logseq/logseq/blob/master/libs/src/LSPlugin.ts).
- [Activepieces: Durable Execution](https://www.activepieces.com/docs/install/architecture/durable-execution): checkpoints, retomada, passo em curso reexecutável e última cópia do checkpoint; [waitpoints](https://www.activepieces.com/docs/install/architecture/waitpoints); [HTTP piece](https://www.activepieces.com/pieces/http); [retry de runs](https://www.activepieces.com/docs/mcp/tools).
- [Zotero: API local](https://www.zotero.org/support/dev/web_api/v3/local_api): leitura offline, opção de ativação, versão/identidade do servidor e autorização separada de escrita.

Esta é validação **documental e matemática dos contratos**, não instalação nem teste executado dos componentes. Nenhum ficheiro de Constituição/Arquitetura foi alterado nesta análise.
