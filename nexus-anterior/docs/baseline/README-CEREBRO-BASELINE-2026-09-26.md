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
