# Fase seguinte — Linguagem Natural -> Parser -> Markdown -> Processo

Data: 2026-10-04
Estado: fase por afinar depois de Kernel + Spiff + Conductor.
Este documento organiza trabalho futuro; não altera leis nem arquitetura congelada.

## Objetivo

Permitir que a Folha aceite linguagem natural normal sem exigir ao utilizador conhecer
YAML, JSON, IDs, processos ou motores.

Fluxo alvo:

`texto humano -> preservação literal -> parser determinístico -> ELIZA/regras de diálogo -> objeto Markdown -> seleção de processo -> JSON de execução -> Kernel`

A autoridade continua no Kernel.

## Princípios já existentes que esta fase deve respeitar

1. Markdown = representação humana/conhecimento/objetos.
2. YAML = definição de processos/workflows.
3. JSON = envelope de execução/transferência.
4. Texto original é sempre preservado.
5. Parser não promove conhecimento.
6. ELIZA não decide verdade, política, IA, Canonical, retry nem permissões.
7. Tiny/IA só entra depois, se o Kernel autorizar e apenas quando regras determinísticas não chegam.
8. Os 7 prefixos continuam como fast-path explícito:
   - `@@` arquivo
   - `@` web
   - `""` fontes
   - `&` trabalhar
   - `??` perguntar
   - `%` calcular
   - `#` tema

## Camadas

### N0 — Raw input

Entrada:
- texto UTF-8 da Folha;
- anexo opcional;
- prefixo opcional.

Guardar:
- bytes/texto original;
- hash;
- data;
- operation_id.

Nunca normalizar destrutivamente o original.

### N1 — Fast parser

Primeira passagem sem ELIZA e sem IA.

Funções:
- detectar um dos 7 prefixos;
- separar prefixo do conteúdo;
- reconhecer comandos exatos/aliases permitidos;
- validar tamanho/codificação;
- reconhecer anexos;
- rejeitar syntax claramente inválida.

Saída:
- intent explícito quando inequívoco;
- ou `UNRESOLVED`.

### N2 — ELIZA determinística

Só recebe pedidos ainda não resolvidos ou pedidos conversacionais permitidos.

Função:
- pattern matching;
- regras de transformação;
- extração de slots;
- perguntas de clarificação determinísticas;
- sinónimos/variações simples;
- converter linguagem corrente numa intenção candidata.

Exemplos:
- "guarda isto" -> candidato `arquivo`;
- "procura isto na net" -> candidato `web`;
- "trabalha este texto" -> candidato `trabalhar`;
- "quanto é..." -> candidato `calcular`.

ELIZA não precisa saber se o backend posterior é:
- Python;
- PowerShell;
- Spiff;
- Conductor;
- Open Notebook;
- Tiny;
- outra IA.

Tal como Spiff, pede uma capacidade abstrata. O Kernel resolve.

### N3 — Objeto Markdown como molde

Depois de a intenção estar resolvida, gerar um objeto Markdown simples e auditável.

Exemplo interno:

```markdown
---
tipo: pedido
intencao: trabalhar
estado: READY
origem: folha
parser: eliza-rules-v1
---

## Pedido original

<texto literal>

## Interpretação

<slots extraídos/regras aplicadas>
```

Este Markdown:
- não é Canonical;
- não concede permissões;
- conserva o original;
- pode viver em Creative/estado de trabalho conforme o processo;
- é legível por humano;
- pode ser convertido para o envelope JSON de execução.

A estrutura deve aproveitar o contrato já provado em F009:
Markdown UTF-8 + YAML inicial + notas/corpo, com validação estrita.

### N4 — Resolver processo

O Kernel recebe:
- intenção validada;
- objeto Markdown;
- contexto mínimo;
- capability pedida.

O Kernel escolhe:
- processo YAML;
- Spiff, Conductor ou ambos;
- limites;
- permissões;
- se IA é ou não permitida.

O parser/ELIZA nunca escolhe autoridade.

### N5 — JSON de execução

O Kernel materializa o pedido de execução em JSON validado.

Não transformar Markdown em YAML de processo.
O YAML continua a ser definição versionada do processo; o Markdown descreve o pedido humano.

## Ordem de preferência

1. Prefixo explícito.
2. Regra exata determinística.
3. ELIZA/patterns.
4. Clarificação humana.
5. Tiny local opcional, apenas se processo autorizado e realmente necessário.

A IA não é fallback automático para qualquer frase.

## O papel de ELIZA

ELIZA é interessante aqui precisamente porque:
- é pequena;
- local;
- auditável;
- regras visíveis;
- sem modelo permanente;
- funciona com hardware fraco;
- pode produzir comportamento conversacional suficiente para pedidos simples.

Mas deve ser usada como:
`parser conversacional + clarificador + matcher`.

Não como:
- memória;
- RAG;
- agente soberano;
- classificador sem limites;
- fonte de verdade;
- substituto do Kernel.

## Testes por fases

### L0 — 100 casos prefixados
Cada prefixo + Unicode + espaços + anexos.
Esperado: 100% determinístico.

### L1 — 1000 variações naturais
Frases equivalentes, erros ortográficos leves e ordem variável.
Comparar intenção esperada vs intenção extraída.

### L2 — 1000 ambiguidades
Pedidos deliberadamente ambíguos.
Esperado: `UNRESOLVED` ou pergunta de clarificação; nunca ação inventada.

### L3 — 1000 adversariais
Prompt injection, texto que contém prefixos como dados, Markdown/YAML malicioso, comandos embebidos.
Esperado: original preservado, nenhuma ampliação de capacidade.

### L4 — 1000 round-trips
`texto -> parser -> Markdown -> JSON -> Kernel -> resultado -> proveniência -> texto original`.

### L5 — 1000 replay/restart
Novo Kernel reproduz objeto/processo sem reinterpretar texto nem chamar IA/ELIZA para fabricar passado.

### L6 — comparação ELIZA vs parser puro
Medir:
- cobertura;
- falsos positivos;
- ambiguidades;
- velocidade;
- regras necessárias;
- manutenção.

Só manter ELIZA onde acrescentar valor mensurável.

## Critérios

PASS:
- intenção correta ou ambiguidade explicitamente conservada;
- original byte-for-byte preservado;
- Markdown válido;
- JSON válido;
- processo escolhido pelo Kernel;
- proveniência fecha ida/volta;
- nenhuma permissão ampliada.

FAIL:
- interpretação silenciosa errada;
- alteração do original;
- ação numa ambiguidade;
- parser/ELIZA escolhe backend ou autoridade;
- processo não versionado;
- replay volta a interpretar o passado.

## Relação com trabalho já feito

- F009 fornece a base de objetos Markdown estritos.
- F010 demonstra que linguagem/prompt nunca substitui comparador determinístico.
- F005 mostra onde cognição Tiny pode entrar depois, como capability opcional.
- Kernel + Spiff + Conductor fornece a execução por trás do pedido.
- Esta fase fecha a ponte entre a linguagem humana da Folha e esses processos.

## Sequência

1. terminar caracterização Kernel/Spiff/Conductor;
2. congelar contratos de dispatch;
3. implementar N0/N1;
4. testar parser puro;
5. adicionar ELIZA mínima;
6. comparar parser puro vs ELIZA;
7. materializar Markdown;
8. ligar JSON -> Kernel;
9. 5000+ testes por fases;
10. só depois considerar Tiny como fallback excepcional.
