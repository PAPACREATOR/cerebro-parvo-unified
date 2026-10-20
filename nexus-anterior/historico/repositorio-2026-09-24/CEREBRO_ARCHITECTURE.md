# Arquitetura consolidada — v0.4, 2026-09-24

Este ficheiro aponta para a arquitetura operacional corrente. A v0.3 de 2026-09-22 (Logseq + Activepieces + dois SQLite) é histórica e a razão da mudança está em MIGRACAO-ARQUITETURAL-2026-09-24.md.

## Circuito
HUMAN → JOPLIN → thin bridge → TINY MODEL SANDBOX (NL→proposal only) → PYTHON DETERMINISTIC CORE → Markdown + EventLog + SQLite.

O tiny model não é memória nem autoridade. O Core deve continuar funcional sem ele.

## Core
Intent Validator; Event Engine; Process Router; Working Memory; Behavioral/Procedural Memory; Persistent Knowledge (Creative + Canonical); Candidate Engine; Provenance; Claims/Relations/Contradictions; Genealogy; Algorithmic Will; Research Loop; Human Authority; Recovery/Replay/Invariants.

## Memória
Creative preserva processo cognitivo: hipóteses, alternativas, contradições, erros, fontes, versões e rejeições. Canonical preserva a versão humana atualmente consolidada. Promoção não destrói Creative. Canonical não significa verdade universal.

## Persistência
Markdown = portable persistent knowledge.
EventLog = causal history.
SQLite = structured operational state/index/projection.
Cada tabela SQLite é REBUILDABLE ou AUTHORITATIVE; rebuild é provado por teste.

## Interface
Joplin é implementação atual da camada humana, não dependência ontológica. O utilizador trabalha em linguagem natural sem gerir Markdown/SQLite/paths/plugins. O bridge deve ser menor e mais simples que o Core e não conter lógica cognitiva.

## IA
Input: human_text + minimal_context + allowed_intents.
Output: intent + arguments + references + confidence/ambiguity.
Sem direct persistent memory, Canonical, human goals, CoreRules, Web research, filesystem ou program execution. Ambiguidade relevante → ASK_HUMAN. Não há escalada interna para LLM grande.

## Iniciativa e pesquisa
Algorithmic Will calcula próxima operação útil a partir de objetivos humanos, gaps, staleness, contradições, evidência e custo. Cada subobjetivo deve ser rastreável a finalidade humana.
Research Loop: gap→question→search→sources→provenance→compare→candidate→Creative→human→Canonical se aprovado.

## LEGO
Consultar LEGO-LOCK.md. Runtime deliberadamente curto: Joplin + Python + SQLite + Markdown + EventLog + TinyModelSandbox + CérebroCore. Projetos externos fornecem produto, código seletivo ou padrões; não se tornam automaticamente serviços.

## Segurança
Core network-deny por defeito quando viável; tiny model com mínimo privilégio; versões externas pinadas; sem silent updates; hash/diff/security+compatibility tests/rollback. Trust(code)=Source+Provenance+Audit+Reproducibility+Isolation+Tests.

## Regra de mudança
ObservedFailure AND CurrentArchitectureCannotSolve antes de novo framework/LEGO/DB/model/protocolo/serviço.

Detalhe normativo: ARQUITETURA-ATUAL-2026-09-24.md.
