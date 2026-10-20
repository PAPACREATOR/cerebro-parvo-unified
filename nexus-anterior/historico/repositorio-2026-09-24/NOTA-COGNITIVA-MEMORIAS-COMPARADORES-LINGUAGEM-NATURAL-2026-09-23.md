# Nota cognitiva — memórias, comparadores e linguagem natural

Data: 2026-09-23  
Estado: **clarificação conceptual de Pedro; referência futura. Não altera F0-001 nem autoriza implementação.**

## Correção essencial

A **linguagem natural pertence à superfície Logseq/cofre criativo**. É aí que a pessoa escreve normalmente.

Não interpretar “linguagem natural” como um quarto comparador, quarta memória ou autoridade adicional.

```text
Pessoa
  ↓ linguagem natural
Logseq Classic / cofre criativo
  ↓
representação/adaptação controlada
  ↓
núcleo e restantes mecanismos
```

A pessoa não precisa de escrever Markdown, SQL, YAML ou comandos técnicos.

## Três funções de memória — modelo conceptual

1. **Working Memory** — contexto/estado temporário necessário ao ciclo atual.
2. **Behavioral/Procedural Memory** — regras, preferências e comportamento confirmado, versionado e auditável.
3. **Persistent Knowledge Memory** — conhecimento persistente.

A terceira função não elimina a arquitetura de dois cofres:
- criativo/Logseq = conhecimento em evolução/candidato;
- final separado = conhecimento aprovado/canónico.

EventLog, snapshots, RAW/Candidate e SQLite não devem ser renomeados automaticamente como novas “memórias”; têm contratos técnicos próprios.

## Três formas de comparação

### 1. Matemática/determinística
Compara estados, valores, regras formais, hashes, versões, limites, invariantes e consistência mecanicamente verificável.

### 2. Semântica
Compara significado, conceitos, equivalências, incompatibilidades, contexto e possíveis contradições de sentido. Quando exigir IA, o resultado é proposta/evidência, nunca verdade automática.

### 3. Relacional — grafo/wiki
Compara posição e relações no conhecimento: nós, blocos, referências, backlinks, vizinhança, caminhos e ligações entre conceitos/projetos/fontes. Aproveitar primeiro capacidades nativas do Logseq/File Graph; não reconstruir um grafo paralelo sem necessidade demonstrada.

## Dois regimes de processamento

**Determinístico:** regras, eventos, estado, cálculo, validação, replay, segurança e promoção mecânica.

**Criativo/associativo:** escrita no Logseq, relações exploratórias, hipóteses, brainstorming e IA apenas quando necessária.

A metáfora “lado esquerdo/lado direito” é apenas de engenharia. Não é afirmação neurocientífica.

## Autoridade

O humano continua acima dos dois regimes.

```text
                    HUMANO
             autoridade canónica
                    │
       ┌────────────┴────────────┐
       │                         │
determinístico             criativo/associativo
       │                         │
       └──────── candidato ──────┘
                    │
          decisão humana explícita
                    │
              cofre final
```

Nenhuma concordância entre os três comparadores promove conhecimento automaticamente.

## Auto-cura

Auto-cura significa restaurar propriedades verificáveis, não inventar verdade:

```text
estado observado
   ↓
matemática + semântica + grafo/wiki
   ↓
divergência detetada
   ↓
causa/reparação conhecida?
   ├─ sim → reparar de forma controlada → repetir verificações
   └─ não → HumanDecisionRequest
```

Exemplos potencialmente automáticos: reconstruir índice/projeção, reconciliar espelho segundo contrato, repetir operação idempotente, restaurar snapshot/replay, corrigir metadata mecanicamente demonstrável.

Não automático: escolher entre interpretações contraditórias, declarar hipótese como facto, alterar significado, promover conhecimento ou apagar conteúdo canónico fora da política explícita.

Regra curta:

`AUTO-CURA ≠ AUTO-VERDADE`

## Relação entre os eixos

Não multiplicar isto em nove motores. São dimensões ortogonais que podem ser consultadas conforme a necessidade:

```text
TIPO DE MEMÓRIA
Working | Behavioral | Persistent knowledge

FORMA DE COMPARAÇÃO
Matemática | Semântica | Grafo/wiki

REGIME
Determinístico | Criativo/associativo

AUTORIDADE
Humano
```

## Precedentes a estudar, não copiar

Soar, ACT-R, CLARION, LIDA, motores de regras/state machines/event sourcing, OpenViking/VikingMem e projetos deterministic-first recentes mostram precedentes para peças isoladas. A hipótese distintiva do Cérebro Independente está na composição, fronteiras de autoridade e uso conjunto das peças — não em alegar que cada mecanismo isolado é novo.

Aplicar sempre:

`USE → ADAPT → CREATE`

## Limite desta nota

Esta nota preserva a clarificação conceptual para comparação e futuras SPECs. Não muda a arquitetura congelada, não altera o contrato dos dois SQLite, não introduz Go nem qualquer novo runtime, e não autoriza Copilot/Codex a implementar estas ideias fora da SPEC ativa.
