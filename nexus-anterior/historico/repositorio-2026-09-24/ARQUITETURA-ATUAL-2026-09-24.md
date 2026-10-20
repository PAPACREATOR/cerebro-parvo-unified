# Arquitetura atual — fecho conceptual de 2026-09-24

Autor da conceção: Pedro Alexandre Caldas Coelho.
Estado: decisão arquitetural corrente. Substitui, sem apagar, a composição Logseq + Activepieces + dois SQLite documentada em 2026-09-22.

## Por que mudou

A arquitetura anterior ajudou a fixar princípios que permanecem: autoridade humana, núcleo determinístico, replay, proveniência, IA sem autoridade e USE > ADAPT > CREATE. A investigação posterior mostrou, porém, que obrigava o utilizador e a implementação a manter demasiadas fronteiras: Logseq + Activepieces + cofre final + dois SQLite + automação externa. A dor original é precisamente reduzir trabalho técnico humano.

A mudança não rejeita a genealogia anterior. É uma simplificação orientada pela regra: **a máquina trabalha para a pessoa; a pessoa não trabalha para manter a máquina**.

Joplin passa a ser a plataforma humana madura e substituível para edição, notas, anexos, pesquisa, desktop/mobile e sincronização. O Core continua independente. Activepieces deixa de ser requisito do produto: pesquisa, prioridades, continuidade e recuperação pertencem ao Core e a adaptadores específicos quando necessários.

## Arquitetura

```text
HUMANO
  ↓ linguagem natural
JOPLIN — camada humana substituível
  ↓ thin bridge
TINY MODEL SANDBOX — NL → proposta estruturada apenas
  ↓ proposal
PYTHON DETERMINISTIC CORE
  ├─ Intent Validator / Process Router
  ├─ Event Engine / Replay / Recovery
  ├─ Working Memory
  ├─ Behavioral / Procedural Memory
  ├─ Persistent Knowledge
  │    ├─ Creative
  │    └─ Canonical
  ├─ Candidate / Provenance
  ├─ Claims / Relations / Contradictions
  ├─ Genealogy
  ├─ Algorithmic Will
  ├─ Research Loop
  └─ Human Authority
  ↓
Markdown + EventLog + SQLite
```

## Contratos constitucionais

- `LLMOutput = Proposal`.
- `LLM ↛ PersistentMemory`.
- `LLM ↛ Canonical`.
- `LLM ↛ HumanFinalGoals`.
- `LLM ↛ CoreRules`.
- `Remove(TinyModel) => Core remains functional`.
- Ambiguidade significativa => `ASK_HUMAN`.
- `Canonical(x) != True(x)`: canónico significa versão humana atualmente aprovada, não verdade universal.
- Creative persiste depois de promoção/rejeição; preservar hipóteses, erros, alternativas, fontes e genealogia.
- Algorithmic Will gera próxima operação útil, nunca finalidade humana nova.
- Web/pesquisa externa produz evidência/candidato, nunca Canonical diretamente.
- `AUTO-CURA != AUTO-VERDADE`.

## Persistência

- Markdown = representação portátil do conhecimento persistente.
- EventLog = história causal/auditável.
- SQLite = estado estruturado, índices e projeções.
- Cada tabela SQLite será classificada `REBUILDABLE` ou `AUTHORITATIVE`; não assumir reconstrução sem teste.
- Escritas críticas usam lock/journal/receipt/verificação e recuperação. Backup só é considerado validado depois de restore bem-sucedido.

## Linguagens e fronteiras

- Interface humana: linguagem natural.
- Joplin bridge: TypeScript/JavaScript mínimo ou Data API, conforme teste.
- Protocolo: JSON estruturado.
- Core/testes: Python, stdlib-first.
- Base: SQLite.
- Conhecimento portátil: Markdown.
- Eventos: formato simples versionado (JSON/JSONL é candidato).
- Tiny model: runner isolado; sem filesystem, memória persistente, credenciais ou rede por defeito.

## Regra de fecho

Não procurar novo framework/LEGO/base/modelo/protocolo sem:
`ObservedFailure AND CurrentArchitectureCannotSolve`.

Ordem: CLOSE → REUSE → IMPLEMENT MINIMUM → TEST → BREAK → MEASURE → SIMPLIFY → VALIDATE.

A confiança conceptual histórica aproximada (~85%) permanece congelada até evidência de implementação, testes, ablação, recovery, hardware fraco e utilizadores diversos. A nova arquitetura reduz risco de implementação; não prova o comportamento final.
