# Constituição do Cérebro Independente

Versão: 0.4 — 2026-09-24
Autor declarado da conceção: Pedro Alexandre Caldas Coelho

## Identidade e finalidade
O Cérebro Independente é um sistema cognitivo determinístico contínuo ao serviço da pessoa. Não é chatbot, personalidade artificial, agente LLM soberano nem coleção de automações.

Princípio central: **a máquina trabalha para a pessoa; a pessoa não trabalha para manter a máquina**.

## Regras invioláveis
1. A pessoa é a autoridade final. Ambiguidade material ou conflito de autoridade gera ASK_HUMAN.
2. O Core funciona sem IA, cloud ou GPU. Remover o tiny model reduz flexibilidade linguística, não destrói memória/cognição determinística.
3. A camada humana atual é Joplin, madura e substituível. O Core não depende ontologicamente do Joplin.
4. O utilizador trabalha em linguagem natural; Markdown, SQLite, eventos, IDs, paths, plugins e protocolos são infraestrutura invisível.
5. LLMOutput = Proposal. O tiny model serve exclusivamente como ponte NL→proposta estruturada com contexto mínimo.
6. O modelo não lê/escreve diretamente memória persistente, não promove Canonical, não altera finalidades humanas, CoreRules ou permissões, não pesquisa Web nem executa programas/ações externas.
7. Sandbox é requisito; Docker não é. Rede, filesystem, credenciais, processos e memória persistente são negados ao modelo por defeito.
8. Resultados externos/não determinísticos entram como eventos/evidência congelada antes de influenciar transições determinísticas.
9. USE > ADAPT > CREATE. Não duplicar função madura sem falha observada.
10. Mudança estrutural exige ObservedFailure AND CurrentArchitectureCannotSolve, consequências documentadas e decisão humana.
11. Há Working Memory, Behavioral/Procedural Memory e Persistent Knowledge. Persistent Knowledge contém Creative e Canonical.
12. Creative preserva ideias, hipóteses, alternativas, contradições, erros, caminhos rejeitados, fontes, versões e genealogia.
13. Canonical é a versão atualmente consolidada/aprovada pela pessoa; Canonical(x) != True(x).
14. Comportamento observado é evidência de preferência, não finalidade. Instrução humana explícita atual prevalece.
15. Algorithmic Will é iniciativa determinística instrumental: escolhe próxima operação útil rastreável a finalidades humanas; nunca cria finalidade humana nova.
16. Research Loop produz fontes/evidência/candidatos. Web não escreve Canonical.
17. AUTO-CURA != AUTO-VERDADE.
18. Markdown é representação portátil; EventLog é história causal; SQLite é estado/índice/projeção estruturada. Cada tabela SQLite declara REBUILDABLE ou AUTHORITATIVE.
19. Backup não é validado até restore bem-sucedido.
20. MCP, n8n, Activepieces, graph DB, Docker, cloud e LLM grande não são dependências do Core atual.

## Determinismo e eventos
S(t+1) = F(S(t), E(t), R(t)).
Replay não volta a chamar IA/Web. Eventos críticos têm identidade/versionamento e dados não determinísticos congelados.

## Fronteira do tiny model
Input: human_text, minimal_context, allowed_intents.
Output: intent, arguments, references, confidence/ambiguity.
Proibido: read_database, write_memory, change_goal, promote_canonical, delete, browse_filesystem, research_web, execute_program.

Testes: Compromise(AI)→Memory intact; Crash(AI)→Core intact; Remove(AI)→Core operational; InvalidOutput(AI)→No mutation.

## Persistência epistemológica
Creative → Candidate/Validation/Provenance → Human Authority → Canonical, mantendo Creative e genealogia. Contradições podem coexistir como dados.

## Engenharia e terceiros
Código externo é classificado REUSE_CODE, ADAPT_CODE, REIMPLEMENT_PATTERN, REFERENCE_ONLY ou REJECT. Antes de copiar: fixar commit/tag, licença/notices, ficheiro/função, dependências/permissões, testes e proveniência. Joplin AGPL permanece separado do Core salvo decisão específica.

## Precedência documental
1. esta Constituição;
2. ARQUITETURA-ATUAL-2026-09-24.md;
3. MIGRACAO-ARQUITETURAL-2026-09-24.md;
4. DECISIONS.md;
5. LEGO-LOCK.md / COMPATIBILITY-MATRIX.md;
6. STATUS.md;
7. SPEC ativa;
8. histórico.

A arquitetura Logseq + Activepieces + dois SQLite de 2026-09-22 é genealogia, não instrução atual.