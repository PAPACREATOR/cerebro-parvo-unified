# Laboratório de conhecimento e wikis — 04-10-2026

## Autoridade e objetivo

Pedro Coelho é o decisor final do projeto. Esta nota orienta a equipa e os agentes que trabalham neste laboratório.

Objetivo: provar, em espaço isolado, se o molde Markdown consegue organizar textos e conhecimento em wikis leves, pesquisáveis e relacionadas, e se essa organização pode ser reutilizada por processos posteriores.

Esta é uma experiência de prova. Não altera a arquitetura oficial nem decide o executor do Nexus.

## Isolamento obrigatório

- Branch exclusiva: `lab-wiki-knowledge-20261004`.
- Base: `lab-bootstrap-20261004`.
- Dados apenas sintéticos.
- Nenhuma alteração em `main`.
- Nenhuma alteração em `pc-full-mirror-20261004`.
- Nenhuma alteração em `pc-snapshot-tooling-20261004`.
- Nenhuma alteração em `work/audit-bidirectional-20261004`.
- Nenhuma alteração em `lab-spiff-conductor-20261004`.
- Não substituir, mover ou editar código do núcleo.
- Não instalar ferramentas externas no runtime oficial.
- Não usar dados pessoais, cofres, credenciais ou conteúdos reais.
- Não abrir pull request para integração sem autorização expressa de Pedro.

## Pergunta a provar

O molde consegue transformar textos e conhecimento em objetos Markdown ligados, indexáveis e recuperáveis, mantendo identidade, versões, relações e proveniência?

Depois: o conhecimento recuperado melhora ou reduz trabalho num processo sintético relacionado?

## Fora do âmbito

- IA ou modelo local.
- Tiny/OpenBook.
- Spiff e Conductor reais.
- Windows real.
- Publicação externa.
- Google Drive, Microsoft ou redes sociais.
- Imagens, vídeo e áudio reais.
- Alteração do Kernel, Store, flows oficiais ou UI oficial.

## Experiência prevista

1. Preparar textos e fontes sintéticos.
2. Representá-los com o molde Markdown existente.
3. Derivar relações, versões e estados.
4. Construir uma wiki/índice apenas no laboratório.
5. Pesquisar nos dois sentidos.
6. Fechar e reabrir o laboratório.
7. Reconstruir o índice a partir dos objetos.
8. Executar processo sintético sem conhecimento anterior.
9. Executar processo sintético com conhecimento recuperado.
10. Comparar resultados, tempo, repetição e proveniência.

## Critérios de PASS

- Todos os objetos de teste conservam identidade estável.
- Nenhum conteúdo autoritativo é duplicado ou perdido.
- Relações diretas e inversas são recuperáveis.
- Versões antigas continuam legíveis.
- Alterações e links partidos são detetados.
- O índice pode ser apagado e reconstruído.
- A pesquisa devolve referências verificáveis, não autoridade.
- O processo com contexto recuperado usa apenas objetos válidos.
- A proveniência regressa ao texto/fonte original.
- O resultado novo fica ligado ao conhecimento anterior.
- Nenhuma alteração ocorre fora desta branch/laboratório.

## Critérios de FAIL

- O índice é tratado como fonte de verdade.
- Um objeto muda de identidade ao ser renomeado.
- Uma relação inválida é aceita como válida.
- Uma versão substitui silenciosamente outra.
- Uma fonte perdida continua apresentada como válida.
- A pesquisa promove um resultado sem validação.
- O processo não consegue regressar à origem.
- A reconstrução altera os objetos autoritativos.
- O teste precisa de tocar no núcleo ou em outra branch.

## Evidência obrigatória

Cada execução deve registar:

- branch e commit-base;
- dados usados;
- número de objetos e relações;
- consulta realizada;
- resultado esperado e observado;
- hashes;
- PASS/FAIL/NOT RUN;
- erros e limitações;
- próximo passo.

## Regra de conclusão

Esta experiência não declara que o produto final está pronto. Apenas prova ou refuta a organização do conhecimento por Markdown, wiki e índice. Qualquer integração posterior exige revisão separada e autorização explícita de Pedro Coelho.
