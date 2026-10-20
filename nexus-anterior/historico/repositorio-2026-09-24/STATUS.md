# Estado operacional

Atualizado: 2026-09-24

## Estado conceptual
Arquitetura fechada para implementação e testes. A composição de 2026-09-22 (Logseq + Activepieces + dois SQLite) é histórica. Decisão corrente: ARQUITETURA-ATUAL-2026-09-24.md; razão/genealogia: MIGRACAO-ARQUITETURAL-2026-09-24.md.

Runtime alvo: Joplin + thin bridge + Python deterministic Core + Markdown + EventLog + SQLite + TinyModelSandbox.

Confiança conceptual histórica aproximada (~85%) permanece congelada. Reutilização reduz risco de implementação, não valida comportamento final.

## LEGO fechado
Joplin=USE; second-brain=REUSE/ADAPT storage/recovery; knowledge-worker=REUSE/ADAPT candidate/provenance/discovery; GBrain=REIMPLEMENT_PATTERN claims/relations/contradictions; Will=REIMPLEMENT_PATTERN event/replay; Pith=REIMPLEMENT_PATTERN/REFERENCE behavioral weighting; PCA=método/referência.

Commits/tags/licenças por ficheiro ainda devem ser fixados antes de copiar código real.

## Estado de implementação
O GitHub contém principalmente documentação/especificações. Pedro indicou trabalho local até F2 que pode não estar enviado; não declarar esse código validado, obsoleto ou substituído até ser inspecionado. A migração deve aproveitar implementação compatível.

## Próxima execução
1. Fixar versões/commits e proveniência LEGO.
2. Reconciliar SPECs antigas com arquitetura corrente sem apagar história.
3. Inspecionar código local quando estiver acessível/pushed.
4. Implementar/testar em microtarefas.

## Ainda não validado
Creative+Canonical sem lixo/complexidade; Algorithmic Will útil sem deriva; Behavioral sem transformar comportamento em finalidade; tiny model NL→intent com baixo erro; continuidade após shutdown/semana; valor do sistema completo sobre Joplin+search+memória simples; suficiência do Joplin Sync; instalação/recovery; necessidade real de A/L/S/G.

## Não fazer
Não reabrir arquitetura por curiosidade. Não instalar ecossistemas LEGO completos. Não adicionar MCP/n8n/Activepieces/graph DB/cloud/LLM grande/Docker obrigatório sem falha observada. Não apagar histórico. Não assumir SQLite descartável. Não promover pesquisa/IA para Canonical sem humano.