# Decisões

Este ficheiro regista decisões humanas e genealogia. Decisões antigas permanecem como histórico mesmo quando substituídas.

## 2026-09-22 — baseline histórico
Foi consolidada arquitetura Logseq Classic/File Graph + Activepieces + cofre final separado + dois SQLite. Foram fixados princípios que permanecem: autoridade humana, núcleo determinístico, eventos/replay/idempotência, IA sem autoridade, linguagem normal, USE>ADAPT>CREATE, proveniência e sandbox. Esta composição concreta foi substituída em 2026-09-24, não apagada.

## 2026-09-23 — princípios sobreviventes
IA não confiável/substituível; AIOutput=Proposal; sandbox obrigatória e Docker não; adaptação humana sem criar objetivos; iniciativa instrumental; Creative+Canonical persistentes; evidência de isolamento Windows sem alterar a confiança histórica ~85%.

## 2026-09-24 — fecho arquitetural corrente
Pedro decidiu simplificar a arquitetura para ficar mais próxima da dor original: trabalhar em linguagem natural sem manter infraestrutura cognitiva manualmente.

- Joplin substitui Logseq como camada humana atual, madura e substituível.
- Activepieces deixa de ser dependência arquitetural; não é substituído automaticamente por n8n.
- Core permanece Python-first, determinístico e independente da interface.
- Markdown=representação portátil; EventLog=causalidade; SQLite=estado/índice/projeção, com tabelas REBUILDABLE/AUTHORITATIVE.
- Deixa de existir obrigação de dois SQLite.
- Tiny model é a única IA interna prevista: NL→structured proposal, sandboxed, contexto mínimo, sem memória/objetivos/regras/Web/programas.
- Não há fallback para LLM grande; tarefas difíceis são decompostas deterministicamente ou perguntadas ao humano.
- Creative preserva hipóteses, alternativas, erros, rejeições, fontes e genealogia. Canonical é conhecimento humano atualmente consolidado, não verdade universal.
- Algorithmic Will é prioridade/iniciativa operacional determinística, não vontade humana.
- Research Loop: gap→questão→fontes→proveniência→comparação→candidate→Creative→humano→Canonical se aprovado.
- AUTO-CURA != AUTO-VERDADE.
- Joplin Sync é primeira solução de sync a testar.
- Novo LEGO/framework/DB/model/protocolo/serviço exige ObservedFailure AND CurrentArchitectureCannotSolve.

### LEGO
Joplin=USE; second-brain=REUSE/ADAPT; knowledge-worker=REUSE/ADAPT; GBrain=ADAPT/REIMPLEMENT pattern; Will=ADAPT/REIMPLEMENT event/replay; Pith=ADAPT/REFERENCE; PCA=método.

### Licenças/supply chain
Antes de copiar código: fixar commit/tag, verificar licença no commit/ficheiro, notices, dependências/permissões e testes. Joplin AGPL permanece separado do Core salvo decisão específica. MIT/Apache não dispensam atribuição/NOTICE aplicável.

### Validação
A reutilização reduz trabalho genérico e risco de implementação, mas não valida hipóteses originais. Manter ~85% conceptual congelado até testes reais.

Ver ARQUITETURA-ATUAL-2026-09-24.md, MIGRACAO-ARQUITETURAL-2026-09-24.md, LEGO-LOCK.md e COMPATIBILITY-MATRIX.md.