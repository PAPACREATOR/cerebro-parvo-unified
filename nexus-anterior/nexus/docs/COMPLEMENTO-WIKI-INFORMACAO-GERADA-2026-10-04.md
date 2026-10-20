# Complemento do estudo — wikis e informação gerada

04-10-2026. Estatuto: estudo experimental e proposta de contrato; não altera a arquitetura.
Base inspecionada: `lab-wiki-knowledge-20261004`, `b0a82e63eae60fdec66afdee6705246c0d3465ea`.
Trabalho isolado: `lab-wiki-complemento-20261004`. Sem merge, PR de integração ou escrita no PC.

## Memória recuperada e corrigida pela inspeção

A decisão vigente de 30/09 em `DECISIONS.md` define Nexus como launcher metódico com memória soberana, leis e templates. Conductor executa; Open Notebook/tiny é bancada substituível. As páginas anteriores sobre Activepieces explicam a genealogia, não prevalecem automaticamente sobre essa decisão posterior.

O laboratório wiki foi delimitado em `LAB-WIKI-KNOWLEDGE-2026-10-04.md`: dados sintéticos, objetos Markdown, identidade, relações, índice reconstruível e reutilização. Os ensaios Spiff/Conductor e a versão oficial são trabalhos separados.

Falha documental observada: o commit `b0a82e6`, intitulado como implementação real, deixou `test_web_research_wiki_100k.py` com uma única linha de comentário. O relatório estava NOT RUN. Executar esse ficheiro podia terminar com código zero sem testar nada. Esta sessão substitui o placeholder por um executor observável; não atribui retroativamente PASS ao estudo anterior.

## O que deve ser guardado

| Informação | Tratamento proposto | O que não significa |
|---|---|---|
| Fonte recolhida | Original, URL quando exista, data de recolha, hash e referência estável | A URL ou o hash não provam verdade factual |
| Texto gerado por IA | Candidato Creative; ligar a pedido, versão do processo, modelo/configuração e fontes efetivamente fornecidas | Não é fonte independente nem conhecimento aprovado |
| Afirmação extraída/síntese | Ligar ao trecho e versão de origem; distinguir citação, inferência e hipótese | Uma relação não prova que a fonte sustenta a afirmação |
| Resultado de teste | Contrato, entrada, esperado, observado, ambiente, commit, comando, erro e evidência | PASS técnico não aprova conteúdo nem fecha produto |
| Falha/correção | Preservar falha, diagnóstico, alteração e repetição que a verifica | Não substituir o FAIL histórico por um PASS novo |
| Relação/contradição sugerida | Proposta com origem e versões; apresentar para revisão quando aplicável | Não funde objetos, não elimina, não transfere autoridade |
| Aprendizagem sobre processo | Template candidato com âmbito, limites e testes de regressão | Não altera regras/permissões automaticamente |
| Decisão humana | Vincular à versão/hash, ação e destino concretos | Não aprova futuras versões por arrasto |

A wiki é uma forma de navegar estas relações. Não exige uma nova aplicação: páginas e índices derivados podem apresentar o conhecimento que já foi preservado. O índice deve poder ser reconstruído; a evidência original deve sobreviver à perda da bancada ou do índice.

## Circuito mínimo a contratar para integração

1. Receber output como não confiável; validar envelope, limites e referências.
2. Preservar original e candidato em Creative, sem executar instruções contidas no texto.
3. Registar proveniência do pedido/processo/contexto/fontes e versão do resultado.
4. Executar verificações aplicáveis; conservar PASS/FAIL/UNKNOWN com escopo explícito.
5. Extrair relações como dados. Uma referência ausente/corrompida deve aparecer como inválida; não como suporte confirmado.
6. Disponibilizar pesquisa e retorno resultado → fonte e fonte → usos.
7. Submeter promoção protegida ao portão humano existente. Pesquisa, aprovação técnica e ligação a Canonical não substituem aprovação humana.
8. Reutilizar apenas contexto cuja integridade e referências foram verificadas, com proveniência do novo resultado.

Duplicação exata não implica perder relações de origem: mesmo que se partilhem bytes, dois eventos de produção continuam eventos diferentes. Semelhança, títulos iguais, resumos ou paráfrases apenas permitem sinalização. Este laboratório não elimina nem promove objetos.

Versionamento: identidade do objeto deve ser distinta da identidade da versão. Uma alteração gera versão ligada à anterior e preserva as referências antigas. O ensaio atual valida apenas versão 1 e renomeação física; não implementa este contrato de histórico.

## Molde: o que existe e o que ainda falta

F009 existe, mas o seu YAML inicial só aceita a família multimédia com campos fixos. Não é um schema geral para fonte, afirmação, experiência ou relatório. Reutilizá-lo sem rever contrato produziria uma falsa integração.

O ensaio usa um envelope **experimental** num comentário Markdown contendo JSON (`id`, `version`, `kind`, `domain`, `origin`, `refs`) e corpo UTF-8. Não se propõe este formato como norma. SQLite/FTS5 é apenas índice temporário; hashes esperados são gerados fora desse índice no ensaio.

Para integração falta fixar o contrato do objeto de conhecimento e mapear para os pacotes reais F013/Store, aproveitando o que já existe. Não criar um segundo gestor de aprovação, novo executor ou base autoritativa.

## Método efetivamente executado

100000 casos de objeto = 50000 fontes sintéticas + 50000 notas sintéticas. Não são 100000 cenários independentes nem páginas web consultadas. Cada par tem um termo único conhecido de antemão, um vínculo nota → fonte e conteúdo Unicode.

- materialização em ficheiros Markdown reais;
- índice SQLite/FTS5 real, com identidade única e backlinks;
- 50000 pesquisas com conjunto esperado exato e 50000 travessias em cada direção;
- fecho da ligação, eliminação do índice derivado e reconstrução a partir dos ficheiros;
- renomeação de ficheiro preservando identidade e hashes de todos os objetos;
- seis cenários adversariais distintos: adulteração, ausência, relação partida, identidade duplicada, autoridade inválida e envelope malformado; cada um verifica a causa esperada de rejeição;
- processo Python novo recupera uma relação do índice persistido sem chamadas a providers.

Medições: tempo por fase, tamanho lógico Markdown/SQLite, custo médio por objeto, hash do manifesto e do executor. Tamanho lógico não mede blocos físicos, RAM nem custo com documentos reais. O corpus temporário é descartado ao terminar; geração determinística e evidência resumida ficam versionadas.

## Limites que impedem PASS global

NOT RUN: Windows, web real, IA, qualidade factual/semântica, UI, integração no Nexus, histórico de múltiplas versões, power loss, concorrência, links entre projetos reais e Human Gate integrado. O ensaio deteta adulteração contra um manifesto conhecido; não protege contra um atacante que altera também a referência de confiança.

A reutilização prova recuperação de uma referência num processo novo; não mede melhoria editorial nem ganho de tempo com/sem contexto. Não publicar percentagens de melhoria. Ficheiros válidos e pesquisa correta não garantem conclusões corretas.

Próximo microprocesso permitido: contratar importação de um resultado real do Store para uma vista wiki derivada, com identidade/versão e proveniência F013. Só depois testar a cadeia completa resultado → fonte → novo resultado, alterações de versões e portão humano. A integração exige a autorização prevista no escopo original do laboratório.

## Fontes internas verificadas

- `DECISIONS.md`, decisão de 30/09; `AGENTS.md`.
- `nexus/docs/LAB-WIKI-KNOWLEDGE-2026-10-04.md`.
- `nexus/docs/REVISAO-CONTRATOS-WIKI.md` e `F013-PROVENIENCIA-INVERSA.md`.
- `nexus/docs/F009-OBJETOS-MARKDOWN.md`; `nexus/store.py`.
- Executor, workflow e relatório do laboratório no commit-base indicado.

Não foi feito novo ranking de ferramentas externas: o problema desta etapa era a ausência do ensaio prometido e a distinção de autoridade da informação, não escolher outro produto wiki.
