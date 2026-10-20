# Instruções obrigatórias para agentes

Projeto: Cérebro Independente
Autor e Gatekeeper: Pedro Alexandre Caldas Coelho

## Antes de alterar
Ler: CEREBRO_CONSTITUTION.md → ARQUITETURA-ATUAL-2026-09-24.md → MIGRACAO-ARQUITETURAL-2026-09-24.md → DECISIONS.md → LEGO-LOCK.md → COMPATIBILITY-MATRIX.md → STATUS.md → SPEC ativa.

## Método
Uma SPEC de cada vez: contrato → implementação mínima → testes → resultados → revisão humana → parar. Aplicar USE > ADAPT > CREATE. Tarefas de programação devem indicar Goal, referência, dependências permitidas, proibições, invariantes e testes.

## Arquitetura congelada
Runtime: Joplin + thin bridge + Python Core + SQLite + Markdown + EventLog + TinyModelSandbox.
- Joplin é camada humana substituível; lógica cognitiva não entra no bridge.
- Python é linguagem do Core; stdlib-first.
- Tiny model apenas NL→structured proposal; sem memória persistente, filesystem, credenciais, rede, pesquisa ou autoridade.
- Creative e Canonical persistem; rejeição/promoção não apaga genealogia.
- Human Authority prevalece.
- Algorithmic Will só cria prioridades/subobjetivos instrumentais rastreáveis a objetivos humanos.
- Web/pesquisa gera candidato/evidência, nunca Canonical.
- SQLite: cada tabela REBUILDABLE ou AUTHORITATIVE.
- Joplin Sync é primeira solução de sincronização a testar.

Não ressuscitar por conveniência: Logseq, Activepieces, dois SQLite obrigatórios, MCP, n8n, graph DB, Docker obrigatório, cloud obrigatória ou LLM grande.
Nova tecnologia só com ObservedFailure AND CurrentArchitectureCannotSolve.

## LEGO
Consultar LEGO-LOCK.md. second-brain/knowledge-worker podem fornecer código seletivo após licença+commit+ficheiro+testes. GBrain/Will/Pith são principalmente padrões a adaptar/reimplementar em Python. Nunca instalar todos como serviços.

## Segurança e paragem
Não commitar segredos. Não dar auto-approve global. Fixar versões, rever network/filesystem/subprocess e manter rollback. No fim da SPEC apresentar ficheiros alterados, proveniência, testes PASS/FAIL, invariantes, riscos e trabalho restante. Falha bloqueia avanço.