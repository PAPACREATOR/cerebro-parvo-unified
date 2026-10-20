# Projeto final auditado — composição mínima governada

Data: 28-09-2026.

Estado: **arquitetura operacional fechada**. O produto completo continua por provar E2E.

## 1. Objetivo

Entregar a experiência de um “cérebro digital” simples para uma pessoa não técnica sem reconstruir ferramentas maduras.

O utilizador escreve em linguagem natural numa interface principal. O sistema escolhe capacidades, executa processos nos bastidores, apresenta o resultado e pede decisão humana apenas quando a autoridade o exige.

O utilizador não precisa de ver flows, tabelas, Markdown, IDs, SQL, MCP, APIs, prompts internos ou aplicações auxiliares.

## 2. Arquitetura final

~~~mermaid
flowchart TD
    P[Pessoa] --> UI[Activepieces WebUI / Chat UI]
    UI --> R[Regras + estado + flows]
    R --> AP[Activepieces]
    AP --> ON[Open Notebook + uma tiny parametrizada]
    AP --> KG[K-DLC ou outro provider de knowledge governance]
    AP --> Z[Zotero]
    AP --> LO[LibreOffice]
    AP --> PX[Pinokio -> providers locais]
    AP --> OT[Outras Pieces / MCP / API / CLI]
    ON --> U[Resultados]
    KG --> U
    Z --> U
    LO --> U
    PX --> U
    OT --> U
    U --> CR[Creative]
    CR --> H[Human Gate]
    P --> H
    H --> CA[Canonical / ação autorizada]
~~~

A frase operacional é:

**A pessoa manda; Activepieces liga; providers trabalham; Open Notebook pensa quando necessário; Creative preserva; Human Gate decide; Canonical guarda o aprovado.**

## 3. O que constitui o Cérebro

### Três memórias

1. Working Memory — estado transitório da tarefa.
2. Behavioral/Procedural Memory — regras, preferências, correções e rotinas versionadas.
3. Persistent Knowledge Memory — conhecimento duradouro dividido por autoridade.

Não são três bases de dados nem três aplicações.

Implementação inicial preferida:

- Working -> flow state + Tables/Storage;
- Behavioral -> Tables/configuração versionada;
- Persistent -> Creative/Canonical + provider de knowledge governance quando útil.

### Dois cofres

- Creative: hipóteses, rascunhos, alternativas, contradições, rejeições e resultados ainda não promovidos;
- Canonical: conhecimento atualmente aprovado pela pessoa.

Promoção nunca apaga Creative nem genealogia.

### Três comparadores

- determinístico: igualdade, hashes, datas, valores, estados, regras, idempotência;
- relacional: fontes, backlinks, versões, genealogia, dependências e relações;
- semântico: significado, equivalência possível, incompatibilidade e contradição candidata.

Podem usar providers diferentes. O flow cruza resultados; nenhum comparador é autoridade.

### M1–M14

Mantêm-se como responsabilidades/invariantes. Não obrigam a 14 serviços, módulos ou processos.

## 4. Activepieces é a plataforma principal

Usar o que já existe:

- Chat UI/Human Input;
- flows;
- routers/branches;
- Subflows;
- Tables;
- Storage;
- MCP;
- Pieces;
- waits/approvals quando aplicáveis;
- triggers/schedules;
- execução e logs.

Por isso deixam de ser pressupostos:

- frontend próprio;
- workflow engine próprio;
- capability registry programado;
- base simples própria;
- sistema de retries próprio;
- catálogo de integrações próprio.

O registo conceptual pode ser apenas uma tabela:

`CAPACIDADE -> PROVIDER`.

## 5. Open Notebook é a bancada cognitiva

Open Notebook entra apenas quando a tarefa beneficia de pesquisa semântica, interpretação, transformação ou síntese.

Usar uma única tiny/modelo reutilizável.

O papel muda por parâmetros:

`tema + objetivo + fontes + regras + permissões + budget + schema`.

Não criar um agente permanente por domínio.

A saída regressa ao flow. Open Notebook não é autoridade, não promove Canonical e não substitui memória persistente.

## 6. Providers especializados

### Knowledge governance

Preferência: K-DLC quando a implementação disponível cumprir os contratos.

Funções potenciais:

- proveniência;
- relações;
- conflitos;
- drafts/overlay;
- revisão;
- publicação governada;
- índices derivados;
- recuperação;
- MCP.

Contudo a especificação K-DLC 0.2.0 está marcada “Draft for implementation”. Portanto é provider opcional/substituível, nunca fundamento impossível de trocar.

### Referências

Zotero fornece biblioteca, metadados, anexos e referências. A API local permite integração sem obrigar o utilizador a operar Zotero durante o flow.

### Documentos

LibreOffice opera headless/API para criar, abrir, converter e exportar documentos e folhas.

### Multimédia local

Pinokio serve para instalar/arrancar ferramentas locais.

Um provider como ComfyUI pode expor geração de imagem/multimédia por API. Música/áudio usa o mesmo padrão com provider local escolhido posteriormente.

### Publishing

Usar Pieces/APIs existentes conforme o destino. Publicação é sempre ação separada e sujeita às regras humanas aplicáveis.

## 7. Pesquisa

Não construir “um supermotor”.

Três caminhos independentes:

```
TEXT/DETERMINISTIC -> filtros/FTS/provider disponível
RELATIONAL         -> relações/backlinks/K-DLC/tabelas
SEMANTIC           -> Open Notebook
```

O resultado agregado é o contrato; a implementação pode mudar.

SQLite próprio entra apenas se as capacidades existentes não conseguirem cumprir pesquisa, relações, eventos ou recuperação exigidos.

## 8. Human Gate e autoridade

Regra central:

**nenhuma IA, Piece, provider, flow, relógio ou autosave decide autoridade.**

As operações podem ser automáticas dentro de autorização prévia e escopo definido.

Quando uma ação exige decisão atual:

`proposta -> apresentação -> decisão humana -> execução`.

Creative -> Canonical é o caso principal.

## 9. Persistência e recuperação

O writer recuperável Python já implementado permanece preservado e testado como fallback técnico.

Não é obrigatório usá-lo no MVP se Activepieces/providers conseguirem preservar o comportamento exigido.

Qualquer solução escolhida deve ainda provar:

- estado não perdido após restart;
- idempotência quando aplicável;
- divergência detectável;
- replay sem reinvocar IA/Web para inventar evidência;
- backup + restore demonstrado.

Implementação muda; invariantes não.

## 10. O que não construímos

Por defeito não construir:

- frontend;
- editor de notas;
- workflow engine;
- RAG/vector DB próprio;
- multiagente;
- motor de pesquisa único;
- gerador de imagem;
- gerador de música;
- gestor bibliográfico;
- suite de documentos;
- publishing engine;
- base de dados própria além do que a necessidade provar;
- adaptadores quando Piece/MCP/API/CLI resolve.

## 11. Experiência desejada

Exemplo:

> “Usa estes documentos, compara com o que já sabemos, encontra contradições, prepara um artigo e uma imagem e deixa tudo pronto; não publiques.”

O sistema pode internamente:

1. receber pelo Chat UI;
2. consultar memória/regras;
3. recuperar referências;
4. usar pesquisa textual/relacional;
5. chamar Open Notebook se necessário;
6. produzir documento;
7. gerar imagem;
8. guardar proposta em Creative;
9. apresentar o resultado;
10. parar antes de publicar;
11. publicar apenas após decisão humana.

O utilizador vê pedido, progresso útil, resultado e decisões necessárias — não o encadeamento técnico.

## 12. Compatibilidade atual

Verificada documentalmente:

- Activepieces: adequada como UI/orquestrador/estado inicial;
- Open Notebook: adequada como capacidade cognitiva via REST;
- Zotero: adequada via API local;
- LibreOffice: adequado headless/API;
- Pinokio: adequado para instalar/arrancar serviços locais;
- ComfyUI: adequado como provider API para imagem/multimédia;
- K-DLC: alinhamento muito forte, mas maturidade ainda insuficiente para dependência obrigatória.

A integração real destes componentes ainda é NOT RUN.

## 13. Regra definitiva de engenharia

**LIGAR > CONFIGURAR > ADAPTAR > CRIAR.**

Antes de escrever código:

1. existe função nativa Activepieces?
2. existe Piece?
3. existe MCP?
4. existe API/CLI madura?
5. Tables/Storage já resolvem?
6. provider existente já resolve?
7. só então adaptar/criar o mínimo comprovadamente necessário.

## 14. MVP

O MVP não é “todos os providers instalados”.

É apenas:

`Activepieces WebUI -> regras/tabelas -> uma capacidade -> Creative -> Human Gate -> Canonical`.

Depois ligar Open Notebook.

Depois ligar capacidades externas uma a uma.

Se esta vertical slice funcionar repetidamente sem expor complexidade técnica ao utilizador, existe produto.

## 15. Arquitetura fechada

Esta arquitetura só reabre por:

- decisão humana explícita; ou
- falha estrutural observada em teste real.

A disponibilidade de uma ferramenta nova não obriga redesenho: normalmente apenas muda o provider de uma capacidade.

[Constituição](../CEREBRO_CONSTITUTION.md) · [Arquitetura](../CEREBRO_ARCHITECTURE.md) · [Compatibilidade](../COMPATIBILITY-MATRIX.md) · [Plano](../IMPLEMENTATION_PLAN.md) · [Estado](../STATUS.md)
