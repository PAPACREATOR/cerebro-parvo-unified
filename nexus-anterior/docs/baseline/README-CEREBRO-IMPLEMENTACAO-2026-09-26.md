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
