# Registo da mudança arquitetural — 2026-09-24

## Decisão humana

Pedro Alexandre Caldas Coelho decidiu substituir a composição operacional Logseq + Activepieces + dois SQLite por uma arquitetura mais simples centrada em Joplin como camada humana, Core Python determinístico, Markdown/EventLog/SQLite e tiny model isolado apenas como ponte de linguagem.

## O que NÃO mudou

Autoridade humana; núcleo funcional sem IA; determinismo; eventos/replay; proveniência; Creative + Canonical persistentes; sandbox; linguagem natural; USE > ADAPT > CREATE; finalidade humana; subobjetivos apenas instrumentais; genealogia das decisões; testes antes de confiança.

## O que mudou e porquê

**Logseq → Joplin:** a finalidade não é possuir um grafo específico, mas oferecer uma superfície madura, natural e invisível tecnicamente. Joplin é tratado como plataforma substituível; o Core não deve depender do DOM ou ontologia da UI.

**Activepieces deixa de ser requisito:** a automação externa acrescentava runtime, instalação, filas, Postgres/Redis/WSL/Docker e outra fronteira de estado. O Core já necessita de event engine, processos/microprocessos, research loop e recovery. Só se reintroduz automação externa perante falha observada que o Core/adaptador não resolva.

**Dois SQLite → SQLite com classificação por autoridade:** a antiga separação nasceu para proteger a fronteira dos cofres. A nova separação epistemológica é Creative/Canonical e a causal é EventLog. SQLite é usado apenas onde traz estrutura/índice/estado. Cada tabela declara REBUILDABLE ou AUTHORITATIVE.

**IA efémera genérica → tiny model exclusivamente NL→Proposal:** elimina escalada para modelos grandes dentro do Cérebro. Tarefas difíceis são decompostas por processos determinísticos. O modelo não pesquisa, não escreve memória, não promove, não altera objetivos/regras e não executa.

**Projetos comparáveis → LEGO explícito:** second-brain e knowledge-worker passam a candidatos de reutilização seletiva; GBrain, Will e Pith fornecem padrões pequenos; não são instalados como ecossistema.

## Genealogia

Os documentos de 2026-09-22 permanecem evidência do percurso intelectual e técnico. Quando contradizem esta decisão, são históricos, não instruções de implementação atuais. Não apagar as razões anteriores: a arquitetura nova deriva dos problemas encontrados na anterior.

## Regra para agentes

Precedência corrente:
1. CEREBRO_CONSTITUTION.md
2. ARQUITETURA-ATUAL-2026-09-24.md
3. MIGRACAO-ARQUITETURAL-2026-09-24.md
4. DECISIONS.md
5. LEGO-LOCK.md e COMPATIBILITY-MATRIX.md
6. STATUS.md
7. SPEC ativa
8. documentos históricos

Nenhum agente pode ressuscitar Logseq, Activepieces, dois SQLite, MCP, n8n, Docker obrigatório, graph DB ou LLM grande por conveniência. Só uma falha observada + incapacidade demonstrada da arquitetura corrente reabre a decisão.
