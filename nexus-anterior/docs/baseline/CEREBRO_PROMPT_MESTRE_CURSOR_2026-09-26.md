# CÉREBRO — PROMPT MESTRE PARA CURSOR

**Versão documental:** 2026-09-26 — fecho para implementação
**Autor da conceção:** Pedro Alexandre Caldas Coelho
**Estado:** arquitetura conceptual congelada; próxima fase = implementação e falsificação por testes.

> ESTE FICHEIRO É A ESPECIFICAÇÃO DE TRABALHO DO CURSOR. Não é um convite a redesenhar o sistema. O agente deve auditar e encontrar erros, mas qualquer alteração de arquitetura, autoridade, significado, invariantes ou requisito é apenas PROPOSTA até decisão humana explícita.

## 0. ORDEM OBRIGATÓRIA DE TRABALHO

A documentação e a implementação seguem esta ordem, sem saltos:

1. README / contrato do sistema.
2. Diagrama global.
3. Algoritmo global.
4. Biografia / identidade operacional do sistema.
5. Stack técnica.
6. Microprocessos IMP-001–IMP-026.
7. Para cada IMP: dados → pré-condições → lógica → regras → saída → falhas → recuperação → testes.
8. Implementar UM IMP.
9. Executar testes reais desse IMP.
10. Só com PASS verificável avançar.
11. Agrupar IMP aprovados em blocos funcionais.
12. Testar cada bloco e regressão dos IMP constituintes.
13. Integrar blocos progressivamente.
14. Testar IA isoladamente e adversarialmente.
15. Testar crashes, replay, recuperação, corrupção, retries e idempotência.
16. Testar ponta-a-ponta.
17. Executar auditoria final de conformidade M1–M14 + invariantes + autoridade humana.

**FAIL, NOT RUN e resultado ambíguo nunca significam PASS.**

## 0.1. BIOGRAFIA / IDENTIDADE OPERACIONAL

O Cérebro nasce como um sistema local-first de conhecimento, trabalho e resolução de problemas para uma pessoa não técnica. A pessoa conversa numa Folha Única; a complexidade interna fica escondida. O sistema não pretende substituir a pessoa, decidir a sua verdade ou transformar inferências de IA em decisões. A sua função é preservar, relacionar, recuperar, comparar, propor, executar trabalho permitido, aprender com resultados verificáveis e manter genealogia.

A sua personalidade operacional é deliberadamente assimétrica: **autonomia técnica alta; autonomia normativa baixa**. Pode procurar uma solução técnica, recuperar de falhas, selecionar uma capacidade previamente autorizada e propor relações/hipóteses. Não pode criar finalidades humanas, aprovar a própria proposta, apagar história por conveniência, ou elevar uma saída probabilística a conhecimento canónico.

Canonical é o conhecimento atualmente consolidado/aprovado pela pessoa com a evidência disponível; não é “verdade absoluta”. Creative é o espaço persistente onde hipóteses, alternativas, erros, rejeições, contradições e material em evolução podem existir sem contaminar Canonical.

## 0.2. STACK DE IMPLEMENTAÇÃO — FRONTEIRAS, NÃO SOBERANIA

A arquitetura é independente de fornecedor. A implementação corrente deve privilegiar simplicidade e substituibilidade:

- Python-first para o Core determinístico, contratos, testes, integração local e ferramentas quando adequado.
- SQLite para estado estruturado, eventos/recibos/metadados e FTS5 quando aplicável; índices/caches continuam reconstruíveis.
- Markdown/ficheiros abertos para conteúdo humano persistente conforme os contratos; o utilizador não precisa editar Markdown.
- Folha Única como única superfície humana obrigatória.
- Activepieces como oficina/orquestração operacional externa ao núcleo epistemológico: Flows/Pieces executam capacidades; não ganham autoridade sobre Canonical.
- IA isolada e opcional por capacidade, com contexto mínimo, permissões delimitadas e saída tratada como não confiável/proposta até validação.
- Web, importadores, conversores, LanguageTool, LibreOffice/PDF e outras ferramentas entram como adaptadores/capacidades substituíveis, nunca como autoridade.
- Sem RAG/vector DB/embeddings como requisito arquitetónico. FTS5, comparação determinística, fuzzy, relações e ranking podem resolver recuperação; IA semântica é chamada apenas quando justificada.

Não introduzir uma tecnologia nova porque “é mais moderna”. Primeiro provar que resolve uma necessidade contratual que a stack atual não resolve.

## 0.3. DOIS CÉREBROS / DOIS DOMÍNIOS DE AUTORIDADE

A expressão “dois cérebros” descreve a separação funcional que não pode ser colapsada:

- lado exploratório/adaptativo: interpreta, compara, relaciona, pesquisa, cria hipóteses, propõe e executa trabalho permitido;
- lado determinístico/constitucional: identidade, regras, autoridade, eventos, integridade, proveniência, genealogia, estados, portões e materialização.

Uma mesma implementação física pode conter ambos, mas **a fronteira de autoridade tem de ser testável**. Um resultado probabilístico não pode atravessar sozinho para uma mutação normativa.

## 0.4. TRÊS MEMÓRIAS

1. **Working Memory** — contexto pequeno e transitório necessário ao ciclo/tarefa atual.
2. **Behavioral / Procedural Memory** — regras, preferências, rotinas, correções e experiência de execução confirmada; versionável e auditável.
3. **Persistent Knowledge Memory** — conhecimento duradouro, cuja maturidade se divide entre Creative e Canonical.

Instrução humana explícita atual prevalece sobre comportamento aprendido.

## 0.5. TRÊS COMPARADORES

- **Determinístico/matemático:** invariantes, hashes, estados, valores, datas, versões, limites, causalidade, idempotência.
- **Semântico:** significado, possível equivalência, incompatibilidade, contexto e contradições candidatas. Resultado semântico = evidência/proposta.
- **Relacional:** documentos, blocos, conceitos, fontes, backlinks, vizinhanças, caminhos, dependências e relações temporais.

Podem cruzar resultados; concordância dos três não promove automaticamente conhecimento.

## 0.6. MATRIZ OBRIGATÓRIA DE TESTES

Cada IMP e cada bloco deve ter, quando aplicável:

- happy path;
- entrada vazia/nula/incompleta;
- limite mínimo/máximo;
- formato inválido/corrompido;
- IDs errados, trocados, repetidos e colisão simulada;
- retry e duplicação;
- execução concorrente quando houver risco;
- crash antes, durante e depois de cada efeito persistente;
- disco cheio/permissão negada/ficheiro desaparecido;
- resultado tardio/fora de ordem;
- estado sem recibo e recibo sem estado;
- corrupção de cache/FTS e reconstrução;
- tentativa de escrita proibida em Creative/Canonical;
- tentativa de contornar Human Gate;
- tentativa de plugin/IA/adaptador se autoaprovar;
- tentativa de transformar similaridade em duplicação;
- tentativa de apagar por hash igual sem autorização;
- replay sem Web/IA/adaptador;
- preservação byte-a-byte do original;
- genealogia e proveniência completas;
- regressão de todos os IMP já aprovados.

### Testes específicos da IA

A IA deve ser testada como componente potencialmente não determinístico e não confiável:

1. alucinação factual;
2. instrução ambígua;
3. prompt injection vindo de documento/Web;
4. tentativa de pedir mais permissões;
5. tentativa de escrever/promover diretamente;
6. saída com schema inválido;
7. saída parcialmente correta;
8. contradição com Canonical;
9. contradição consigo própria em duas execuções;
10. contexto insuficiente;
11. contexto excessivo ou irrelevante;
12. timeout/modelo indisponível;
13. resposta maliciosa ou conteúdo que tenta comandar o sistema;
14. mesma entrada com respostas diferentes;
15. evidência inexistente/inventada;
16. replay: provar que não é chamada novamente para reconstruir um efeito autoritativo já registado.

**Critério:** falhar um teste de autoridade é bloqueante, mesmo que a qualidade linguística seja excelente.

## 0.7. TESTES DE BLOCOS

Depois dos IMP unitários, formar blocos apenas com IMP PASS:

- **B1 Ingestão segura:** IMP-001–007.
- **B2 Interpretação/adaptação:** IMP-008–015.
- **B3 Persistência Creative e auditoria:** IMP-016–020.
- **B4 Apresentação/falha/recuperação:** IMP-021–023.
- **B5 Eliminação protegida:** IMP-024–026.

Cada bloco deve provar propriedades emergentes, não apenas repetir testes unitários. Ex.: B1 prova que um ficheiro externo pode atravessar receção→hash→duplicação sem alterar original ou Canonical; B3 prova replay/materialização e reconstrução de derivados; B5 prova que nada é eliminado sem autorização humana específica e atual.

## 0.8. TESTES PONTA-A-PONTA MÍNIMOS

E2E-01 Importação normal → Creative → apresentação.
E2E-02 Mesmo ficheiro novamente → detetar duplicação exata sem apagar.
E2E-03 Paráfrase/conteúdo semelhante → não tratar como duplicado exato.
E2E-04 Resultado incerto → REVIEW → apresentar sem criar Creative automaticamente.
E2E-05 Adaptador falha → FAILED/RETRYABLE correto, nunca “Importado”.
E2E-06 Crash em materialização → reconciliação demonstrável.
E2E-07 Apagar FTS/cache → reconstruir sem perda autoritativa.
E2E-08 IA propõe alteração contraditória → preservar proposta/contradição; Canonical não muda.
E2E-09 Pedido de promoção → Human Gate → aprovação/rejeição → genealogia preservada.
E2E-10 Pedido de eliminação → alvo exato → autorização → eliminação só desse original → auditoria preservada.
E2E-11 Reinício da aplicação em cada estado relevante → nenhum salto silencioso de estado.
E2E-12 Replay autoritativo → mesmo estado materializado sem chamar Web/IA/adaptadores.
E2E-13 Documento malicioso com prompt injection → tratado como conteúdo, não como instrução de sistema.
E2E-14 Mover/renomear ficheiro → IDs e relações permanecem válidos.
E2E-15 Contradições coexistentes → nenhuma é apagada; Canonical atual e genealogia continuam identificáveis.

## 0.9. DEFINITION OF DONE

Um IMP/bloco/release só está DONE quando:

- código existe;
- testes especificados foram realmente executados;
- evidência de execução está guardada;
- regressão relevante passa;
- nenhuma invariante foi enfraquecida;
- nenhum `POR DEFINIR` necessário foi improvisado;
- estado final é PASS explícito.

O Cursor deve manter uma tabela de conformidade: `requisito → módulo → IMP/bloco → teste → evidência → estado`.

---

# PARTE I — BASELINE AUTORITATIVA RECUPERADA

A secção seguinte é preservada integralmente como fonte normativa recuperada da Biblioteca.

# CÉREBRO --- README DE REFERÊNCIA E BASELINE DE IMPLEMENTAÇÃO

**Baseline:** 26-09-2026\
**Autor da conceção:** Pedro Alexandre Caldas Coelho\
**Estado:** arquitetura conceptual fechada; implementação e validação
experimental por microprocessos.\
**Regra de precedência:** decisões humanas posteriores prevalecem sobre
versões anteriores, sem apagar a genealogia.

------------------------------------------------------------------------

## 1. O que é o sistema

O Cérebro é um sistema local de conhecimento, trabalho e resolução de
problemas em que **a pessoa é a autoridade máxima**.

A superfície humana é a **Folha Única**: a pessoa escreve normalmente,
como numa conversa. Markdown, IDs, paths, SQLite, EventLog e restantes
mecanismos técnicos são infraestrutura interna e não são exigidos ao
utilizador.

O sistema não depende conceptualmente de uma aplicação concreta de
notas, de um modelo de IA específico, de Activepieces, n8n, dois SQLite,
um grafo externo ou uma cloud. Essas escolhas podem existir na
genealogia ou ser testadas como implementações/adaptadores, mas não
definem a arquitetura.

A arquitetura é fechada, mas o comportamento não é rígido. O sistema
deve conseguir observar, recuperar contexto, reconhecer padrões,
comparar, medir incerteza, formar hipóteses, detetar contradições,
tentar soluções permitidas, observar resultados, corrigir-se e
reutilizar aprendizagem --- sempre dentro das invariantes e da
autoridade humana.

**Regra curta:** regras fixas para autoridade, integridade e segurança;
mecanismos adaptativos para resolução de problemas.

------------------------------------------------------------------------

## 2. Princípios constitucionais

1.  A pessoa é a autoridade final.
2.  Uma proposta da máquina não se transforma silenciosamente numa
    decisão humana.
3.  Creative e Canonical são classes de autoridade distintas.
4.  Canonical significa versão atualmente consolidada/aprovada pela
    pessoa; não significa verdade universal.
5.  Creative preserva hipóteses, alternativas, erros, contradições,
    rejeições, fontes, versões e genealogia.
6.  Promoção para Canonical exige o portão humano definido para essa
    operação.
7.  Adaptadores, importadores, Web, plugins e IA não escrevem
    diretamente em Canonical.
8.  Resultados externos são não confiáveis até passarem pelo processo
    aplicável.
9.  Originais são preservados. Similaridade, paráfrase, mesmo
    significado ou contradição nunca autorizam eliminação automática.
10. Mesmo hash/duplicação exata pode permitir reconhecer identidade
    técnica, mas **não autoriza por si só apagar um original**.
11. Efeitos autoritativos são representados por eventos autoritativos e
    devem poder ser auditados.
12. Replay de eventos autoritativos deve ser determinístico quando o
    contrato assim o exige.
13. Informação não determinística necessária ao replay é congelada como
    evidência/evento; replay não volta a pedir à Web/IA que produza a
    mesma resposta.
14. Falha não pode ser registada como sucesso.
15. Uma operação crítica termina em estado demonstrável: `COMMITTED`,
    `NOT_COMMITTED` ou `RECOVERY_REQUIRED`.
16. `RECOVERY_REQUIRED` bloqueia continuação incompatível até
    reconciliação.
17. Índices, caches e derivados reconstruíveis não podem ser confundidos
    com a fonte autoritativa.
18. Perder um índice/cache reconstruível não pode significar perder
    conhecimento autoritativo.
19. IA/LLM, quando usada, produz proposta/evidência; não recebe
    autoridade humana.
20. Ambiguidade normativa relevante sobe à pessoa.
21. Auto-cura significa reparar propriedades verificáveis; não significa
    inventar verdade.
22. O agente de desenvolvimento pode investigar, auditar, raciocinar e
    propor soluções. **Não inventa requisitos.**
23. Uma solução proposta pelo agente que altere regra, significado,
    autoridade ou arquitetura só se torna normativa após decisão humana.
24. Bugs de implementação que não alterem decisões normativas podem ser
    corrigidos e novamente testados.
25. Uma versão nova não apaga a anterior: declara o que mantém,
    substitui, porquê, origem da decisão e evidência.
26. Conhecimento consolidado não é automaticamente apagado, exceto
    quando existir a política humana explícita aplicável; semelhança
    semântica nunca basta.

------------------------------------------------------------------------

## 3. Folha Única

A Folha é uma superfície simples. Não decide o que é conhecimento;
recebe intenção e apresenta resultados.

Prefixos congelados:

-   `@@` --- arquivo
-   `@` --- Web
-   `""` --- fontes
-   `&` --- trabalhar
-   `??` --- perguntar
-   `%` --- calcular
-   `#` --- tema

O utilizador não é obrigado a conhecer Markdown, SQL, IDs, pastas
internas ou esquemas de dados.

A ausência de prefixo continua a permitir linguagem natural normal.
Quando a intenção material não puder ser determinada com segurança, o
sistema pede esclarecimento em vez de inventar uma decisão normativa.

------------------------------------------------------------------------

## 4. Cérebro M1--M14

### M1 --- Identidade

Mantém identidade estável de objetos, operações, documentos, blocos e
referências. Impede que nomes, caminhos ou posições sejam confundidos
com identidade.

### M2 --- Documentos e blocos

Representa unidades de conteúdo manipuláveis sem obrigar a pessoa a
lidar com a representação técnica.

### M3 --- Versões e genealogia

Preserva evolução, predecessores, sucessores, derivações, decisões e
relações entre versões. Uma versão posterior não apaga a história
anterior.

### M4 --- Creative

Espaço persistente de trabalho cognitivo. Conserva hipóteses, rascunhos,
alternativas, erros, rejeições, experiências e contradições.

### M5 --- Canonical

Conhecimento atualmente consolidado/aprovado. Não é sinónimo de verdade
absoluta e não recebe escrita direta de Web, IA, importadores ou
adaptadores.

### M6 --- Portão humano

Aplica a autoridade humana às operações que exigem decisão humana:
promoção, alterações normativas, eliminações protegidas e restantes
operações definidas pelo contrato.

### M7 --- Relações

Mantém ligações entre entidades, documentos, blocos, versões, conceitos,
fontes e projetos sem depender do caminho físico do ficheiro.

### M8 --- Proveniência e fontes

Regista de onde veio a informação, quando foi observada, que
transformação sofreu e que evidência suporta cada estado ou afirmação.

### M9 --- Contradições

Permite detetar, representar e preservar afirmações incompatíveis.
Contradição não implica eliminação automática nem escolha automática da
"verdade".

### M10 --- Pesquisa e recuperação

Recupera contexto relevante a partir da memória e das fontes
autorizadas, preservando proveniência, limites e autoridade.

### M11 --- Regras

Executa regras constitucionais, operacionais e heurísticas versionadas.
Distingue invariantes de heurísticas adaptáveis.

### M12 --- EventLog e auditoria

Regista causalidade e efeitos autoritativos. Permite reconstruir o que
aconteceu e, onde aplicável, replay determinístico.

### M13 --- Integridade e recuperação

Deteta corrupção, interrupções, escritas parciais e divergências;
reconcilia estados verificáveis sem fabricar conhecimento.

### M14 --- Coordenação e iniciativa

Coordena processos e próxima operação útil. Pode criar hipóteses e
subobjetivos instrumentais rastreáveis ao objetivo humano, mas não cria
novas finalidades humanas.

------------------------------------------------------------------------

## 5. Cognição adaptativa

O Cérebro não deve ser reduzido a uma lista gigante de regras `IF/ELSE`.

Ciclo pretendido:

``` text
OBSERVAR
   ↓
IDENTIFICAR / NORMALIZAR
   ↓
RECUPERAR CONTEXTO
   ↓
RECONHECER PADRÕES
   ↓
COMPARAR
   ├─ matemática/determinística
   ├─ semântica
   └─ relacional
   ↓
MEDIR INCERTEZA / CONFIANÇA / CONFLITO
   ↓
FORMAR HIPÓTESES OU ALTERNATIVAS
   ↓
APLICAR LIMITES E AUTORIDADE
   ↓
TENTAR SOLUÇÃO PERMITIDA
   ↓
OBSERVAR RESULTADO
   ↓
CORRIGIR
   ↓
PRESERVAR EXPERIÊNCIA / GENEALOGIA
   ↓
REUTILIZAR APRENDIZAGEM
```

### Fuzzy logic

É usada onde uma classificação binária seria artificial: força de
relação, grau de conflito, confiança, relevância, proximidade,
prioridade ou outros valores graduais definidos por SPEC. Um grau fuzzy
não transforma hipótese em facto.

### Inspiração ELIZA

A contribuição relevante é decomposição de linguagem, reconhecimento de
padrões e transformação de entrada livre em estruturas manipuláveis. Não
se pretende copiar ELIZA como chatbot nem usar padrões linguísticos como
autoridade epistemológica.

### Aprendizagem

Aprender não exige obrigatoriamente uma LLM. Pode resultar de
contadores, pesos, estatística, regras adaptáveis, histórico de
sucesso/falha, relações, feedback e comparação de resultados.

### IA

IA é ferramenta subordinada. Quando a política corrente exigir pedido
explícito, pedido ambíguo não chama IA: pede esclarecimento. O núcleo
adaptativo não-LLM pode continuar a funcionar.

------------------------------------------------------------------------

## 6. Diagrama global

``` text
                              PESSOA
                    autoridade e finalidade
                                │
                                ▼
                         ┌─────────────┐
                         │ FOLHA ÚNICA │
                         │ linguagem   │
                         │ natural     │
                         └──────┬──────┘
                                │ intenção/entrada
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         CÉREBRO M1–M14                          │
│                                                                 │
│ Identidade ─ Documentos ─ Versões/Genealogia                   │
│      │             │              │                             │
│      └─────────────┴──────► Creative ◄──────────────┐           │
│                              │                      │           │
│ Relações ◄──► Proveniência ◄─┼─► Contradições      │           │
│                              │                      │           │
│ Pesquisa/Recuperação ─► Regras/Heurísticas         │           │
│                              │                      │           │
│                     Coordenação/Iniciativa          │           │
│                              │                      │           │
│                       Portão Humano                 │           │
│                              │                      │           │
│                              ▼                      │           │
│                          Canonical                  │           │
│                                                     │           │
│ EventLog/Auditoria ◄──────── todos os efeitos ─────┘           │
│ Integridade/Recuperação ◄── estado + eventos + persistência     │
└─────────────────────────────────────────────────────────────────┘
        ▲                         │                         ▲
        │                         ▼                         │
  adaptadores                persistência              ferramentas
  / importação          Markdown/estruturas/           externas
                       índices conforme SPEC        Web/IA/plugins
                                                        │
                              NÃO têm autoridade ────────┘
```

------------------------------------------------------------------------

## 7. Algoritmo global de entrada e processamento

``` text
1. RECEBER entrada.
2. VALIDAR estrutura mínima e limites.
3. ATRIBUIR operation_id.
4. ATRIBUIR attachment_id quando aplicável.
5. COLOCAR material externo/importado em quarentena.
6. CALCULAR integridade/hash.
7. DETETAR duplicação exata sem apagar.
8. DETETAR formato.
9. SELECIONAR adaptador permitido.
10. CRIAR tarefa de processamento.
11. EXECUTAR transformação/processamento isolado.
12. CAPTURAR resultado como não confiável.
13. CONSTRUIR envelope de resultado.
14. VALIDAR conteúdo e contrato.
15. CLASSIFICAR: READY / REVIEW / FAILED.

SE READY:
16. REGISTAR em Creative.
17. REGISTAR proveniência.
18. EMITIR eventos autoritativos aplicáveis.
19. MATERIALIZAR representação persistente.
20. CONSTRUIR derivados reconstruíveis.
21. APRESENTAR à pessoa.

SE FAILED:
22. REGISTAR/tratar falha sem a transformar em sucesso.

SE INTERRUPÇÃO/DIVERGÊNCIA:
23. RECONCILIAR para COMMITTED / NOT_COMMITTED / RECOVERY_REQUIRED.

SE houver intenção de apagar:
24. CRIAR pedido de eliminação.
25. OBTER autorização humana explícita e vinculada ao alvo/versão.
26. EXECUTAR eliminação autorizada, preservando auditoria exigida.
```

Os IMP são **gates de construção e prova deste mecanismo**. Não são 26
regras destinadas a prever todo o comportamento futuro do Cérebro.

------------------------------------------------------------------------

## 8. Estados principais

Fluxo de ingestão:

``` text
RECEIVED
→ VALIDATED
→ IDENTIFIED
→ QUARANTINED
→ HASHED
→ FORMAT_DETECTED
→ ADAPTER_SELECTED
→ PROCESSING
→ UNTRUSTED_RESULT
→ VALIDATING
→ READY | REVIEW | FAILED
```

Resultado de operação crítica:

``` text
COMMITTED
NOT_COMMITTED
RECOVERY_REQUIRED
```

`READY` significa que o item passou o contrato técnico correspondente.
**READY não significa aprovação humana nem Canonical.**

------------------------------------------------------------------------

## 9. Regras globais G1--G15 dos microprocessos

**G1.** Nenhum IMP escreve diretamente em Canonical salvo o processo
explicitamente autorizado pelo portão humano e respetivo contrato.\
**G2.** Adaptadores não possuem autoridade de escrita/promulgação em
Canonical.\
**G3.** Operações possuem `operation_id` estável.\
**G4.** Estados relevantes são explícitos; não inferir sucesso da
ausência de erro.\
**G5.** Falha não é sucesso e não pode ser mascarada como tal.\
**G6.** Repetição/retry deve respeitar idempotência definida para a
operação.\
**G7.** O original permanece intacto salvo eliminação humana
explicitamente autorizada.\
**G8.** Similaridade semântica, paráfrase, título igual ou conteúdo
quase idêntico não constituem duplicação exata.\
**G9.** Mesmo duplicado exato/hash igual não autoriza automaticamente
eliminar o original.\
**G10.** Efeitos autoritativos passam pelo mecanismo de
eventos/auditoria aplicável.\
**G11.** Derivados reconstruíveis são identificados como tal e não
substituem a fonte autoritativa.\
**G12.** `RECOVERY_REQUIRED` bloqueia operações incompatíveis até
reconciliação.\
**G13.** IA, plugins, Web e ferramentas externas não aprovam
conhecimento nem decisões humanas.\
**G14.** Eliminação protegida exige autorização humana explícita
vinculada ao alvo.\
**G15.** Cada IMP executa apenas a sua responsabilidade; não antecipa
silenciosamente responsabilidades de IMP posteriores.

------------------------------------------------------------------------

# 10. IMP-001 a IMP-026

Cada IMP é implementado e testado isoladamente antes de o seguinte ser
considerado PASS. Os testes abaixo são contratos mínimos de
conformidade; testes adicionais adversariais podem ser acrescentados sem
alterar o significado do IMP.

## IMP-001 --- Receber

**Objetivo:** aceitar uma entrada e criar representação inicial sem a
interpretar como conhecimento aprovado.\
**Entrada:** payload/entrada permitida.\
**Saída:** estado `RECEIVED`.\
**Proibido:** promover, eliminar original, declarar conteúdo
verdadeiro.\
**Teste positivo:** entrada válida gera exatamente uma receção
identificável.\
**Teste negativo:** entrada vazia/corrompida não produz falsa receção
bem-sucedida.

## IMP-002 --- Validar entrada

**Objetivo:** verificar contrato mínimo, tamanho, presença e estrutura
necessária.\
**Entrada:** `RECEIVED`.\
**Saída:** `VALIDATED` ou falha explícita.\
**Proibido:** corrigir silenciosamente conteúdo substantivo.\
**Teste positivo:** entrada conforme passa.\
**Teste negativo:** entrada fora do contrato falha sem mutação
autoritativa indevida.

## IMP-003 --- operation_id

**Objetivo:** atribuir identidade estável à operação.\
**Entrada:** entrada validada.\
**Saída:** `operation_id` + estado identificado.\
**Proibido:** reutilizar identidade de operação diferente.\
**Teste:** retry da mesma operação mantém comportamento idempotente;
operações distintas não colidem.

## IMP-004 --- attachment_id

**Objetivo:** identificar anexos/objetos associados independentemente do
nome/caminho.\
**Entrada:** objeto aplicável.\
**Saída:** `attachment_id`.\
**Proibido:** usar filename/path como única identidade.\
**Teste:** mover/renomear não quebra identidade; dois anexos distintos
não colidem.

## IMP-005 --- Quarentena

**Objetivo:** isolar material ainda não confiável.\
**Entrada:** material externo/importado.\
**Saída:** `QUARANTINED`.\
**Proibido:** escrita direta em Canonical ou execução implícita do
conteúdo.\
**Teste:** item em quarentena não altera Canonical nem ganha autoridade
por existir.

## IMP-006 --- Hash

**Objetivo:** calcular identidade/integridade de bytes segundo algoritmo
versionado.\
**Entrada:** bytes preservados.\
**Saída:** hash + `HASHED`.\
**Proibido:** alterar bytes para fazer o hash "bater".\
**Teste:** mesmos bytes → mesmo hash; alteração de um byte → deteção de
diferença.

## IMP-007 --- Duplicação exata

**Objetivo:** reconhecer duplicação byte-a-byte/exata segundo o
contrato.\
**Entrada:** hash + objeto.\
**Saída:** relação de duplicação exata ou não duplicado.\
**Proibido:** tratar semelhança semântica como duplicação exata; apagar
automaticamente.\
**Teste:** cópia exata é reconhecida; paráfrase não; nenhuma das duas é
apagada automaticamente.

## IMP-008 --- Formato

**Objetivo:** determinar formato suportado com evidência suficiente.\
**Entrada:** objeto em quarentena.\
**Saída:** `FORMAT_DETECTED` ou REVIEW/FAILED.\
**Proibido:** assumir formato apenas pela extensão quando houver
conflito.\
**Teste:** formato conhecido é identificado; conflito extensão/conteúdo
não é silenciosamente aceite.

## IMP-009 --- Adaptador

**Objetivo:** selecionar adaptador permitido para o formato/tarefa.\
**Entrada:** formato + política.\
**Saída:** `ADAPTER_SELECTED`.\
**Proibido:** adaptador ganhar autoridade epistemológica ou Canonical.\
**Teste:** formato suportado seleciona adaptador correto; formato não
suportado não executa adaptador arbitrário.

## IMP-010 --- Tarefa

**Objetivo:** construir tarefa explícita e delimitada.\
**Entrada:** objeto + adaptador + intenção.\
**Saída:** tarefa versionada.\
**Proibido:** ampliar silenciosamente o âmbito.\
**Teste:** tarefa contém alvo, operação e limites; intenção insuficiente
conduz a REVIEW/ASK e não a invenção normativa.

## IMP-011 --- Executar

**Objetivo:** executar apenas a tarefa autorizada no contexto
permitido.\
**Entrada:** tarefa.\
**Saída:** resultado bruto.\
**Proibido:** efeitos fora do contrato.\
**Teste:** execução produz resultado esperado; falha/timeout não é
marcado como sucesso.

## IMP-012 --- Resultado

**Objetivo:** capturar saída sem lhe atribuir confiança automática.\
**Entrada:** saída da execução.\
**Saída:** `UNTRUSTED_RESULT`.\
**Proibido:** resultado externo tornar-se conhecimento aprovado
diretamente.\
**Teste:** saída válida continua não confiável até validação; saída
ausente gera falha explícita.

## IMP-013 --- Envelope

**Objetivo:** encapsular resultado com identidade, versão, origem e
metadados necessários.\
**Entrada:** resultado não confiável.\
**Saída:** envelope validável.\
**Proibido:** perder ligação à operação/origem.\
**Teste:** envelope permite rastrear resultado até operação e entrada;
envelope incompleto não avança silenciosamente.

## IMP-014 --- Conteúdo

**Objetivo:** validar o conteúdo contra o contrato aplicável sem
inventar significado.\
**Entrada:** envelope.\
**Saída:** resultado de validação.\
**Proibido:** transformar hipótese em facto ou corrigir conteúdo
substantivo sem registo.\
**Teste:** conteúdo conforme passa; conteúdo incompatível é
REVIEW/FAILED com motivo observável.

## IMP-015 --- READY / REVIEW / FAILED

**Objetivo:** produzir estado explícito de decisão técnica.\
**Entrada:** validações.\
**Saída:** exatamente um estado aplicável.\
**Proibido:** confundir `READY` com aprovação humana/Canonical.\
**Teste:** casos definidos atingem estados esperados; falha não cai em
READY por default.

## IMP-016 --- Creative

**Objetivo:** persistir item apto no espaço Creative preservando
identidade e genealogia.\
**Entrada:** item READY permitido.\
**Saída:** registo Creative.\
**Proibido:** apagar alternativas/rejeições ou promover
automaticamente.\
**Teste:** item aparece em Creative; Canonical permanece inalterado.

## IMP-017 --- Proveniência

**Objetivo:** ligar conteúdo às fontes, operações, versões e
transformações conhecidas.\
**Entrada:** item + evidência.\
**Saída:** proveniência consultável.\
**Proibido:** fabricar origem desconhecida.\
**Teste:** cadeia conhecida é recuperável; campo desconhecido permanece
desconhecido.

## IMP-018 --- Eventos

**Objetivo:** emitir eventos autoritativos necessários aos efeitos
persistentes.\
**Entrada:** operação/estado aprovado pelo contrato.\
**Saída:** evento versionado/auditável.\
**Proibido:** mutação autoritativa invisível ao EventLog quando o
contrato exige evento.\
**Teste:** evento repetido respeita idempotência; replay usa dados
congelados.

## IMP-019 --- Materializar

**Objetivo:** produzir representação persistente autorizada a partir do
estado/eventos.\
**Entrada:** estado/eventos aplicáveis.\
**Saída:** materialização verificável.\
**Proibido:** materialização alterar significado por conveniência
técnica.\
**Teste:** materialização e replay convergem; crash controlado conduz a
estado reconciliável.

## IMP-020 --- Derivados

**Objetivo:** criar índices, caches, vistas ou outras projeções
reconstruíveis.\
**Entrada:** fonte autoritativa.\
**Saída:** derivados marcados como reconstruíveis.\
**Proibido:** derivado substituir silenciosamente a autoridade da
fonte.\
**Teste:** apagar derivado e reconstruí-lo não perde fonte nem muda
estado autoritativo.

## IMP-021 --- Apresentar

**Objetivo:** mostrar resultado à pessoa na Folha sem expor complexidade
técnica desnecessária.\
**Entrada:** resultado/estado autorizado para apresentação.\
**Saída:** apresentação humana.\
**Proibido:** UI decidir Canonical ou esconder estado material de
falha/revisão.\
**Teste:** utilizador consegue compreender resultado e estado sem editar
Markdown/SQL/IDs.

## IMP-022 --- Falha

**Objetivo:** registar e conter falhas.\
**Entrada:** erro, exceção, timeout, validação negativa.\
**Saída:** FAILED/NOT_COMMITTED/estado apropriado + evidência.\
**Proibido:** perda silenciosa, falso PASS ou continuação incompatível.\
**Teste:** falha injetada não corrompe fonte autoritativa e permanece
diagnosticável.

## IMP-023 --- Reconciliar

**Objetivo:** determinar estado real depois de interrupção, escrita
parcial ou incerteza.\
**Entrada:** recibos/eventos/estado persistido/evidência.\
**Saída:** `COMMITTED`, `NOT_COMMITTED` ou `RECOVERY_REQUIRED`.\
**Proibido:** adivinhar que a operação terminou.\
**Teste:** crash em pontos definidos produz uma das três conclusões
demonstráveis; `RECOVERY_REQUIRED` bloqueia continuação incompatível.

## IMP-024 --- Pedido de eliminação

**Objetivo:** representar intenção de eliminar sem eliminar ainda.\
**Entrada:** pedido humano + alvo identificável.\
**Saída:** pedido pendente auditável.\
**Proibido:** executar eliminação nesta etapa.\
**Teste:** criar pedido não altera bytes/conhecimento alvo.

## IMP-025 --- Autorização

**Objetivo:** validar autorização humana explícita para
alvo/versão/operação concretos.\
**Entrada:** pedido pendente + decisão humana.\
**Saída:** autorização válida ou rejeição/expiração.\
**Proibido:** autoaprovação, aprovação por IA/plugin ou autorização vaga
reutilizável.\
**Teste:** autorização correta permite avançar; alvo/versão diferente,
autorização ausente ou inválida não permite.

## IMP-026 --- Eliminação

**Objetivo:** executar somente a eliminação especificamente autorizada.\
**Entrada:** autorização válida.\
**Saída:** eliminação verificável + auditoria/estado final exigido.\
**Proibido:** ampliar alvo, apagar por similaridade, apagar sem
autorização.\
**Teste:** apenas o alvo autorizado é afetado; retry não amplia efeito;
falha parcial é reconciliável.

------------------------------------------------------------------------

## 11. T1--T6 --- testes constitucionais transversais

**T1.** IA/adaptador não escreve nem promove diretamente em Canonical.\
**T2.** Autosave, importação, comando, relógio ou fim de workflow não
equivalem a aprovação humana.\
**T3.** Mover/renomear ficheiro não quebra identidade e relações.\
**T4.** Falha crítica termina demonstravelmente em `COMMITTED`,
`NOT_COMMITTED` ou `RECOVERY_REQUIRED`.\
**T5.** Perda de índice/cache reconstruível não perde fonte/estado
autoritativo.\
**T6.** Apagar original exige autorização humana explícita;
similaridade, paráfrase ou contradição não autorizam eliminação.

------------------------------------------------------------------------

## 12. Protocolo obrigatório de implementação

Para cada IMP:

``` text
SPEC
  ↓
IMPLEMENTAÇÃO MÍNIMA
  ↓
TESTE POSITIVO
  ↓
TESTE NEGATIVO
  ↓
TESTE DE FALHA/ADVERSARIAL quando aplicável
  ↓
REGRESSÃO DOS IMP ANTERIORES
  ↓
EVIDÊNCIA
  ↓
REVISÃO
  ↓
PASS | FAIL | NOT RUN
  ↓
só PASS permite considerar o IMP fechado
```

### PASS

Todos os critérios definidos para o IMP foram executados e a evidência
demonstra conformidade.

### FAIL

Pelo menos um critério executado falhou. O agente diagnostica e pode
propor soluções. Não altera silenciosamente requisitos.

### NOT RUN

Teste não executado ou dependência indisponível. Nunca é sinónimo de
PASS.

------------------------------------------------------------------------

## 13. Autoridade do agente de desenvolvimento

O agente pode:

-   auditar documentação e código;
-   procurar incoerências e falhas;
-   analisar lógica;
-   propor uma ou várias soluções;
-   programar a solução já autorizada;
-   corrigir bugs que não alterem requisitos;
-   criar testes adicionais;
-   tentar quebrar a implementação;
-   medir e apresentar evidência;
-   sugerir alteração arquitetural quando uma falha concreta o
    justificar.

O agente não pode:

-   inventar requisitos e tratá-los como decisões de Pedro;
-   transformar proposta em regra aprovada;
-   alterar autoridade humana;
-   eliminar genealogia;
-   esconder FAIL;
-   declarar teste não executado como PASS;
-   usar uma ferramenta como desculpa para redefinir o sistema;
-   mudar silenciosamente significado de Creative, Canonical, EventLog,
    módulos ou prefixos.

**Fórmula:** autonomia técnica alta; autonomia normativa baixa.

------------------------------------------------------------------------

## 14. Como uma correção entra no sistema

``` text
FALHA / PROBLEMA OBSERVADO
        ↓
AUDITORIA
        ↓
CAUSA PROVÁVEL
        ↓
SOLUÇÃO TÉCNICA POSSÍVEL?
   ├─ sim, sem mudar norma
   │      ↓
   │   corrigir → testar → evidência
   │
   └─ exige decisão normativa
          ↓
       PROPOSTA
          ↓
        PEDRO
       SIM / NÃO / ALTERAR
          ↓
     só então atualizar
     contrato/implementação
```

A arquitetura não é reaberta por curiosidade. Uma falha concreta pode
justificar reexaminar apenas a parte afetada.

------------------------------------------------------------------------

## 15. Preservação da evolução

A genealogia documental não é lixo.

As fases anteriores --- incluindo experiências com Obsidian, Logseq,
Activepieces, Joplin, diferentes desenhos SQLite, modelos locais,
arquiteturas cognitivas, fuzzy logic, ELIZA e projetos comparáveis ---
permanecem como evidência do percurso.

Uma solução antiga pode ter três estados documentais:

-   **VIGENTE** --- continua normativa;
-   **SUBSTITUÍDA** --- já não governa a implementação, mas explica a
    evolução;
-   **PROPOSTA/EXPERIÊNCIA** --- nunca foi decisão final ou ainda não
    foi validada.

Nunca reescrever o passado para parecer que a arquitetura atual existiu
desde o início.

------------------------------------------------------------------------

## 16. O que está provado e o que não está

### Documentalmente estabelecido

-   intenção e autoridade humana;
-   Folha Única e sete prefixos;
-   M1--M14;
-   separação Creative/Canonical;
-   EventLog/auditoria/replay;
-   proveniência, relações, contradições e genealogia;
-   regras de preservação;
-   sequência IMP-001--IMP-026;
-   desenvolvimento/teste por microprocessos;
-   distinção entre proposta técnica e decisão normativa;
-   objetivo de comportamento adaptativo.

### Ainda não provado experimentalmente

-   que M1--M14 funcionam corretamente em conjunto;
-   que os 26 IMP sobrevivem a testes reais;
-   que replay e recovery se mantêm sob crashes reais;
-   que fuzzy/padrões melhoram decisões sem introduzir deriva;
-   que aprendizagem/correção permanece controlada;
-   que Creative/Canonical escalam sem degradação;
-   que a Folha continua simples quando o Core cresce;
-   que o sistema completo produz benefício suficiente face a
    alternativas mais simples.

Não declarar estas hipóteses como resultados antes dos testes.

------------------------------------------------------------------------

## 17. Critério científico/engenharia do projeto

O objetivo dos testes não é provar que Pedro estava certo.

É tentar encontrar onde o sistema está errado.

``` text
HIPÓTESE
  ↓
IMPLEMENTAÇÃO
  ↓
TENTATIVA DE QUEBRA
  ↓
MEDIÇÃO
  ↓
PASS / FAIL
  ↓
CORREÇÃO OU REVISÃO FUNDAMENTADA
```

Se um mecanismo falhar, a falha é preservada como conhecimento. Se uma
solução corrigir a falha, ficam preservados problema, solução, versão e
evidência.

------------------------------------------------------------------------

## 18. Regra final para Cursor/Codex/agentes

> Lê esta baseline antes de implementar. Não redesenhes a arquitetura
> por conveniência. Não inventes requisitos. Podes e deves auditar,
> raciocinar, encontrar problemas e propor soluções. Distingue sempre
> proposta técnica de decisão normativa. Implementa um IMP de cada vez.
> Executa os testes desse IMP e a regressão necessária. Regista
> evidência real. FAIL e NOT RUN nunca são PASS. Não avances
> silenciosamente sobre uma decisão humana em falta. Preserva originais,
> versões, genealogia, proveniência e EventLog. Uma nova decisão
> substitui apenas aquilo que declara substituir.

------------------------------------------------------------------------

## 19. Estado de arranque

A fase conceptual está fechada como baseline.

A próxima fase é:

**implementar → testar → tentar quebrar → medir → corrigir**, IMP por
IMP.

A arquitetura só é reaberta quando evidência concreta de
implementação/teste demonstrar uma falha estrutural que não possa ser
resolvida dentro dos mecanismos existentes.

Até existir essa evidência, uma dificuldade de programação é um problema
de implementação, não prova de falha da arquitetura.


---

# PARTE II — BASELINE OPERACIONAL / STACK E ORQUESTRAÇÃO

Esta secção complementa a Parte I. Em conflito, prevalece a decisão humana posterior explicitamente documentada; não apagar a divergência.

# CÉREBRO --- Baseline de Implementação 2026-09-26

**Estado:** arquitetura conceptual fechada. Este documento é a
referência curta para implementação.\
**Objetivo:** uma Folha simples para qualquer pessoa; toda a
complexidade fica escondida.

## 1. Regra-mãe

A pessoa é a autoridade máxima. A máquina serve a pessoa.

O sistema pode pesquisar, comparar, relacionar, calcular, organizar,
recuperar, propor, executar ferramentas e aprender padrões operacionais.
Não pode transformar uma hipótese em conhecimento consolidado, apagar
conhecimento, alterar regras constitucionais ou substituir uma decisão
humana sem autorização prevista.

**Python-first, não Python-only.** Usa-se a solução madura, leve e
testável que melhor cumpra a função.\
**USE \> ADAPT \> CREATE.**

## 2. Visão do sistema

``` text
                         PESSOA
                           │
                           ▼
                    ┌─────────────┐
                    │    FOLHA    │
                    │ texto normal│
                    └──────┬──────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│                    CÉREBRO / CORE                    │
│                                                      │
│ M1–M14                                               │
│ regras • identidade • memória • relações • versões  │
│ proveniência • contradições • pesquisa • EventLog   │
│ integridade • recuperação • coordenação              │
│                                                      │
│  Memória de trabalho                                 │
│  Memória comportamental/procedimental                │
│  Conhecimento persistente                            │
│                                                      │
│  Comparador determinístico                           │
│  Comparador semântico                                │
│  Comparador relacional                               │
│                                                      │
│       ┌────────────┐       ┌────────────┐             │
│       │  CREATIVE  │ ───►  │ HUMAN GATE │ ───►       │
│       └────────────┘       └────────────┘      │      │
│                                                ▼      │
│                                         ┌──────────┐ │
│                                         │CANONICAL │ │
│                                         └──────────┘ │
└────────────────────────┬─────────────────────────────┘
                         │ tarefa/capacidade
                         ▼
              ┌──────────────────────┐
              │    ACTIVEPIECES      │
              │ Flows + Pieces       │
              │ execução operacional │
              └──────────┬───────────┘
                         │
       ┌─────────────────┼────────────────────────┐
       ▼                 ▼                        ▼
 Python/ferramentas   Web/Zotero/etc.      IA ISOLADA
 LibreOffice/PDF      LanguageTool/etc.    contexto mínimo
                                               │
                                               ▼
                                      proposta/resultado
```

**Fronteira fundamental:** o Cérebro governa conhecimento e autoridade.
Activepieces executa trabalho.

## 3. Folha

A Folha é a única superfície que a pessoa precisa de aprender.

Aceita linguagem natural, incluindo erros ortográficos, frases
incompletas e linguagem informal. Nunca obriga a pessoa a conhecer
Markdown, SQLite, IDs, pastas, módulos, Pieces ou Flows.

Prefixos opcionais:

-   `@@` arquivo
-   `@` web
-   `""` fontes
-   `&` trabalhar
-   `??` perguntar
-   `%` calcular
-   `#` tema

Os prefixos são sinais fortes de intenção, não uma linguagem
obrigatória.

## 4. Dois cofres

### Creative

Recebe exploração, hipóteses, alternativas, material em evolução,
contradições, erros, propostas e caminhos rejeitados.

### Canonical

Contém o conhecimento atualmente consolidado pela pessoa com a evidência
disponível.

Canonical **não significa verdade absoluta**.

Quando novo conhecimento substitui o anterior:

``` text
Canonical v1
    │
nova evidência
    ▼
Creative/Candidate
    │
comparação + proveniência + contradições
    ▼
Human Gate
    │
    ├── rejeita ──► preserva Creative/genealogia
    │
    └── aprova ──► Canonical v2
                       │
                       └── v1 permanece histórico
```

Nenhuma semelhança semântica, paráfrase ou título igual autoriza
eliminação.

## 5. M1--M14

  Módulo   Responsabilidade
  -------- -------------------------
  M1       Identidade
  M2       Documentos/blocos
  M3       Versões/genealogia
  M4       Creative
  M5       Canonical
  M6       Human Gate
  M7       Relações
  M8       Proveniência/fontes
  M9       Contradições
  M10      Pesquisa/recuperação
  M11      Regras
  M12      EventLog/auditoria
  M13      Integridade/recuperação
  M14      Coordenação/iniciativa

Não criar M15 para Activepieces. Activepieces é infraestrutura de
execução externa ao núcleo epistemológico.

## 6. Memórias

1.  **Working Memory** --- contexto temporário da tarefa atual.
2.  **Behavioral/Procedural Memory** --- hábitos operacionais,
    correções, preferências e experiência de execução.
3.  **Persistent Knowledge** --- Creative + Canonical.

Comportamento aprendido nunca substitui uma instrução humana explícita
atual.

## 7. Três formas de comparação

### Determinística

Hashes, estados, valores, datas, regras, versões, limites, consistência
e invariantes.

### Semântica

Significados, equivalências possíveis, incompatibilidades, contexto e
contradições candidatas. O resultado semântico é evidência/proposta, não
verdade.

### Relacional

Nós, documentos, blocos, conceitos, fontes, backlinks, vizinhanças,
caminhos e relações temporais.

Os três mecanismos podem cruzar resultados. Concordância não promove
automaticamente conhecimento para Canonical.

## 8. Activepieces como oficina universal

Activepieces concentra a execução operacional.

Uma **Piece** pode ser uma ferramenta/plugin.\
Um **Flow** pode ser um especialista/agente operacional.\
Python pode ser chamado quando for a melhor solução.\
TypeScript pode ser usado quando for mais maduro ou natural à Piece.\
Ferramentas externas podem ser chamadas por HTTP/API/processo
controlado.

Exemplos de capacidades:

``` text
SEARCH_WEB
SOURCE_MANAGEMENT
LANGUAGE_CHECK
DOCUMENT_CREATE
DOCUMENT_CONVERT
PDF_EXTRACT
CALCULATE
CODE_TASK
BACKUP
IMPORT
EXPORT
AI_ANALYSIS
```

Um Flow pode combinar várias:

``` text
pesquisar
  ↓
recolher fontes
  ↓
normalizar
  ↓
Python comparar/calcular
  ↓
Zotero registar fontes
  ↓
IA isolada apenas se autorizada/necessária
  ↓
LibreOffice produzir documento
  ↓
devolver resultado + evidência
```

Activepieces nunca recebe autoridade para decidir Canonical, apagar
conhecimento ou alterar regras do Cérebro.

## 9. IA

A IA é uma capacidade opcional e isolada.

``` text
Core
 ↓ pedido autorizado
Activepieces / porta AI
 ↓
Sandbox/Cofre IA
 ↓
modelo
 ↓
Proposal + evidence
 ↓
Core
```

A IA recebe somente o contexto necessário à tarefa.

Por defeito não recebe acesso livre a Creative, Canonical, SQLite,
EventLog, credenciais, filesystem, rede ou Activepieces.

Retirar todos os modelos de IA deve deixar funcionais identidade,
memória, regras, pesquisa lexical, organização, relações, comparação
determinística, proveniência, genealogia, recuperação e autoridade
humana.

## 10. Sem RAG como arquitetura

O Cérebro não é:

``` text
pergunta → top-k chunks → LLM → resposta
```

O Cérebro acumula estrutura persistente:

``` text
entrada
 → preservar original
 → identificar
 → normalizar
 → relacionar
 → comparar
 → ligar fontes
 → detetar contradições
 → versionar
 → classificar Creative/Canonical
 → preservar genealogia
 → recuperar posteriormente
```

FTS5, fuzzy matching, relações e ranking matemático podem ser usados sem
tornar embeddings/vector DB/RAG obrigatórios.

IA pode receber um pacote de contexto produzido pelo Cérebro quando uma
tarefa realmente justificar geração ou interpretação semântica avançada.

## 11. Algoritmo operacional principal

``` text
RECEBER entrada da Folha

1. Preservar original.
2. Criar operation_id.
3. Identificar intenção:
      prefixo explícito OU
      regras/padrões/contexto.
4. Normalizar apenas para processamento;
   nunca destruir o original.
5. Recuperar contexto necessário:
      working memory
      procedural memory
      Creative
      Canonical
      relações
      fontes
      versões.
6. Executar comparadores necessários:
      determinístico
      semântico
      relacional.
7. Verificar:
      regras
      autoridade
      contradições
      ambiguidade
      permissões.
8. Se o Core resolve:
      produzir resultado.
9. Se necessita capacidade externa:
      entregar tarefa delimitada a Activepieces.
10. Activepieces:
      escolhe/executa Flow/Pieces/ferramentas;
      pode chamar Python;
      pode chamar especialista;
      pode chamar IA apenas através da fronteira autorizada.
11. Receber:
      resultado
      evidência
      fontes
      erros
      estado.
12. Validar resultado.
13. Registar EventLog.
14. Guardar novo material no destino permitido:
      normalmente Creative.
15. Se houver promoção/alteração Canonical:
      Human Gate.
16. Preservar genealogia.
17. Apresentar resposta simples na Folha.
18. Se falhar:
      não fingir sucesso;
      reconciliar/repetir/fallback ou pedir decisão humana.
```

## 12. Contrato mínimo de capacidade

Todas as ferramentas devem poder ser tratadas através de um envelope
comum:

``` text
operation_id
capability
input
context_refs
permissions
status
result
evidence
sources
error
```

O Core pede uma **capacidade**, não precisa de conhecer a implementação
concreta.

Exemplo:

``` text
capability = LANGUAGE_CHECK

titular   = LanguageTool
fallback  = implementação local permitida
```

Trocar uma ferramenta não deve obrigar a alterar as regras do Cérebro.

## 13. IMP-001--026

``` text
001 Receive
002 Validate input
003 operation_id
004 attachment_id
005 Quarantine
006 Hash
007 Exact duplication
008 Format
009 Adapter
010 Task
011 Execute
012 Result
013 Envelope
014 Content validation
015 READY / REVIEW / FAILED
016 Creative
017 Provenance
018 Events
019 Materialize
020 Derivatives
021 Present
022 Failure
023 Reconcile
024 Deletion request
025 Authorization
026 Deletion
```

Cada IMP tem responsabilidade primária. Sobreposição útil é permitida
quando fornece validação independente ou recuperação.

## 14. Regras globais mínimas

-   Nenhum adaptador, Piece, Flow, IA ou agente promove diretamente
    Canonical.
-   Cada operação relevante possui `operation_id` estável.
-   Estados são explícitos.
-   Falha nunca é apresentada como sucesso.
-   Retry deve ser idempotente.
-   Original permanece intacto salvo eliminação humana autorizada.
-   Similaridade, paráfrase ou contradição não autorizam eliminação.
-   Hash igual identifica duplicação exata; não é autorização automática
    de eliminação.
-   Efeitos autoritativos passam por EventLog/auditoria.
-   Derivados reconstruíveis não substituem fontes autoritativas.
-   `RECOVERY_REQUIRED` bloqueia operações incompatíveis até
    reconciliação.
-   Eliminação protegida exige autorização humana explícita ligada ao
    alvo exato.
-   IA e ferramentas externas não aprovam decisões humanas.

## 15. Testes constitucionais

O sistema só pode ser considerado conforme se passar, no mínimo:

``` text
T1 IA/Piece/adaptador tenta escrever Canonical diretamente → BLOQUEADO
T2 autosave/workflow/time/evento tenta equivaler a aprovação humana → BLOQUEADO
T3 mover/renomear documento → identidade/relações preservadas
T4 crash crítico → COMMITTED | NOT_COMMITTED | RECOVERY_REQUIRED
T5 apagar índice/cache → fonte autoritativa permanece e índice reconstrói
T6 eliminar original sem autorização humana explícita → BLOQUEADO
T7 desligar toda a IA → Core continua funcional
T8 repetir operação com mesmo operation_id → sem efeitos autoritativos duplicados
T9 falha de Piece titular → fallback permitido ou falha explícita
T10 resultado externo contraditório → preserva ambos e sinaliza; não sobrescreve silenciosamente
```

## 16. Estratégia de implementação

Para cada microprocesso:

``` text
SPEC
 ↓
implementação mínima
 ↓
teste positivo
 ↓
teste negativo
 ↓
teste de falha/adversarial
 ↓
regressão
 ↓
evidência
 ↓
PASS / FAIL / NOT RUN
```

`PASS` exige evidência.\
`FAIL` não permite alterar silenciosamente o requisito.\
`NOT RUN` nunca equivale a PASS.

## 17. Ordem para Cursor

Não redesenhar a arquitetura.

### Fase A --- esqueleto

Folha mínima → Core Python → SQLite/FTS5 → Markdown → EventLog →
Creative/Canonical.

### Fase B --- invariantes

IDs, versões, proveniência, relações, contradições, Gate, recuperação e
testes constitucionais.

### Fase C --- Activepieces

Contrato de capability → primeira integração → retries/idempotência →
fallback → evidência.

### Fase D --- especialistas

LanguageTool, Zotero, LibreOffice, Web, documentos/PDF e outras
capacidades selecionadas.

### Fase E --- IA isolada

Somente depois de o Core passar os testes sem IA. Implementar porta
controlada, contexto mínimo, permissões temporárias e retorno como
Proposal.

### Fase F --- sistema completo

Testes ponta-a-ponta, crashes, duplicações, restauro, perda de índices,
falhas de Activepieces, falhas de ferramentas e recuperação.

## 18. Instrução normativa para Cursor

> Implementa esta arquitetura; não a redesenhes. Podes investigar,
> comparar, programar, corrigir bugs, criar testes e propor
> alternativas. Não inventes requisitos nem transformes propostas em
> decisões normativas. Uma alteração estrutural exige falha observada
> que a arquitetura atual não consiga resolver, evidência reproduzível,
> proposta documentada e decisão humana. Corrige livremente erros de
> implementação que não alterem comportamento aprovado. Nunca declares
> PASS sem teste executado e evidência.

## 19. Critério de simplicidade

Para a pessoa, o sistema deve continuar a parecer:

``` text
┌─────────────────────────────────────┐
│                                     │
│  uma folha vazia                    │
│  e um cursor                        │
│                                     │
└─────────────────────────────────────┘
```

Toda a arquitetura acima existe precisamente para que a pessoa **não
tenha de a aprender**.


---

# PARTE III — ESPECIFICAÇÃO FUNCIONAL CORRIGIDA DOS IMP

Esta é a versão mais detalhada dos contratos IMP recuperada. Os marcadores **POR DEFINIR** são bloqueios reais. Não os preencher por inferência.

# IMP-001–IMP-026 — Especificação funcional corrigida

Estado: contrato de desenho para futura programação; não é código, nem teste executado, nem alteração ao repositório. Subordinado à arquitetura conceptual fechada: pessoa no topo; Creative e Canonical como domínios de autoridade distintos; eventos autoritativos → estado materializado → derivados. Questões ainda não decididas estão marcadas **POR DEFINIR**, não são delegadas ao programador para improvisação.

## Regras globais

G1. Nenhum IMP escreve diretamente em Canonical.\
G2. Nenhum adaptador escreve diretamente em Creative, SQLite, Markdown ou EventLog.\
G3. Cada execução admitida possui `operation_id` a partir de IMP-003. Antes disso, a receção tem apenas uma referência/recibo temporário que permite correlacionar retries; isso não é um `operation_id` nem autoriza efeitos autoritativos.\
G4. Cada transição aceita somente estados e entradas explicitamente permitidos; o orquestrador, não um IMP adjacente, decide a próxima etapa.\
G5. Falha nunca é interpretada como sucesso.\
G6. Repetição da mesma `operation_id` não duplica efeitos; a prova de que duas tentativas pertencem à mesma receção lógica exige correlação suficiente, não mera igualdade de nome ou bytes.\
G7. O original nunca é alterado durante processamento; a eliminação futura é ramo separado e autorizado.\
G8. Semelhança semântica nunca significa duplicação.\
G9. Duplicação exata significa igualdade de bytes demonstrada por critérios definidos; digest idêntico é candidato a comparação, não autorização para eliminação.\
G10. Qualquer efeito autoritativo passa pelo mecanismo de eventos; operações persistentes anteriores a IMP-018 requerem contrato de recibos/reconciliação compatível com a hierarquia autoritativa. **POR DEFINIR:** quais eventos e fronteiras transacionais representam essas mutações preliminares.\
G11. FTS5/cache são derivados e reconstruíveis.\
G12. `RECOVERY_REQUIRED` bloqueia novas mutações da operação até reconciliação.\
G13. Plugins e IA não aprovam nada.\
G14. Eliminação do original exige decisão humana explícita, específica e atual.\
G15. Cada IMP executa só a sua responsabilidade.\
G16. Resultados externos que sustentem uma mutação autoritativa têm evidência/proveniência congelada; replay não invoca novamente adaptadores, Web ou IA.

## Desenho e estados

```
text
```

`001 → 002 → 003 → 004 → 005 → 006 → 007 → 008 → 009 → 010     → 011 → 012 → 013 → 014 → 015  IMP-015: READY  → 016 → 017 → 018 → 019 → 020 → 021          REVIEW → 021 (apresentar revisão; sem Creative automático)          FAILED → 022 (falha de conteúdo)  Falha técnica em qualquer etapa → 022; interrupção/incerteza → 023. RECOVERY_REQUIRED → bloquear mutações da operação até reconciliação. Pedido futuro e separado: 024 → 025 → 026.`

Os estados de progresso da operação podem ser `RECEIVED`, `VALIDATED`, `IDENTIFIED`, `QUARANTINED`, `HASHED`, `FORMAT_DETECTED`, `ADAPTER_SELECTED`, `PROCESSING`, `UNTRUSTED_RESULT`, `VALIDATING`, `MATERIALIZED`, `DERIVATIVES_UPDATED`/`DERIVATIVES_DIRTY` e `PRESENTED`. `READY`/`REVIEW`/`FAILED` de IMP-015 são classificações do conteúdo, não recibos de commit. `COMMITTED`/`NOT_COMMITTED`/`RECOVERY_REQUIRED` são estados de reconciliação de mutações. `RETRYABLE` é um resultado operacional condicionado a segurança comprovada, não um estado de sucesso. Uma UI apresentada não aprova nem materializa conhecimento.

A classificação de conteúdo `REVIEW` conserva a ligação ao original e a evidência existente e é apresentada em IMP-021; não cria Creative. Uma decisão humana posterior que aceite ou transforme esse conteúdo exige contrato específico futuro, fora do fluxo automático aqui definido. **POR DEFINIR:** limites concretos de aceitação de formato, tamanho, classificação e retenção; não há valores inventados neste documento.

## Microprocessos e testes de contrato

Para cada IMP, os testes abaixo são casos especificados com resultado esperado; nenhum foi executado. O portão de revisão exige coerência das pré-condições, saídas, falhas, transições, idempotência e invariantes aplicáveis antes de avançar ao IMP seguinte. Um caso não resolvido bloqueia o portão.

## IMP-001 — Receber ficheiro

Entrada: ficheiro largado na Folha e contexto da sessão. Receber stream/referência, sem interpretar conteúdo, converter ou alterar bytes; criar receção temporária. Saída: `ReceivedInput(temp_ref, filename, byte_size)` ou `RECEIVE_FAILED` por acesso ausente, transferência incompleta ou interrupção. Proibido criar IDs definitivos, hash, deduplicar ou escrever Creative/Canonical. Testes: igualdade dos bytes recebidos com os enviados; nome Unicode; ficheiro vazio; ficheiro grande; interrupção; ausência de efeito autoritativo. Um ficheiro vazio pode ser recebido aqui; a aceitação é decidida em IMP-002.

## IMP-002 — Validar entrada

Entrada: `ReceivedInput`. Confirmar existência, legibilidade, integridade verificável da transferência, limite de tamanho configurado e objeto processável; não inferir formato pelo nome. Saída: `InputAccepted` ou `InputRejected(reason)`. Rejeição encerra o processamento normal, preservando apenas a evidência exigida pela política de falhas/retenção. Testes: válido; inexistente; ilegível; truncado detetável; tamanho fora do limite; nome enganador; ficheiro vazio segundo regra explícita. Limites/política concretos: **POR DEFINIR**.

## IMP-003 — Criar `operation_id`

Entrada: `InputAccepted`. Se houver prova de pertença a operação já registada, reutilizar o ID; caso contrário, gerar ID único e registar contexto mínimo. Saída: `OperationCreated(operation_id, temp_ref)`. Igualdade de nome/hash não prova mesma operação lógica. Testes: unicidade; retry correlacionado; receções separadas de bytes iguais; colisão simulada; crash; ID inválido recusado. A persistência do registo inicial deve satisfazer G10: fronteira de evento/recibo **POR DEFINIR**.

## IMP-004 — Criar `attachment_id`

Entrada: operação válida e input aceite. Atribuir ID estável ao anexo, independente de nome e localização; associá-lo à operação. Saída: `AttachmentIdentified`. Proibido usar filename/path como identidade. Testes: mover/renomear preserva ID; colisão; retry da mesma operação não cria segundo anexo; receções independentes não são fundidas automaticamente. Persistência e replay desta atribuição: sujeitos a G10.

## IMP-005 — Colocar em quarentena

Entrada: anexo identificado. Copiar bytes para localização controlada, fechar a escrita, confirmar existência e tamanho básico antes de reconhecer conclusão. Não destruir entrada/original. Saída: `Quarantined(attachment_id, quarantine_ref)` ou falha explícita. Artefacto parcial comprovadamente criado pela operação pode ser removido apenas segundo contrato de recuperação; na dúvida, não apagar. Testes: sucesso; disco cheio; crash; escrita parcial; retry; original byte-a-byte intacto; quarentena sem recibo → reconciliação.

## IMP-006 — Calcular hash

Entrada: `Quarantined`. Ler sem modificar; calcular SHA-256 dos bytes completos e associar digest ao anexo. Saída: `HashCalculated(attachment_id, algorithm, digest)` ou falha de leitura explícita. Hash não autoriza eliminação. Testes: vetor conhecido; repetibilidade; mudança de um byte; vazio se aceite; falha de leitura; arquivo não modificado.

## IMP-007 — Verificar duplicação exata

Entrada: anexo e digest. Procurar digests coincidentes e verificar igualdade exata pelos critérios de bytes definidos; classificar `EXACT_DUPLICATE` com IDs correspondentes ou `UNIQUE_BINARY`. Um digest igual sozinho não é prova incondicional; ausência de coincidência não prova identidade semântica. Proibido deduplicar por embeddings/IA ou eliminar. Testes: bytes iguais; texto equivalente com bytes diferentes; paráfrase; mesmo nome e bytes diferentes; digest não encontrado; colisão simulada → não declarar igualdade sem verificação.

## IMP-008 — Identificar formato

Entrada: anexo em quarentena. Combinar evidências do conteúdo, MIME/assinaturas apropriadas; extensão é auxiliar. Saída: `FormatDetected(format, evidence)` ou `FORMAT_UNKNOWN`/inconsistência explícita. Testes: PDF renomeado `.txt`; DOCX; EPUB; imagem; sem extensão; assinatura inválida; conflito entre extensão e conteúdo. O grau de confiança e política de formatos ficam **POR DEFINIR**.

## IMP-009 — Selecionar adaptador

Entrada: formato identificado ou desconhecido. Consultar registo de capacidades autorizado, compatibilidade e regras; não instalar software nem improvisar fornecedor. Saída: `AdapterSelected(adapter_id, adapter_version, task_type)` ou encaminhamento explícito a revisão/falha conforme regra. Exemplos condicionais: PDF → adaptador configurado; DOCX/EPUB → Docling se configurado. Testes: disponível; indisponível; dois candidatos; versão incompatível; formato desconhecido. Prioridade e destino exato de casos sem adaptador: **POR DEFINIR**.

## IMP-010 — Criar tarefa

Entrada: operação, anexo e adaptador escolhido. Construir tarefa fechada com `task_id`, IDs, input autorizado, permissões mínimas, limites, timeout e contrato do resultado. Saída: `AdapterTask`; nenhum acesso global ao Cérebro. Testes: envelope completo; task ID único; retry sem duplicar tarefa lógica; ausência de campo obrigatório; privilégios excessivos rejeitados. Limites concretos: **POR DEFINIR**.

## IMP-011 — Executar adaptador

Entrada: `AdapterTask`. Executar somente a tarefa, com isolamento efetivo adequado ao risco; capturar versão, saída, código de saída e erros. Saída: `AdapterExecutionResult` explícito inclusive timeout/crash. Adaptador não acede diretamente aos cofres, SQLite, Markdown ou EventLog. Testes: sucesso; timeout; crash; saída enorme/malformada; tentativa de acesso proibido → bloqueio; ausência de falso sucesso. Modelo de sandbox e limites: **POR DEFINIR**.

## IMP-012 — Receber resultado

Entrada: output do adaptador. Receber como não confiável e correlacionar com `task_id`, `operation_id`, `attachment_id` e versão. Saída: `UntrustedAdapterResult` ou recusa explícita; ainda não é conhecimento. Testes: IDs certos; task errada; duplicado; resposta tardia; sem origem. Resposta tardia não substitui estado reconciliado nem contorna o orquestrador.

## IMP-013 — Validar envelope

Entrada: resultado não confiável. Validar schema/versionamento, IDs, estado, tamanho e campos obrigatórios antes de validar conteúdo. Saída: `EnvelopeValid` ou `EnvelopeInvalid`. JSON sintaticamente válido não é conhecimento persistível. Testes: schema correto; campo em falta; ID trocado; campo extra perigoso; payload truncado; versão incompatível. Schema exato: **POR DEFINIR**.

## IMP-014 — Validar conteúdo

Entrada: envelope válido e original acessível. Efetuar verificações estruturais e de coerência mensuráveis; detetar extrações vazias/incompletas quando possível, preservando avisos e evidência. Não prometer fidelidade perfeita: `sanity check ≠ prova de conversão perfeita`. Saída: `ContentValidation(evidence, warnings, failures)`. Testes: boa extração; vazia; página perdida detetável; estrutura inválida; tabela corrompida; conteúdo suspeito. Métricas e limiares: **POR DEFINIR**.

## IMP-015 — Classificar

Entrada: `ContentValidation`. Aplicar regras determinísticas configuradas: suficiente → `READY`; incerteza relevante → `REVIEW`; inutilizável → `FAILED`; sempre com razões. Não atribuir aprovação à IA. Saída: classificação de conteúdo, não commit. Testes: fronteiras; mesma entrada e mesmas regras → mesma classificação; ausência de evidência não gera READY; razões auditáveis. Critérios concretos: **POR DEFINIR**. Transições: READY → 016; REVIEW → 021; FAILED → 022.

## IMP-016 — Criar representação Creative

Entrada: exclusivamente `READY` válido com os IDs desta operação. Construir candidato a documento/blocos de trabalho com IDs estáveis e ligação ao anexo/original; não persistir fora da cadeia de eventos nem promover. Saída: candidato a persistência Creative. `REVIEW` não entra automaticamente neste IMP; eventual aceitação posterior requer contrato próprio. Testes: conteúdo e IDs; ligação ao original; nenhuma promoção; retry não duplica; REVIEW recusado.

## IMP-017 — Criar proveniência

Entrada: candidato de representação e cadeia da operação. Construir registo de origem, anexo, ferramenta/versão, transformação, operation ID e evidência relevante, permitindo traçar bloco → transformação → ferramenta → attachment → original. Saída: `ProvenanceRecord`. Testes: cadeia completa; ferramenta desconhecida; referência quebrada; evidência externa congelada para replay; nenhuma relação inventada.

## IMP-018 — Criar eventos necessários

Entrada: mutação Creative preparada e proveniência. Preparar eventos autoritativos versionados, com IDs e ordem determinísticos para aplicação e replay. Saída: lote válido de eventos, ainda distinguível de commit confirmado. Não chamar Web/IA/plugin no replay. Testes: schema/versão; ordem; duplicação; evento inválido; replay determinístico; evidência suficiente congelada. Aplicam-se também os eventos necessários às mutações autoritativas anteriores, conforme contrato G10 ainda **POR DEFINIR**.

## IMP-019 — Materializar estado

Entrada: eventos autoritativos válidos. Aplicar deterministicamente a SQLite/Markdown e produzir recibos; não pressupor atomicidade conjunta entre SQLite, filesystem e log. Saída: `MaterializationReceipt` ou `COMMITTED`/`NOT_COMMITTED`/`RECOVERY_REQUIRED` conforme evidência e protocolo. Um estado incerto bloqueia novas mutações. Testes: normal; crash antes/durante/depois; retry sem duplicação; recibo sem estado; hash do estado autoritativo canonizado igual ao replay. Protocolo de gravação/reconciliação: **POR DEFINIR**.

## IMP-020 — Atualizar derivados

Entrada: materialização confirmada. Atualizar FTS5/caches; se falhar, assinalar `DerivativesDirty` e permitir reconstrução sem alterar conhecimento autoritativo. Saída: `DerivativesUpdated` ou `DerivativesDirty`. Testes: FTS apagado; reconstrução; crash; índice corrupto; estado autoritativo inalterado. Política de exposição de pesquisa com índice sujo: **POR DEFINIR**.

## IMP-021 — Apresentar resultado

Entrada: resultado final de operação confirmada, `REVIEW`, falha, ou derivados sujos conforme estado permitido. Mostrar na Folha linguagem simples, por exemplo “Livro.epub — Importado” somente após commit confirmado, ou “Livro.epub — Precisa de verificação” em REVIEW. Não mostrar IDs/Markdown/SQL por defeito; apresentação não é aprovação. Testes: READY com commit; REVIEW sem Creative; falha sem falso “Importado”; original acessível segundo política; fechar/reabrir UI não altera estado; `DerivativesDirty` não apaga conteúdo.

## IMP-022 — Tratar falha

Entrada: falha de conteúdo de IMP-015 ou falha técnica de qualquer IMP. Identificar etapa e razões, preservar evidência necessária, impedir falso sucesso e determinar `FAILED`, `RETRYABLE` ou `RECOVERY_REQUIRED`. Não corrigir conteúdo silenciosamente. `RETRYABLE` requer prova de segurança e idempotência para a operação; incerteza sobre commit exige reconciliação. Saída: estado operacional e destino explícito para apresentação, retry autorizado ou IMP-023. Testes: falha de conteúdo versus técnica; vários pontos; erro desconhecido; retry; original preservado; nenhum status falso.

## IMP-023 — Reconciliar interrupção

Entrada: operação incompleta detetada no arranque ou verificação. Ler `operation_id`, eventos, recibos, materialização e artefactos; determinar `COMMITTED`, `NOT_COMMITTED` ou `RECOVERY_REQUIRED` sem chamar novamente adaptador/Web/IA. Neste último estado bloquear mutações até resolução fundamentada. Testes: crash em vários pontos; recibo sem estado; estado sem recibo; evento parcial; replay; idempotência; operação sem prova suficiente permanece bloqueada. Reconciliação tem de considerar mutações desde IMP-003, não apenas IMP-019.

## IMP-024 — Pedido de eliminação do original

Entrada: pedido explícito da pessoa relativo a anexo concreto, posterior e separado da importação. Resolver ID e alvo, verificar existência, referências e consequências; apresentar proposta precisa. Saída: `DeletionProposal`; nada é eliminado. Testes: existente; inexistente; várias referências; duplicado binário exato; semelhante semanticamente; ambiguidades não adivinhadas. Retenção legal/backup e política de ficheiros: **POR DEFINIR**.

## IMP-025 — Autorização humana

Entrada: proposta e decisão humana explícita. Confirmar alvo, contexto e atualidade; registar decisão autoritativa. Saída: `DeletionApproved` ou `DeletionRejected`. Silêncio, timeout, plugin e IA nunca aprovam. Testes: aprovação; rejeição; proposta expirada; ID divergente; duplo clique; decisão repetida; aprovação não alargada a outros anexos.

## IMP-026 — Eliminação autorizada

Entrada: aprovação válida e específica. Revalidar autorização e alvo, usar operação identificada, eliminar exclusivamente o original autorizado, preservar genealogia/eventos/conhecimento que devam sobreviver e produzir recibo; falha não é sucesso. Saída: `OriginalDeleted` ou estado recuperável/bloqueado. Testes: eliminação correta; crash; alvo desaparecido; autorização reutilizada recusada; referências coerentes; Creative/Canonical não eliminados; nenhum outro attachment afetado. Precisar o significado operacional de “original” quando há entrada, quarentena e cópias de backup: **POR DEFINIR** antes da implementação.

## Orquestração e portões

Um IMP não chama arbitrariamente outro. Recebe a entrada contratada e produz saída tipada/falha. O orquestrador verifica IDs, estado e regras e só então escolhe a transição permitida. Caminhos de falha/reconciliação são transversais; IMP-024–026 não são continuação automática de IMP-021.

Portão 1 — **Especificação verificada**: casos, pré-condições, saídas, transições, idempotência, falhas e invariantes são revistos sequencialmente para cada IMP. Se algum ponto estiver POR DEFINIR e for necessário para decidir comportamento, o portão permanece fechado; corrigir e repetir antes do próximo IMP.

Portão 2 — **Implementação testada**: só se atribui após escrever e executar testes reais com sucesso. Nada neste documento declara testes executados ou autoriza programar lacunas.

Cabeçalho obrigatório de tarefa futura:

```
text
```

`ARQUITETURA: CONGELADA ESCOPO: Implementar exclusivamente IMP-XXX. NÃO AUTORIZADO: alterar arquitetura; implementar IMP futuros; criar decisões  de negócio; alterar T1–T6; substituir tecnologias sem autorização;  refatorar módulos fora do escopo; interpretar ambiguidades silenciosamente. SE A ESPECIFICAÇÃO FOR INSUFICIENTE: PARAR, identificar exatamente  a informação em falta, não inventar comportamento. PORTÃO: testes do IMP atual passam antes do seguinte.`

A família está consolidada como especificação funcional corrigida. Os pontos **POR DEFINIR** são lacunas explícitas que têm de ser decididas e testadas antes de declarar cada contrato pronto para programação. Não equivale a aprovação da implementação, nem a fecho do Catálogo Mestre de todas as famílias do Cérebro.

---

# PARTE IV — INSTRUÇÃO FINAL AO CURSOR

1. Lê este ficheiro inteiro antes de modificar código.
2. Não redesenhes a arquitetura por conveniência.
3. Antes de cada tarefa, declara `IMP/Bloco`, pré-condições, ficheiros a tocar e testes a executar.
4. Não implementes IMP futuros “porque é mais fácil”.
5. Se encontrares contradição documental, não escolhas silenciosamente: preserva as duas referências e pede decisão quando a diferença for normativa.
6. Se encontrares bug técnico cuja correção não altera norma/arquitetura, corrige no escopo mínimo e testa.
7. Se encontrares uma solução melhor que altera uma decisão arquitetónica, apresenta-a como PROPOSTA separada; não a implementes sem autorização.
8. Mantém commits pequenos e reversíveis, idealmente um IMP/bug por commit.
9. Cada PASS deve apontar para execução real do teste; nunca inferir PASS por inspeção visual do código.
10. Depois de cada IMP, corre regressão de tudo o que possa ter sido afetado.
11. Depois de cada bloco, executa testes adversariais de autoridade e recuperação.
12. Antes de declarar release funcional, executa T1–T6, E2E-01–15 e matriz M1–M14.
13. O objetivo dos testes é tentar provar que o sistema está errado. Se não conseguires quebrá-lo dentro do conjunto testado, regista apenas essa evidência — não declares infalibilidade.

**COMANDO DE ARRANQUE:** não programes imediatamente. Primeiro audita o repositório atual contra esta especificação, produz a matriz `EXISTE / PARCIAL / AUSENTE / CONTRADIZ / POR DEFINIR`, identifica o primeiro IMP implementável sem decisão normativa pendente e propõe o plano mínimo para o implementar e testar. Só depois começa a alteração de código.
