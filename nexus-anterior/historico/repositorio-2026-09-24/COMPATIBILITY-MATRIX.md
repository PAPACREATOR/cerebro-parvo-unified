# Matriz de compatibilidade — arquitetura 2026-09-24

## Runtime pretendido

`Joplin + thin bridge + Python Core + SQLite + Markdown + EventLog + TinyModelSandbox`.

Will, Pith, GBrain, second-brain e knowledge-worker são minas de mecanismos/código, não cinco serviços adicionais.

| Fronteira | Contrato | Prova mínima |
|---|---|---|
| Joplin ↔ Bridge | operações mínimas de nota/recurso + IDs estáveis | capture/store/retrieve/open/continue |
| Bridge ↔ Core | JSON versionado | schema + malformed/duplicate/out-of-order |
| Tiny ↔ Core | Intent Proposal | ambiguidade→ASK_HUMAN; invalid output→no mutation |
| Core ↔ Markdown | representação portátil | round-trip + hash + conflito |
| Core ↔ EventLog | causalidade | replay produz estado/hash esperado |
| Core ↔ SQLite | projeção/estado classificado | rebuild apenas onde declarado REBUILDABLE |
| Candidate ↔ Creative | rejeição preservada | reject não destrói hipótese |
| Candidate ↔ Canonical | promoção humana | zero promoção sem aprovação concreta |
| Behavioral ↔ HumanAuthority | evidência, não finalidade | instrução explícita sobrepõe padrão |
| AlgorithmicWill ↔ HumanGoals | rastreabilidade | cada subobjetivo aponta para finalidade humana |
| Research ↔ Knowledge | evidência→candidate | Web nunca escreve Canonical |

## Compatibilidade de linguagem

Python é a linguagem oficial do Core. TypeScript/JavaScript fica limitado à fronteira Joplin se necessário. JSON evita acoplamento de runtime. GBrain/Will não justificam Bun/Node adicionais no produto; os mecanismos úteis são reimplementados/adaptados em Python.

## Compatibilidade Windows

Alvo: Windows 10/11, sem Docker obrigatório. Sandbox é obrigatória. O mecanismo concreto será escolhido por teste de isolamento, IPC, runner/GPU, instalação e recovery. O núcleo não depende de GPU.

## Supply chain

Fixar versões/commits; negar updates silenciosos; rever imports/dependências/network/filesystem/subprocess; guardar notices; testar antes de atualizar; manter rollback. Core network-deny por defeito quando operacionalmente possível.

## Critério

Compatibilidade deixa de ser opinião quando os testes de fronteira passam. Uma peça tecnicamente executável mas que aumenta manutenção humana sem valor marginal suficiente deve ser removida.
