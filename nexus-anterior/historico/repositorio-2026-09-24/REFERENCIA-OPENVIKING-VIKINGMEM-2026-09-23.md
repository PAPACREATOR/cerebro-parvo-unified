# Referência técnica — OpenViking / VikingMem

Data: 2026-09-23  
Estado: **referência para comparação futura; não altera a arquitetura nem autoriza adoção.**

## O que é

**OpenViking** é uma base de contexto open source iniciada e mantida pela equipa Viking da ByteDance/Volcano Engine. Organiza recursos, memórias e skills num filesystem virtual `viking://`, com recuperação semântica e carregamento progressivo de contexto.

**VikingMem** (2026) é o trabalho académico associado sobre uma *Memory Base* para aplicações LLM com estado. Usa eventos e entidades, extração seletiva, evolução de memória e recuperação temporal. OpenViking disponibiliza apenas parte destas capacidades.

Fontes primárias:
- https://github.com/volcengine/OpenViking
- https://github.com/volcengine/OpenViking/blob/main/docs/en/getting-started/01-introduction.md
- https://arxiv.org/abs/2605.29640
- Integração real no DeerFlow: https://github.com/bytedance/deer-flow/blob/main/docs/OPENVIKING.md

## O que interessa ao Cérebro Independente

### 1. Hierarquia + leitura progressiva

OpenViking usa três níveis:
- L0 — resumo curto para filtragem;
- L1 — overview para navegação;
- L2 — conteúdo original completo.

Ideia reutilizável: consultar primeiro representações pequenas e só carregar detalhe quando necessário. Pode reduzir contexto, I/O e chamadas de IA.

**Não copiar automaticamente:** no Cérebro, o conhecimento aprovado continua sujeito aos contratos dos dois cofres e à autoridade humana.

### 2. Separação conteúdo / índice

A arquitetura OpenViking separa armazenamento de conteúdo do índice vetorial. Isto reforça um princípio útil: índice e conteúdo não devem ser confundidos com autoridade semântica.

É comparável, mas não equivalente, à nossa separação entre representações persistentes e estruturas computacionais SQLite.

### 3. Identidade e caminhos

OpenViking dá URIs estáveis de navegação e IDs derivados para indexação. A ideia útil é separar identidade lógica de apresentação/nome do ficheiro.

No nosso sistema, não copiar o algoritmo de ID sem análise: já existe requisito de identidade/eventos determinísticos e o contrato final ainda é nosso.

### 4. Parsing separado da semântica

No OpenViking, parsing/estruturação pode ocorrer sem LLM; geração semântica é posterior e assíncrona.

Isto encaixa diretamente no princípio do projeto:
`determinístico primeiro → IA apenas quando necessária`.

### 5. Sessões, commit e recuperação

A integração OpenViking do DeerFlow mantém identidade estável de sessão, progresso parcial, retries e políticas explícitas de falha. A própria documentação alerta que, quando perder uma atualização é inaceitável, continua a ser necessário um **durable outbox**.

Isto é evidência externa favorável à decisão já tomada para F3: outbox/retry e estados explícitos. Não é motivo para substituir Activepieces ou o EventLog do núcleo.

### 6. Proveniência e apagamento

OpenViking possui operações de alteração/apagamento, incluindo `forget`. O DeerFlow avisa que `forget` elimina permanentemente e deve exigir confirmação.

No Cérebro Independente a regra é mais restritiva: esta referência **não altera** a política de aprovação humana nem autoriza apagamento automático do conhecimento consolidado.

## Diferenças estruturais

| Tema | OpenViking/VikingMem | Cérebro Independente |
|---|---|---|
| Objetivo | infraestrutura de contexto/memória para agentes | sistema pessoal determinístico e humano-no-loop |
| Memória | extração/evolução automática orientada a agentes | dois cofres com promoção humana para o final |
| Organização | filesystem virtual `viking://` | Logseq/File Graph + cofre final separado |
| Pesquisa | recuperação híbrida/semântica | arquitetura própria; pesquisa externa via fluxo controlado |
| IA | componente importante da extração semântica | efémera, opcional e subordinada |
| Execução | SDK/API/integrações de agentes | Activepieces + núcleo Python |
| Autoridade | política da aplicação/backend | Pedro é autoridade final |
| Replay | não assumir equivalência | requisito explícito do núcleo determinístico |

## O que vale estudar/reutilizar

1. L0/L1/L2 como padrão de recuperação progressiva.
2. Separação parsing determinístico / enriquecimento semântico.
3. Estrutura hierárquica como contexto para retrieval.
4. IDs/URIs e resolução de escopo — apenas como referência para o nosso contrato de identidade.
5. Testes de sessão, retries, falhas parciais e reinício.
6. Estratégias de redução de contexto.
7. Benchmarks/metodologia do VikingMem para futura avaliação de memória.

## O que NÃO importar

- Não substituir Logseq pelo OpenViking.
- Não substituir os dois cofres.
- Não substituir os dois SQLite sem SPEC e decisão explícita.
- Não permitir consolidação automática de IA no cofre final.
- Não importar esquecimento/fading automático para conhecimento aprovado.
- Não introduzir vector DB apenas porque OpenViking o usa.
- Não transformar a arquitetura num agente autónomo.
- Não adicionar esta tecnologia ao runtime antes de uma microtarefa demonstrar necessidade.

## Decisão provisória

**Referência técnica forte; dependência atual: NÃO.**

OpenViking/VikingMem valida várias escolhas de engenharia já presentes — hierarquia, contexto progressivo, eventos, separação de etapas e necessidade de recuperação explícita — mas resolve um problema diferente e aceita mais automatismo sobre memória do que o Cérebro Independente.

Aplicar a regra do projeto:

`USE → ADAPT → CREATE`

Se uma futura SPEC precisar de retrieval/contexto/memória, consultar esta referência antes de programar. Reutilizar uma ideia ou componente apenas se reduzir complexidade total e preservar determinismo, proveniência, aprovação humana e os contratos dos dois cofres.
