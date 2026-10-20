# Decisões vigentes e genealogia

## 06-10-2026 — reconciliação documental e Writer editorial

A documentação ativa foi alinhada com o runtime candidato realmente testado: Kernel/Host/Store Python + MCP determinístico + ferramentas externas. Activepieces, Memory Provider, Spiff e Conductor permanecem preservados como genealogia em decisões, histórico e relatórios, mas deixam de aparecer como dependências vigentes.

Foi separado o que já está provado no LibreOffice do que ainda é capacidade futura. F007 continua a representar DOCX/ODT → PDF. O novo contrato `nexus/docs/CAPABILITY-WRITER-EDITORIAL.md` define Writer editorial completo em W001–W020: ODT editável, estilos, páginas, gutter, cabeçalhos/rodapés, viúvas/órfãos, imagens/legendas, sumário, PDF, round-trip, adulteração, restart e Human Gate.

Decisão de implementação preferida para esta capability: ODF/ODT determinístico + LibreOffice para render/export; UNO só quando necessário e testável; macros não são mecanismo normal.

Isto adiciona capacidade, não altera M1–M14 nem autoridade.

## 05-10-2026 — reconciliação documental da implementação candidata

A [PR #21](https://github.com/PAPACREATOR/cerebro-parvo-/pull/21) documenta a remoção de Conductor/Spiff/YAML de execução do ativo; a [PR #23](https://github.com/PAPACREATOR/cerebro-parvo-/pull/23) é a única continuação. Kernel/Host/Store Python, MCP determinístico, ferramentas externas e Human Gate constituem a composição candidata. A pessoa continua autoridade máxima; M1–M14 e os princípios não são reabertos por esta nota.

A entrada de 30/09 mantém a genealogia do produto, mas as suas escolhas de executor/templates foram substituídas na implementação. O [ponto de situação](nexus/docs/PONTO-DE-SITUACAO.md) é a fonte operacional para SHAs, PASS/FAIL e limites. Referência verde histórica não equivale a HEAD atual aprovado.

Esta entrada regista decisões já materializadas e evidência anterior; não cria uma nova decisão arquitetural.

## Desenvolvimento: problema, decisão e evidência

| Fase | Problema / objetivo | Desenvolvimento e razão | Evidência e limite |
|---|---|---|---|
| 27–28/09 — receção e persistência | Receber dados e guardar estado recuperável sem atribuir autoridade à ferramenta | Contratos de importação e writer PREPARED → materialização → verificação → COMMITTED/reconciliação; separar escrita de aprovação | Suites históricas preservadas; issues #3/#4 continuam abertas e exigem reconciliação com o candidato atual |
| 28/09 — composição com ferramentas existentes | Evitar reconstruir capacidades maduras | Estudo Activepieces, Memory Provider e ferramentas externas; consolidou a regra LIGAR > CONFIGURAR > ADAPTAR > CRIAR | Os documentos de 28/09 são genealogia da composição; não obrigam a reinstalar esses componentes |
| 30/09 — Folha e bancada descartável | Dar uma entrada simples e manter memória independente da IA | Nexus como launcher metódico; OpenNotebook delimitado por tarefa; Creative/Canonical e decisão humana fora do modelo | Princípios preservados na entrada de 30/09; escolha de executor evoluiu depois |
| 01–04/10 — execução e recuperação Windows | Demonstrar arranque, ida/volta, proveniência e recuperação com ferramentas | Folha/Host/Store, testes Windows, comparação Spiff/Conductor e processo de falha → correção → repetição | Relatórios F011–F013 e comparações datadas preservados; runner não prova PC pessoal |
| 04/10 — runtime Python mínimo | Reduzir dependências e componentes de execução preservando os contratos | PR #21 remove Conductor/Spiff/YAML de execução do ativo após trabalho comparativo e regressão; não remove leis nem Human Gate | PR #21 regista falhas da migração e suites Windows; a genealogia da alternativa permanece |
| 04–05/10 — MCP e ferramentas externas | Chamar ferramentas sem dar autoridade ao transporte nem tornar IA obrigatória | MCP stdio, allowlists, OpenNotebook delimitado; normalização de respostas e fecho de sessão corrigidos após FAIL | 1.000 operações MCP; E2E do Kernel usa uma fronteira HTTP simulada, não backend/modelo completos |
| 04–05/10 — avatar e multimédia | Reutilizar o podcast existente e acrescentar vídeo; preparar ferramentas locais de imagem/música | Áudio existente + retrato → Wav2Lip/FFmpeg; ACE-Step/Forge externos; instalação/checks Windows | Avatar curto real CPU Linux; 165 testes por OS; health check não demonstra geração; PC/GPU e pedido escrito completo pendentes |
| 05/10 — consolidação e revisão | Evitar continuações concorrentes e documentação que manda executar componentes antigos | Uma PR ativa, um documento de estado; esta revisão corrige os pontos de entrada e distingue histórico de candidato | A comparação 7e1ec9b → 7faead6 é documental; o novo FAIL Practical Windows fica explícito e não é ocultado por PASS anteriores |

A razão transversal é reduzir engenharia e dependências sem perder comportamento exigido. Uma mudança de mecanismo não prova a implementação de toda a arquitetura. O critério de progresso continua a ser contrato, execução observada e evidência reproduzível; não o número de bibliotecas, commits ou testes isolados.

## 30-09-2026 — Nexus Minimal: launcher metódico + bancada descartável (HISTÓRICA; princípios mantidos, executor substituído)

A arquitetura foi reduzida novamente para preservar funções e cortar engenharia própria.

### Formulação vigente

**Nexus é um launcher metódico, com memória, leis e templates executáveis, que compõe ferramentas existentes para atingir um fim.**

Fluxo principal:

```text
Humano → Folha em linguagem natural → Condutor
                                  ├→ template/processo conhecido → ferramenta/capability
                                  └→ problema novo → Open Notebook/tiny → resultado
                                                        ↓
Creative → VERIFY → PASS/FAIL/UNKNOWN → Human Gate quando exigido → Canonical
                                                        ↓
                                    experiência validada → template candidato
```

### Responsabilidades fechadas

- **Folha Nexus:** interface inicial em linguagem natural; anexos, resultados e Human Gates. Infraestrutura fica invisível na utilização normal.
- **Conductor:** runtime/condutor candidato para flows, routing, scripts, MCP, paralelismo e gates. Deve passar testes locais antes de ser dependência definitiva.
- **Open Notebook:** apenas bancada cognitiva. Não é memória Nexus, Creative, Canonical, arquivo, Wiki, autoridade ou interface principal.
- **Nexus/Windows:** memória soberana, regras, proveniência, histórico, processos/templates e continuidade.
- **Tiny local:** cognição probabilística apenas quando necessária, dentro do pacote de trabalho autorizado.
- **Capabilities:** LibreOffice, Zotero, LanguageTool, web, imagem, áudio, Whisper/TTS etc. entram por processo, nunca por antecipação.

### Memória soberana

A memória durável pertence ao Nexus e deve permanecer em formatos portáveis/reconstruíveis: Markdown, JSON, YAML, fontes originais, hashes e logs; SQLite/FTS5 pode servir de índice/estado quando necessário. Destruir Open Notebook não pode destruir conhecimento Nexus.

### Agente em microprocesso

Um agente não precisa de identidade persistente. Pode ser reconstruído por tarefa como:

`tiny + prompt + contexto permitido + leis + ferramentas permitidas + schema + objetivo`.

Executa, devolve resultado estruturado e termina. O que persiste é memória/processo/proveniência, não o agente.

### Templates/processos

Experiência validada pode ser compilada num processo explícito e testável (`process.yaml`, schemas, prompts, regras e testes). A primeira resolução pode usar mais cognição; ocorrências semelhantes devem reutilizar o processo e, quando possível, reduzir chamadas à IA. Aprendizagem nunca aumenta autoridade.

### Benchmark externo único

Para impedir dispersão, o único projeto externo escolhido para comparação arquitetónica nesta fase é **Negentropy-Laby/OpenDoge**. Motivos: local-first/single-operator, workflow templates, runtime contracts, approvals, evidence/replay e extensão por slots/capabilities. É benchmark, não dependência nem arquitetura a copiar. Só se adapta algo se reduzir código/risco sem violar leis Nexus e com licença compatível.

### Testes que decidem

1. Folha → condutor → bancada → JSON → Creative → Folha;
2. Canonical não aceita escrita direta;
3. Human Gate permite promoção explícita;
4. Open Notebook pode ser destruído/reconstruído sem perda Nexus;
5. tiny não ganha acesso fora do pacote permitido;
6. proveniência percorre resultado ↔ processo ↔ contexto/evidência ↔ fonte/pedido;
7. microprocessos independentes podem comparar e produzir PASS/FAIL/UNKNOWN;
8. tarefa semelhante reutiliza experiência/processo com menos descoberta;
9. substituir tiny/bancada não destrói leis nem memória.

### Regra de engenharia

**LIGAR > CONFIGURAR > ADAPTAR > CRIAR.** O Core programa sobretudo cola, contratos, memória, leis, auditoria e testes. Não reprogramar motores maduros.

---

## 28-09-2026 — simplificação Activepieces + Memory Provider (HISTÓRICA / SUPERADA)

A fase anterior propôs Activepieces Community + um Memory Provider SQLite/MCP como dois blocos nucleares. Foi útil para provar que workflows, memória e providers podiam ser desacoplados, mas ainda atribuía demasiada responsabilidade a um provider de memória e mantinha um motor específico como centro conceptual.

Os candidatos RMANOV/sqlite-memory-mcp e Beledarian/mcp-local-memory permanecem referências históricas. Não são dependências vigentes e só regressam perante FAIL concreto.

PiecesOS permanece benchmark histórico/proprietário, não dependência.

## Decisão anterior — Activepieces + Open Notebook + K-DLC (HISTÓRICA)

Demonstrou que ferramentas maduras podiam substituir grande parte do código próprio, mas acumulava providers e responsabilidades. Open Notebook regressa agora com responsabilidade muito mais estreita: **bancada de trabalho apenas**.

## Evidência histórica de implementação

Código Python e writer recuperável já testados permanecem preservados como fallback/evidência. Não são apagados e não voltam a ser obrigatórios sem FAIL real.
