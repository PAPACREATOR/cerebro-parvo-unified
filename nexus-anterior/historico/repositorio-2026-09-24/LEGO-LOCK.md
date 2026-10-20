# LEGO Lock — 2026-09-24

Estado: seleção arquitetural congelada; commits/tags exatos devem ser fixados e auditados antes de copiar código.

| LEGO | Papel | Estratégia | Runtime no produto | Licença a verificar no commit fixado |
|---|---|---|---|---|
| Joplin | camada humana madura | USE | sim | AGPL-3.0-or-later no Desktop/repo atual; verificar versão |
| stancsz/second-brain | persistência/recovery | REUSE_CODE / ADAPT_CODE seletivo | não como serviço | MIT; verificar ficheiro/commit |
| rahulmranga/knowledge-worker | candidates/provenance/discovery | REUSE_CODE / ADAPT_CODE seletivo | não como serviço | MIT; verificar ficheiro/commit |
| garrytan/gbrain | claims/provenance/contradições | REIMPLEMENT_PATTERN | não | MIT; verificar commit |
| mindot-ai/will | event/tick/replay determinístico | REIMPLEMENT_PATTERN | não | Apache-2.0; verificar commit |
| pithrun/pith-core | behavioral weighting/decay | REIMPLEMENT_PATTERN / REFERENCE | não | Apache-2.0; verificar commit |
| PCA | método de especificação/execução | REFERENCE_ONLY | não | verificar antes de copiar qualquer material |

## Regra de proveniência

Antes de reutilizar código real registar: origem, autor/projeto, URL, commit/tag, data, licença e hash da licença, ficheiro/função, dependências, rede/filesystem/subprocess, decisão (REUSE_CODE/ADAPT_CODE/REIMPLEMENT_PATTERN/REFERENCE_ONLY/REJECT), alterações Cérebro e testes.

Open source não significa copiar sem condições. MIT/Apache exigem preservação dos avisos aplicáveis. Código Joplin AGPL não é incorporado no Core sem decisão específica e revisão das consequências de distribuição.

## Blocos alvo

### second-brain
Estudar lock, receipt, crash journal, snapshot, restore, rebuild, digest e conflict preservation. Rejeitar MCP, agent-host assumptions, cloud/Git sync/Postgres/Supabase/rclone salvo falha futura concreta.

### knowledge-worker
Estudar candidate lifecycle, validation, provenance, promote/merge e discovery determinístico (staleness, question debt, weak/single-source claims, bridges/tensions e métricas de grafo quando justificadas). Rejeição no Cérebro permanece em Creative.

### GBrain
Adaptar em Python esquema Entity/Claim/Relation/Source/Confidence/Timestamp/Contradiction e identidade/proveniência. Não trazer Bun/TypeScript/runtime apenas para isto.

### Will
Adaptar event/step/record/replay/state hash/stable clock. Não trazer personalidade, identidade artificial, objetivos existenciais ou runtime Will.

### Pith
Começar com função pequena de BehaviorEvidence: source/time/frequency/confidence/current_weight/contradictions. Instrução humana explícita atual prevalece sempre.

## Testes constitucionais de qualquer LEGO

`Compromise(TinyModel) => Memory intact`
`Crash(TinyModel) => Core intact`
`Remove(TinyModel) => Core operational`
`InvalidOutput(TinyModel) => No mutation`
`Reject(Hypothesis) => Hypothesis remains in Creative`
`AlgorithmicWill => no new HumanFinalGoal`

Nenhum LEGO entra se quebrar autoridade humana, determinismo/replay, portabilidade ou substituibilidade.
