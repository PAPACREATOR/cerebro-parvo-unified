# Relatório — Wiki 100K, complemento de 04/10/2026

Estado: **PASS no ensaio sintético delimitado; estudo global PARCIAL**.

Base: `b0a82e63eae60fdec66afdee6705246c0d3465ea`. Branch de trabalho: `lab-wiki-complemento-20261004`.
Executor SHA-256: `1f1495ebbb99607a58a7cc4d2b9a407ca8e1a0b9114fbe6195178cd3348db7e5`.
Ambiente: Linux-6.18.44-x86_64-with-glibc2.39; Python 3.12.14.

| Verificação | Resultado observado |
|---|---|
| Materialização Markdown | 100000 objetos; 50000 fontes + 50000 notas |
| Pesquisa FTS5 | 50000 consultas com resultados esperados exatos |
| Relações | 50000 pares verificados nos dois sentidos |
| Reconstrução | Índice eliminado e reconstruído; 100000 hashes verificados |
| Renomeação | Identidade da nota preservada após mudança de nome físico |
| Adversariais | 6 cenários distintos rejeitados pela causa esperada |
| Processo novo | Uma relação recuperada sem chamar provider |
| Duração total | 20.114 segundos, inclui limpeza temporária |
| Markdown, tamanho lógico | 22088890 bytes |
| SQLite/FTS5, tamanho lógico | 33050624 bytes |
| Média lógica total | 551.40 bytes/objeto neste corpus pequeno |

Evidência: [summary.json](../lab/wiki/evidence/20261004/summary.json).
Comando: `python nexus/lab/wiki/test_web_research_wiki_100k.py --cases 100000 --output nexus/lab/wiki/evidence/20261004`.

100000 é uma contagem de objetos parametrizados, não de cenários independentes, páginas web reais ou testes semânticos. Os tempos são uma observação única, não benchmark comparativo. Não extrapolar estes tamanhos para PDFs/livros/fontes reais.

O ficheiro anterior era um placeholder e o relatório anterior NOT RUN. Este resultado pertence ao executor com hash indicado, após a correção. CI remoto desta alteração não foi observado nesta sessão.

NOT RUN: Windows, web/IA reais, histórico de versões, qualidade semântica, concorrência/crash, Human Gate integrado, UI e integração Nexus. Reutilização não foi comparada editorialmente nem em desempenho com/sem contexto.

Auditoria documental existente: PASS, 47 ficheiros históricos preservados e 89 ligações ativas. Não constitui teste de produto.

Ver [complemento e contrato proposto](COMPLEMENTO-WIKI-INFORMACAO-GERADA-2026-10-04.md). Nenhuma promoção para Canonical; nenhum merge ou alteração da instalação oficial.
