# Fundação Nexus — revisão de continuidade

1 de outubro de 2026. Documento de análise; não altera Constituição, leis ou arquitetura.

## Fontes e precedência
Revisão do snapshot Git origin/main (1e58020027d46377d75eb337616bb8418b1f0404), em particular CEREBRO_CONSTITUTION.md, DECISIONS.md (30/09), docs/baseline/CEREBRO_PROMPT_MESTRE_CURSOR_2026-09-26.md e a nota histórica sobre memórias/comparadores de 23/09; confronto com a especificação Nexus Minimal fornecida nesta conversa, código nexus e evidências locais. Não representa releitura integral de todos os chats ou de todo o acervo.

Decisão humana posterior prevalece. As invariantes conceptuais sobrevivem à simplificação. Activepieces/Joplin/Logseq e os dois SQLite obrigatórios pertencem a etapas anteriores e não devem regressar por leitura isolada de documentação antiga. A Constituição no snapshot ainda contém implementação Activepieces de 28/09; DECISIONS de 30/09 e a instrução humana atual fixam Folha/Host/Conductor. Conservar a genealogia; não fundir silenciosamente documentos.

## As três memórias
1. Trabalho: contexto limitado e transitório da tarefa em curso. Não é o arquivo nem o contexto ilimitado de uma IA.
2. Comportamental/procedimental: regras, preferências, rotinas, correções e experiência confirmadas, versionadas e auditáveis. Experiência bem-sucedida só vira processo normativo após decisão humana.
3. Conhecimento persistente: conteúdo duradouro, separado em Creative (evolução, propostas, alternativas, erros e contradições) e Canonical (versões aprovadas).

Estas são funções, não uma exigência de três bases de dados. Logs, índices, backups e a base interna do Open Notebook não constituem novas memórias soberanas.

## Dois cérebros
Expressão recuperada da secção 0.3 da baseline:
- exploratório/adaptativo: interpreta, relaciona, pesquisa, propõe hipóteses e realiza trabalho permitido;
- determinístico/constitucional: identidade, regras, autoridade, eventos, integridade, proveniência, genealogia, estados e gates.

Não significa dois modelos de IA. Host verifica; Conductor coordena o processo; capacidades especializadas executam; Open Notebook/Tiny entram quando a tarefa exige cognição. Nenhum destes ganha autoridade normativa. A pessoa governa ambos.

## Três comparadores
Determinístico (valores, hashes, versões, limites); semântico (significado e contradições candidatas); relacional (ligações, dependências, fontes e genealogia). São usados conforme o processo. Concordância não promove Canonical.

## Estados: três famílias distintas
- Resultado/verificação: PASS, FAIL, UNKNOWN.
- Controlo: BLOCKED e HUMAN_REQUIRED, entre outros estados de andamento.
- Reconciliação de operação crítica: COMMITTED, NOT_COMMITTED, RECOVERY_REQUIRED.

A baseline também contém READY/REVIEW/FAILED para classificação de conteúdo. Não escolher um destes trios como significado exclusivo da frase “três estados” sem conservar esta distinção. Aprovação não transforma incerteza em verdade. Canonical significa aprovado com a evidência disponível.

## Leis preservadas
Humano como autoridade; promoção explícita ligada ao item/versão/destino; informação externa e saída de IA como candidatos; originais/proveniência/genealogia preservados; divergência visível; nenhuma eliminação por similaridade; nenhuma ampliação automática de permissões; contexto mínimo; replay não repete IA/web para fabricar o passado; backup exige restauro demonstrado; falha e desconhecimento não são sucesso. Usar componentes existentes antes de criar código. M1–M14 são responsabilidades, não 14 serviços.

## M1–M14: cobertura atual do Nexus
| Responsabilidade | Evidência / limite |
|---|---|
| M1 Identidade | IDs de execução; identidade durável de documentos/blocos ainda incompleta |
| M2 Documentos/blocos | Texto e um anexo; edição estruturada pendente |
| M3 Versões/genealogia | Hash de candidato e aprovação; evolução completa pendente |
| M4 Creative | Candidatos persistidos; gestão completa ainda parcial |
| M5 Canonical | Escrita pelo gate na aplicação; isolamento Windows pendente |
| M6 Portão humano | Sessão, confirmação, versão e ticket testados |
| M7 Relações | Referências básicas; comparador relacional pendente |
| M8 Proveniência | Input/processo/ferramenta/output registados no circuito testado |
| M9 Contradições | Estados e duas evidências preservados; semântica ainda não testada |
| M10 Pesquisa/recuperação | Histórico simples; web/Zotero não integrados |
| M11 Regras | Política, schemas e integridade; oito leis resumidas não substituem a Constituição completa |
| M12 Eventos/auditoria | Logs e proveniência; replay autoritativo completo não demonstrado |
| M13 Integridade/recuperação | Alguns testes passaram; encontrado novo FAIL de reconciliação |
| M14 Coordenação | Conductor real; iniciativa adaptativa ainda não demonstrada |

## Novo FAIL reproduzível
Interrompida artificialmente a atualização do estado depois da publicação atómica do pacote Canonical. No reinício, conteúdo e aprovação existem em Canonical, mas a execução continua HUMAN_REQUIRED. Não houve promoção sem aprovação: o ensaio forneceu aprovação sintética válida em pasta de teste. A falha é a incoerência do estado e a ausência de reconciliação. Evidência em FOUNDATION-CRASH-EVIDENCE.json.

Os 51 testes anteriores passaram, mas não cobriam esta janela. Assim, o conjunto não deve ser descrito como totalmente PASS. Resolver este microprocesso antes de ampliar integração. A baseline deixa o protocolo geral autoritativo POR DEFINIR; uma correção local não deve ser apresentada como solução de todo o protocolo.

## Conta e ferramentas
Conta Nexus não encontrada; pasta ProgramData/NexusMinimal não criada na verificação de hoje. O assistente abriu o pedido de criação, mas não deve afirmar que a conta foi criada. Isolamento continua não demonstrado.
LibreOffice e Zotero instalados. LibreOffice passou ensaios isolados ODT/PDF. Open Notebook passou acesso/contratos; Tiny e interpret.yaml ausentes. Pesquisa desta conversa não equivale a capability instalada no Host.

## Continuação ordenada
1. Fechar recuperação de aprovação e bloquear estados inconsistentes; reproduzir falha e regressão.
2. Concluir criação da conta com intervenção humana e testar permissões com dados artificiais.
3. Restauro de cópia de ensaio e verificação de conteúdo/proveniência.
4. Ligar LibreOffice e Zotero por processos autorizados e verificar resultados reais.
5. Escolher/configurar Tiny, implementar circuito cognitivo limitado e testar violações.
6. Integrar pesquisa web e comparadores necessários, sem novos componentes por antecipação.
7. Validar a experiência pela Folha, arranque/reinício e matriz completa de requisitos.
