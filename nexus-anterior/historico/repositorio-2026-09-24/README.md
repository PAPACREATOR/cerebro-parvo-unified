# Cérebro Independente — funcionamento e estado do projeto

**Para retomar o trabalho:** ler primeiro [MEMORIA-DE-TRABALHO.md](MEMORIA-DE-TRABALHO.md), com decisões, cobertura da análise, pendências e estado da cópia para D:.

Data de organização documental: 2026-09-22.
Autor declarado da conceção: Pedro Alexandre Caldas Coelho.
Estado: fundação de implementação iniciada. Ainda não existe código F0 validado.

## A ideia em linguagem simples

A pessoa escreve normalmente no Logseq, pensa, investiga e decide. **Não precisa de saber o que é Markdown.** O sistema trata de ficheiros, organização e formatos nos bastidores. A internet e as ferramentas podem encontrar e propor informação, mas **nada entra no cofre final sem aprovação humana de uma versão concreta**. A IA, quando útil, é chamada pontualmente; não é o cérebro nem decide o que é verdade.

O projeto usa peças maduras para funções que elas já fazem. O código próprio, sobretudo Python, liga as fronteiras e executa as regras determinísticas específicas do Cérebro Independente. A pessoa mantém a autoridade.

## Diagrama do circuito

```text
ENTRADA DA INTERNET                         ESCRITA DA PESSOA
        │                                          │
        ▼                                          ▼
Activepieces: pesquisa/fluxos             Logseq Classic: escrita normal
        │                                  e funções nativas do grafo
        ▼                                          │
bruto → validação/proveniência → candidato ────────┤
                                                   ▼
                                        COFRE CRIATIVO LOGSEQ
                                        trabalho, ligações, revisão
                                                   │
                                        brainstorming? Só se fizer
                                        sentido para o input/pedido
                                                   │
                                             decisão humana
                                       ┌───────────┼───────────┐
                                       ▼           ▼           ▼
                                  manter aqui    apagar     aprovar
                                                              │
                                                              ▼
                                                COFRE FINAL SEPARADO
                                                Markdown interno +
                                                SQLite interno vivo
                                                              │
                                                              ▼
                                                  SQLite espelhado
                                               (contrato por fechar)
```

O bruto em validação é uma **zona de entrada**, não um terceiro cofre. Quando uma proposta entra no trabalho criativo, fica nesse cofre até decisão. “Apagar” é uma decisão da pessoa, nunca consequência automática de um hash igual. A aprovação não apaga automaticamente a versão criativa.

O **cofre final fica fechado por defeito**: não é varrido continuamente pela pesquisa nem pela IA; só responde a operações autorizadas pelo contrato a definir. É a **IA** que fica dormente até ser chamada. Isto descreve a regra pretendida, não um isolamento já testado.

## Algoritmo funcional

1. **Receber.** Uma pesquisa traz um resultado da internet, ou a pessoa começa a escrever no Logseq. O primeiro caso passa por Activepieces e pela zona de entrada; o segundo usa diretamente o cofre criativo.
2. **Verificar sem inventar conhecimento.** Para resultados externos, registar origem, identidade, versão, data observada e integridade; rejeitar entrada inválida ou deixá-la pendente com erro visível. A classificação e a pesquisa são regras de triagem, não aprovação.
3. **Trabalhar no criativo.** Apresentar o candidato em linguagem normal no Logseq. Usar blocos, páginas, ligações, tarefas e navegação que o Logseq já fornece. O utilizador não edita Markdown, YAML, SQL ou ficheiros técnicos.
4. **Escolher o ramo.** Conforme a entrada e a intenção da pessoa, pode haver brainstorming/perguntas críticas ou simplesmente leitura e organização. IA só é chamada sob pedido ou necessidade concreta permitida; recebe contexto mínimo e devolve proposta ao criativo. Sem IA, o ciclo essencial continua.
5. **Esperar pela decisão.** Enquanto não há decisão expressa ligada ao item e à versão, o conteúdo permanece no criativo. As opções são continuar a trabalhar, manter só ali, pedir apagamento ou aprovar para o final.
6. **Promover apenas após aprovação.** Python aplica as regras e uma operação idempotente, com identidade e auditoria, para colocar a versão aprovada no cofre final. O final contém Markdown tratado pelo sistema e **um SQLite interno que faz parte da memória/lógica determinística**. Uma falha entre estas escritas não pode ser ocultada: a operação tem de ser reconciliável.
7. **Espelhar depois.** Há um **segundo SQLite distinto**. Só recebe a representação autorizada pelo contrato a definir; não decide promoções nem substitui o SQLite interno. Uma falha de espelhamento fica visível e recuperável.
8. **Continuar o ciclo.** Novas pesquisas e tarefas usam os fluxos do Activepieces e informação autorizada, sem acesso irrestrito ao cofre final. O estado aprovado pode orientar novos temas, mas nunca transforma uma descoberta externa em conhecimento final por si só.

Para o núcleo: `novo_estado = F(estado, evento_observado, regras_versionadas, configuração)`. Repetir os mesmos inputs congelados deve produzir o mesmo resultado. Rede, relógio e respostas de IA não são determinísticos por natureza; os seus resultados têm de ser registados como eventos antes de entrar nesta função.

## Quem faz o quê

| Peça | Responsabilidade | Não faz |
| --- | --- | --- |
| Pessoa | Escrever, avaliar, aprovar, manter ou apagar. | Lidar com Markdown, SQL ou detalhes internos. |
| Logseq Classic/File Graph | Cofre criativo e funções nativas de escrita, blocos, relações e tarefas. | Autorizar automaticamente o cofre final. |
| Activepieces | Pesquisa e execução de workflows, horários, espera e retoma. | Ser dono da memória aprovada ou aprovar conhecimento. |
| Python mínimo | Regras próprias, eventos, validação, Gate, promoção e reconciliação. | Refazer editor, motor de workflows ou biblioteca documental. |
| Cofre final | Conhecimento aprovado em Markdown gerido pelo sistema e SQLite interno vivo. | Receber diretamente da internet, da IA ou de um workflow. |
| SQLite espelhado | Representação derivada de âmbito ainda a especificar. | Substituir o interno ou conferir autoridade de escrita. |
| Zotero | Fontes, PDFs e referências quando aplicável. | Decidir o que é conhecimento final. |
| IA opcional | Perguntas, expansão ou análise sob chamada delimitada. | Agir autonomamente ou entrar no cofre final. |

## O que é decisão e o que falta provar

**Decidido por Pedro:** dois cofres; criativo nativo do Logseq; final só após aprovação; dois SQLite (interno no final e espelhado); Activepieces para fluxos; Python para lógica própria; IA opcional; experiência sem Markdown imposto ao utilizador. Obsidian e Dynalist pertencem ao percurso histórico, não às peças atuais.

**Por fechar antes de F2:** autoridade de cada tipo de dado entre Markdown e SQLite interno; conteúdo/direção/permissões do espelho; backup e recuperação; proteção em repouso; protocolo de falha parcial na promoção; e teste de usabilidade que prove a escrita normal sem sintaxe exposta. Não presumir que o SQLite interno se reconstrói todo a partir do Markdown.

**Critério mínimo do protótipo:** com dados artificiais, um resultado da internet e uma nota humana chegam ao criativo; a via sem brainstorming funciona; a via com brainstorming só é acionada quando permitida; nenhuma delas altera o final sem aprovação; uma aprovação concreta atualiza o final uma única vez; falhas e repetição não perdem informação nem duplicam a entrada; o espelho cumpre o contrato aprovado; o núcleo continua com IA desligada. Estes testes **ainda não foram executados**.

Isto é mais simples de montar do que programar editor, pesquisa, scheduler, biblioteca de fontes e motor de IA próprios. Não é, porém, uma promessa de prazo: a dificuldade real está nas fronteiras entre as peças e na experiência sem Markdown. O caminho é testar primeiro um ciclo vertical pequeno, não instalar um ecossistema completo e declarar sucesso.

## Referências externas: comparação, não dependências

[ResearchVault](https://github.com/pjastam/ResearchVault) mostra um fluxo de fontes com decisão humana antes de um artefacto de investigação; o objetivo e a dependência de síntese por IA não são iguais aos deste projeto. [Will](https://github.com/mindot-ai/will) mostra continuidade e mecanismos de replay com LLM como componente, mas segue o **caminho de uma mente/agente autónomo**, com faculdades e ações. O Cérebro Independente segue o caminho de um **sistema humano de conhecimento**, com aprovação do cofre final e IA sem autoridade. São precedentes parciais, não componentes previstos. Ver [comparação dirigida](COMPARACAO-RESEARCHVAULT-WILL-2026-09-22.md).

## Retomar a implementação

1. Ler `CEREBRO_CONSTITUTION.md`.
2. Ler `CEREBRO_ARCHITECTURE.md` e `IMPLEMENTATION_PLAN.md`.
3. Consultar `STATUS.md` e `DECISIONS.md`.
4. Executar apenas a SPEC indicada em `STATUS.md`.
5. Rever alterações e testes antes de autorizar a próxima SPEC.

As regras antigas do Cline permanecem arquivadas em `.clinerules/`, mas Cline está inativo. Para Cursor, `AGENTS.md` comunica regras e `.cursorignore` exclui acervo, dossier jurídico e memória do contexto normal; esta exclusão não bloqueia leituras por terminal/MCP. Manter aprovações manuais.

Consultar também `INSTALLATION_PLAN.md` e `TEAM_WORKFLOW.md`. A instalação é faseada e cada tarefa termina com teste e revisão antes da seguinte.

Pesquisa atual dos planos gratuitos, chave Gemini, Copilot e coordenação: `FERRAMENTAS-GRATUITAS-E-EQUIPA.md`. A documentação define uma linha de base; o produto ainda não foi implementado ou testado.

Divisão de tarefas e portas de passagem **até F4 técnica (IA efémera)**: `PLANO-DE-TAREFAS-POR-FASE.md`. Uso restrito da API Google: `PROTOCOLO-GEMINI-CONTEXTO-MINIMO.md` (proposta ainda sem chamada real). A comparação com o Plano Mestre corrigido e a numeração funcional antiga está em `AUDITORIA-DOCUMENTAL-P4.md`.

**Auditoria em curso por ações e horas:** `REGISTO-DE-EVENTOS-E-ACOES.md` distingue ações observadas, correções e horas históricas desconhecidas. `VALIDACAO-CONCEPTUAL-E-MITIGACAO.md` liga lacunas a testes. `COMPARACAO-WILL-E-PROBABILIDADES.md` separa precedente técnico e modelo matemático de probabilidades, sem transformar semelhança em garantia. Estes relatórios são internos e não autorizam publicação.

**Decisão atual após a correção mais recente de Pedro:** dois cofres separados. A pessoa escreve normalmente no cofre criativo nativo do Logseq Classic/File Graph, sem input Markdown técnico. O final só recebe versões expressamente aprovadas e contém Markdown gerido pelo sistema **e um SQLite interno vivo**. Há **um segundo SQLite espelhado**, distinto. Activepieces executa fluxos. Ler `ARQUITETURA-CORRIGIDA-2026-09-22.md` e `COMPARACAO-RESEARCHVAULT-WILL-2026-09-22.md`; o mapa de versões e a auditoria Lego preservam interpretações intermédias, não substituem esta correção.

## Ler por esta ordem

**Documento consolidado mais recente:** `documentacao/2026-09-22/08-MEMORIA-DESCRITIVA-DO-PROJETO.md` — conceção, evolução, inspiração, escolhas e funcionamento, com data de 22 de setembro de 2026 e autoria declarada de Pedro Alexandre Caldas Coelho.

**Auditoria do código histórico:** `documentacao/2026-09-22/09-AUDITORIA-FUNCIONAL-ACERVO.md` — comportamentos observados, conflitos com as regras atuais e cobertura ainda pendente.

**Capacidades e plugins:** `documentacao/2026-09-22/11-CAPACIDADES-E-PLUGINS-CANDIDATOS.md` — necessidade humana, blocos existentes, referências oficiais e condições de adoção.

**Valor documental:** `juridico/2026-09-22/04-VALOR-DO-DOSSIER.md` — o que o dossier sustenta e o que não certifica.

1. `documentacao/2026-09-22/01-AUTORIA-E-PROVENIENCIA.md`
2. `documentacao/2026-09-22/02-CRONOLOGIA-E-DECISOES.md`
3. `documentacao/2026-09-22/03-FUNCIONAMENTO.md`
4. `documentacao/2026-09-22/04-FASES-E-ACEITACAO.md`
5. `documentacao/2026-09-22/05-ARQUITETURA-ANTERIOR.md` — proposta anterior, subordinada às correções posteriores.
6. `documentacao/2026-09-22/06-PESQUISA-HISTORICA-CHATGPT.md` — fontes encontradas nos chats, cronologia e novos anexos deduplicados.
7. `documentacao/2026-09-22/07-PERCURSO-INTELECTUAL-DO-AUTOR.md` — estudo das ferramentas de conhecimento, escolha do Logseq e retirada da IA do núcleo em favor de regras determinísticas.

Os documentos fornecidos pela pessoa são preservados em `fontes/recebidas-2026-09-22/`. O manifesto nessa pasta regista os hashes SHA-256 das cópias e dos originais. A data da pasta é a data deste arquivo, não uma afirmação sobre quando a ideia foi criada.

## Dossier para apresentação e confidencialidade

- `juridico/2026-09-22/01-DECLARACAO-DE-AUTORIA.md`: declaração para revisão e assinatura por Pedro Alexandre Caldas Coelho.
- `juridico/2026-09-22/02-NDA.md`: minuta de acordo de confidencialidade com destinatário por preencher.
- `juridico/2026-09-22/03-APRESENTACAO-E-REGISTOS.md`: folha de apresentação, vias oficiais e campos ainda necessários.

As minutas não estão assinadas e não constituem registo oficial ou parecer jurídico. Foram preparadas com Portugal como enquadramento proposto; utilização internacional exige adaptação.

Regras documentais: alterações futuras devem indicar data, origem da decisão e estado de aprovação. Uma proposta técnica do assistente não substitui uma decisão da pessoa. Datas históricas desconhecidas ficam expressamente desconhecidas. Nenhuma licença de publicação do projeto é concedida por este documento.
