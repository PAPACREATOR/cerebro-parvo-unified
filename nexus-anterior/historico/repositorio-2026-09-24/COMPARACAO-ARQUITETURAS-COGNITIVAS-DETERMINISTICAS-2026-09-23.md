# Comparação profunda — arquiteturas cognitivas determinísticas e Cérebro Independente

Data: 2026-09-23  
Estado: **referência técnica/comparativa; não altera a arquitetura, não autoriza dependências nem implementação.**

## Pergunta

Que partes do Cérebro Independente já existem na investigação/engenharia, o que é diferente, e onde pode existir originalidade na combinação?

A comparação foi feita com fontes primárias ou académicas sobre **Soar, ACT-R, CLARION, LIDA, ActiveGraph/event sourcing, ESAA, OpenViking/VikingMem** e projetos modernos de memória determinística. A pesquisa não é uma busca de anterioridade jurídica/patentes e **não prova novidade legal**.

## Anatomia atual do Cérebro Independente

Não reduzir o sistema a uma metáfora de “IA com memória”. O desenho vigente tem camadas com autoridades diferentes:

1. **Working Memory** — estado temporário do ciclo atual.
2. **Behavioral Memory** — regras/preferências confirmadas, versionadas e auditáveis.
3. **Memória/conhecimento criativo** — Logseq Classic/File Graph: escrita, relações, rascunhos, hipóteses e conhecimento em evolução.
4. **Conhecimento final aprovado** — cofre separado; Markdown gerido + SQLite interno vivo; só entra uma versão concreta por decisão humana.
5. **SQLite espelhado** — segunda base, sob contrato ainda por fechar; não é automaticamente outra memória nem outra autoridade.
6. **EventLog/snapshots** — história causal/replay do núcleo; não confundir com conhecimento canónico.
7. **RAW/Candidate** — quarentena de entrada, não é cofre nem verdade.
8. **IA efémera** — ferramenta; não é memória soberana nem decisor final.

Portanto, a frase “três memórias, uma canónica” é útil como **modelo funcional simplificado** se se quiser agrupar:
- memória de trabalho/operacional;
- memória comportamental/procedimental;
- memória de conhecimento persistente, cujo subconjunto aprovado é canónico.

Mas a implementação documental atual é mais precisa que essa simplificação: criativo e final são dois cofres distintos, e EventLog/SQLite têm funções próprias.

A ideia de “lado esquerdo/lado direito” também pode ser uma metáfora útil:
- lado **determinístico/analítico**: eventos, regras, estado, validação, replay;
- lado **criativo/associativo**: Logseq, brainstorming e IA pontual.

**Não afirmar equivalência neurocientífica com hemisférios humanos.** Tecnicamente são dois regimes de processamento com uma fronteira controlada, não uma simulação anatómica do cérebro.

---

## 1. Soar — o precedente mais próximo nas memórias clássicas

Soar já separa várias formas de memória:
- working memory;
- production/procedural memory;
- semantic memory;
- episodic memory;
- preference memory no processo de decisão.

O ciclo é estruturado: input → proposal/elaboration → decision → application/output. Regras de produção interpretam o estado e propõem operadores; um procedimento de decisão escolhe.

### Igual ao nosso desenho

- estado corrente separado de memória persistente;
- regras/procedimentos separados dos factos;
- ciclo de decisão explícito;
- comportamento complexo sem LLM;
- memória episódica/histórica separada de conhecimento semântico;
- possibilidade de resolver “impasses” apenas quando o conhecimento corrente não chega.

### Diferente

- Soar pretende ser uma arquitetura cognitiva geral e autónoma;
- a arquitetura não tem como princípio central os **dois cofres humano-criativo → humano-aprovado-final**;
- não usa a nossa fronteira de promoção item+versão/hash+decisão humana;
- não tem Activepieces/Logseq/Zotero como peças LEGO externas;
- o nosso EventLog/replay é um contrato de engenharia e auditoria, não simplesmente memória episódica cognitiva.

### Lição

Não reinventar conceitos de working/procedural/semantic/episodic memory. Estudar especialmente os mecanismos de seleção, impasse e recuperação. A diferença do nosso sistema deve estar nos contratos, autoridade, integração e verificabilidade.

Fontes:
- https://soar.eecs.umich.edu/soar_manual/02_TheSoarArchitecture/
- https://soar.eecs.umich.edu/soar_manual/07_EpisodicMemory/

---

## 2. ACT-R — regras + memória declarativa + buffers

ACT-R separa essencialmente:
- **declarative memory**: chunks/factos;
- **procedural memory**: production rules;
- **buffers**: pequena superfície de contexto/working state;
- módulos especializados.

O comportamento emerge de ciclos de matching de regras contra o estado dos buffers.

### Igual

- regras não precisam de IA generativa;
- memória ativa pequena;
- conhecimento persistente separado das regras;
- decisões podem ser extremamente baratas computacionalmente;
- decomposição modular.

### Diferente

- ACT-R foi concebido principalmente como teoria/modelo computacional da cognição humana;
- inclui mecanismos subsimbólicos de ativação/utility e temporização psicológica;
- não tem o nosso conceito de conhecimento final sujeito a aprovação humana;
- não resolve a nossa proveniência web, promoção entre cofres, outbox, replay de efeitos externos ou integração local-first.

### Lição

A nossa decisão “determinístico primeiro; IA só quando regras não bastam” tem precedentes fortes. Isso reduz a alegação de novidade dessa ideia isolada, mas também a torna tecnicamente defensável.

Fontes:
- https://link.springer.com/chapter/10.1007/978-3-030-31846-8_2
- https://acs.ist.psu.edu/projects/act-r-faq/act-r-faq.html

---

## 3. CLARION — a comparação mais interessante para os “dois lados”

CLARION usa uma estrutura **dual**:
- nível explícito/simbólico;
- nível implícito/distribuído;
e separa subsistemas de ação, raciocínio/memória, motivação e metacognição.

### Semelhança conceptual

Há uma semelhança abstrata com dois regimes:
- processamento explícito, controlado e verificável;
- processamento associativo/não totalmente explícito.

Isso lembra a nossa separação entre núcleo determinístico e criatividade/IA.

### Diferença essencial

No CLARION, os dois níveis fazem parte da própria arquitetura cognitiva e aprendem/interagem internamente. No nosso desenho:
- IA pode desaparecer e o núcleo continua;
- criatividade não ganha autoridade por produzir uma conclusão;
- passagem para conhecimento final exige uma **decisão humana externa ao mecanismo cognitivo**;
- o sistema não tenta modelar processos inconscientes humanos.

Logo, “lado esquerdo/lado direito” não é novidade por si só; arquiteturas dual-process/dual-representation existem há décadas. A nossa fronteira de autoridade é outra coisa.

Fontes:
- https://academic.oup.com/edited-volume/34641/chapter-abstract/295173431
- https://sites.google.com/site/clarioncognitivearchitecture

---

## 4. LIDA — muitas memórias e ciclos cognitivos

LIDA combina memória perceptual, episódica, declarativa e procedural com ciclos de atenção/seleção de ação inspirados em Global Workspace Theory.

### Igual

- várias memórias especializadas;
- seleção de informação para impedir sobrecarga;
- ciclos repetidos;
- memória + atenção + ação como funções distintas.

### Diferente

O Cérebro Independente não procura reproduzir consciência/global workspace. A atenção pode ser uma seleção determinística de temas/contexto, e a autoridade final continua humana.

Fonte académica:
- https://pmc.ncbi.nlm.nih.gov/articles/PMC9506380/

---

## 5. Event sourcing moderno — aqui também há precedentes fortes

Em 2026 surgiram propostas que colocam o **log/eventos** no centro em vez do LLM.

### ActiveGraph — “The Log is the Agent”

Propõe:
- append-only event log como fonte de verdade operacional;
- working graph como projeção determinística;
- comportamentos reagem e emitem eventos;
- replay determinístico;
- lineage e fork.

Isto é muito próximo do nosso F0 em **mecanismo**, embora não em toda a arquitetura.

Fonte:
- https://arxiv.org/abs/2605.21997

### ESAA

Separa intenção probabilística de mutação determinística:
- agentes emitem intenções estruturadas;
- orquestrador determinístico valida/persiste/aplica;
- event log append-only;
- replay/hashing/auditoria.

Isto confirma que “LLM propõe, núcleo determinístico decide/aplica” não é isoladamente novo.

Fonte:
- https://arxiv.org/abs/2602.23193

### RationaleVault / deterministic-memory-layer

Projetos atuais também usam SQLite/local-first, eventos imutáveis, projeções determinísticas, snapshots, replay e proveniência.

Isto é importante precisamente para não alegarmos originalidade onde já há precedente.

Referências:
- https://github.com/NeutronZero/RationaleVault
- https://github.com/daveremy/deterministic-memory-layer

---

## 6. OpenViking/VikingMem — contexto e memória de agentes

Já existe relatório próprio no repositório. A semelhança relevante é organização/retrieval progressivo e gestão estruturada de memória/contexto.

A diferença crítica permanece: no nosso sistema, recuperação ou consolidação automática **não equivale a verdade canónica**.

Ver:
- `REFERENCIA-OPENVIKING-VIKINGMEM-2026-09-23.md`

---

## 7. Human-in-the-loop — não é novo; a posição do humano é que importa

Human-in-the-loop é um padrão conhecido. Portanto, “há aprovação humana” isoladamente **não é uma inovação**.

O ponto arquitetural mais específico do Cérebro Independente é a combinação de contratos:

`externo/IA → RAW/Candidate → espaço criativo → item+versão → decisão humana explícita → promoção determinística → cofre final`

e simultaneamente:

- IA não é autoridade;
- automação não é autoridade;
- classificação não é aprovação;
- pesquisa não é aprovação;
- fim de workflow não é aprovação;
- repetição da mesma decisão deve ser idempotente;
- falha parcial não pode transformar candidato em conhecimento final;
- o original é preservado;
- conhecimento final tem proveniência e história auditável.

É uma diferença **de autoridade e fronteiras**, não apenas “um humano carrega num botão”.

---

## 8. Onde NÃO está a novidade

Não reivindicar como novo, isoladamente:

- memória de trabalho;
- memória procedural/comportamental;
- memória semântica;
- memória episódica;
- sistemas de regras;
- arquiteturas de dois processos;
- event sourcing;
- append-only log;
- deterministic replay;
- snapshots;
- SQLite;
- local-first;
- human-in-the-loop;
- RAG/retrieval hierárquico;
- IA efémera;
- LLM como componente periférico;
- separação entre execução determinística e geração probabilística.

Há precedentes claros para todos.

---

## 9. Onde a combinação é mais distintiva

A pesquisa feita até agora **não encontrou um sistema idêntico** que reúna simultaneamente:

1. superfície criativa humana nativa em Logseq/File Graph;
2. cofre final fisicamente/lógicamente separado;
3. promoção para o final apenas de item+versão concretos aprovados pelo humano;
4. núcleo Python determinístico independente de LLM;
5. EventLog + replay + snapshots para estado semântico;
6. memória comportamental versionada;
7. SQLite interno no cofre final com papel vivo na lógica/memória;
8. segundo SQLite espelhado sob contrato independente;
9. automação externa Activepieces sem autoridade sobre a verdade;
10. pesquisa contínua que produz candidatos, nunca factos automaticamente;
11. IA dormente/efémera, sem autoridade e substituível;
12. ferramentas maduras usadas como peças LEGO em vez de reconstruídas;
13. conteúdo criativo e conhecimento canónico tratados como classes de autoridade diferentes;
14. aprovação humana como **barreira de commit epistemológico**, não mera supervisão de ações.

Isto **não prova inovação científica ou novidade de patente**. Prova apenas que, nas fontes comparadas até esta data, a combinação exata e a distribuição de autoridade não apareceu como uma arquitetura equivalente.

---

## 10. A característica mais interessante: três eixos independentes

A arquitetura torna-se mais clara se não misturarmos três coisas:

### Eixo A — tipo de memória
- Working;
- Behavioral/procedural;
- conhecimento persistente.

### Eixo B — maturidade/autoridade do conhecimento
- RAW;
- Candidate/creative;
- Approved/canonical.

### Eixo C — modo de processamento
- determinístico;
- criativo/associativo/IA;
- decisão humana.

Isto é mais específico do que simplesmente copiar a taxonomia humana “working/episodic/semantic”.

Um conteúdo pode, por exemplo, ser:
- persistente;
- criativo/candidato;
- produzido associativamente;
- **não canónico**.

Outro pode ser:
- persistente;
- aprovado;
- promovido deterministicamente;
- **canónico**.

Essa ortogonalidade é arquiteturalmente importante.

---

## 11. Hipótese de “hemisférios” — formulação tecnicamente segura

Se Pedro quiser conservar a metáfora:

**Hemisfério determinístico**
- regras;
- eventos;
- identidade;
- estado;
- validação;
- cálculo;
- replay;
- segurança;
- promoção mecânica.

**Hemisfério criativo**
- associação;
- exploração;
- escrita;
- hipóteses;
- relações;
- brainstorming;
- IA quando chamada.

**Corpo caloso funcional**
- contratos/eventos/candidatos.

**Córtex executivo externo**
- humano decide o que atravessa a fronteira para conhecimento aprovado.

É apenas uma metáfora de design. Não apresentar como modelo neurocientífico.

---

## 12. Teste de originalidade útil para futuras fases

Para cada mecanismo futuro perguntar:

1. Já existe em Soar/ACT-R/LIDA/CLARION?
2. Já existe num runtime event-sourced moderno?
3. Já existe em OpenViking/VikingMem ou sistema de memória equivalente?
4. Já existe nativamente em Logseq/SQLite/Activepieces/Zotero?
5. Se existe, podemos reutilizar/adaptar?
6. Se não existe, qual é exatamente a diferença verificável?
7. Essa diferença é necessária ao objetivo de Pedro ou apenas complexidade?

Regra:

`novidade arquitetural útil ≠ quantidade de código novo`

Uma arquitetura pode ser original na **composição, fronteiras e contratos**, mesmo usando componentes conhecidos. Mas qualquer alegação formal de invenção/propriedade intelectual requer pesquisa de anterioridade própria.

---

## Conclusão provisória

O Cérebro Independente **não inventa as peças fundamentais da cognição computacional**. Isso é positivo: working memory, regras, memória persistente, ciclos cognitivos, event sourcing e human-in-the-loop têm décadas de investigação e engenharia.

O elemento mais diferenciador observado é a **composição das fronteiras de autoridade**:

`determinístico ↔ criativo ↔ humano`

cruzada com:

`working ↔ behavioral ↔ persistent knowledge`

e com:

`RAW ↔ CANDIDATE/CREATIVE ↔ APPROVED/CANONICAL`.

O humano não é apenas supervisor de execução: é a autoridade que transforma uma versão candidata em conhecimento canónico. O lado criativo pode explorar sem contaminar automaticamente o lado aprovado. O núcleo pode continuar sem IA. A história operacional pode ser reproduzida sem confundir EventLog com verdade epistemológica.

**Classificação para o projeto:** referência comparativa forte; nenhuma nova dependência; nenhuma alteração de arquitetura; usar para evitar reinvenção durante futuras SPECs.
