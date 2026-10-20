# Nota arquitetural — Escalada de resolução integrada

Data: 2026-09-23
Estado: **DESIGNED / hipótese arquitetural a validar**
Âmbito: clarificação do comportamento integrado do sistema. **Não altera nem expande a SPEC-F0-001 ativa.**

## Princípio

O utilizador comunica e decide em **linguagem natural**. Não escolhe comparadores, motores, bases de dados, pesquisas ou modelos.

O Cérebro Independente tenta resolver cada problema usando primeiro as capacidades internas já disponíveis. Só escala quando não consegue resolver com informação/capacidade suficiente.

A Web e a LLM **não são fluxos separados do sistema**: são capacidades que o próprio sistema pode convocar quando necessárias.

## Ciclo de resolução

```text
PEDIDO HUMANO EM LINGUAGEM NATURAL
              |
              v
       ESTADO + MEMÓRIAS
              |
              v
       REGRAS / LEIS
              |
              v
       COMPARAÇÃO INTERNA
              |
              v
        CONSEGUE RESOLVER?
          /          \
        SIM          NÃO
         |            |
         v            v
   RESULTADO       PREPARAR O QUE JÁ SE SABE
                      |
                      +-- objetivo
                      +-- regras aplicáveis
                      +-- factos relevantes
                      +-- relações relevantes
                      +-- contradições/incertezas
                      +-- limites/permissões
                      +-- pergunta concreta ainda por resolver
                      |
                      v
                    LLM
        "Com estas regras e esta informação,
             consegues resolver isto?"
                      |
                 CONSEGUE?
                  /    \
                SIM    NÃO
                 |      |
                 v      v
             VALIDAR   IDENTIFICAR O QUE FALTA
                         |
                         v
                     WEB / FONTE EXTERNA
                         |
                         v
                  RESULTADOS + PROVENIÊNCIA
                         |
                         v
                    VOLTAR AO SISTEMA
                         |
                         v
              "Agora consegues resolver?"
                         |
                   repetir com limites
                         |
              +----------+----------+
              |                     |
           RESOLVE                 NÃO RESOLVE
              |                     |
              v                     v
          VALIDAR               ESCALAR /
          RESULTADO             PEDIR HUMANO
```

## Regra de economia

A ordem conceptual é:

```text
usar o que já existe
→ resolver deterministicamente o que for possível
→ pedir à LLM apenas a parte que falta
→ pesquisar externamente apenas quando falta informação
→ devolver os novos resultados ao processo
→ escalar modelo/capacidade apenas se continuar necessário
→ pedir decisão humana quando regras, evidência ou autoridade não chegam
```

Não existe obrigação de chamar IA, Web ou qualquer outro recurso em cada pedido.

## Papel da LLM

A LLM não recebe por defeito todo o cofre nem toda a pergunta sem preparação.

Quando necessária, recebe **contexto mínimo suficiente**, construído a partir do estado conhecido:

```text
LLM_INPUT =
    objetivo
  + microproblema atual
  + regras aplicáveis
  + factos/fontes relevantes
  + relações relevantes
  + contradições/incertezas
  + permissões/limites
  + formato de resposta necessário
```

A LLM pode:

- resolver a ambiguidade restante;
- produzir uma hipótese/proposta;
- indicar explicitamente que não consegue resolver;
- indicar qual informação concreta falta.

A resposta da LLM não se torna automaticamente verdade nem conhecimento final. Volta ao sistema para validação e, quando aplicável, decisão humana.

## Papel da Web/pesquisa externa

A pesquisa externa é uma **capacidade de resolução**.

Não existe a regra “pesquisar sempre”. O sistema pesquisa quando o problema não pode ser resolvido porque falta informação atual ou externa.

Fluxo preferido:

```text
não resolvido
→ identificar lacuna
→ pesquisar a lacuna
→ recolher resultados + fonte + data + proveniência
→ voltar a comparar/validar
→ entregar resultados à LLM se a interpretação continuar necessária
→ tentar novamente
```

A Web é fonte de evidência, não autoridade canónica.

```text
WEB != VERDADE
LLM != VERDADE
RESULTADO DE COMPARADOR != VERDADE ABSOLUTA
```

Conteúdo externo continua a respeitar a fronteira RAW/Candidate e a regra de aprovação humana antes do cofre final.

## Comparadores e linguagem natural

Os comparadores são mecanismos internos. O utilizador não deve dizer “usa o comparador matemático/semântico/grafo”.

A interface continua:

```text
Humano: "Consegues resolver isto?"
Sistema: tenta resolver.
Sistema: usa internamente os mecanismos necessários.
Sistema: responde em linguagem natural.
```

A hipótese atual mantém três famílias de comparação a validar:

1. determinística/matemática;
2. semântica;
3. relacional/grafo.

O número exato e a utilidade independente de cada família continuam sujeitos a prova formal, testes de ablação e benchmark. Esta nota não os declara validados.

## Escalada por recursos

O mesmo princípio deve adaptar-se ao hardware disponível.

Exemplo conceptual:

```text
núcleo determinístico
→ Tiny/Small LLM local, se disponível e necessária
→ pesquisa externa, se permitida e faltar informação
→ modelo mais capaz, se disponível/permitido e ainda necessário
→ humano
```

Uma máquina de 4–8 GB não recebe outro cérebro: recebe o mesmo ciclo com menos degraus pesados disponíveis.

## Invariantes

1. A pessoa continua autoridade final.
2. Linguagem natural é a superfície humana; não é uma quarta memória/comparador.
3. IA é opcional, efémera e subordinada.
4. Web é fonte externa, não verdade.
5. Pesquisa externa não escreve diretamente no cofre final.
6. LLM não escreve diretamente no cofre final.
7. O sistema deve tentar o caminho mais barato/suficiente antes de escalar.
8. Quando não consegue resolver, deve poder dizer **não consigo / falta X**, em vez de inventar.
9. Cada escalada deve preservar contexto, proveniência e limites necessários.
10. A execução final continua sujeita às regras de risco, permissões e autoridade já definidas na Constituição.

## Hipótese a testar

A hipótese experimental é:

> Preparação determinística + memória + regras + comparação + recuperação dirigida permite que uma LLM pequena resolva problemas que, sem essa preparação, exigiriam mais contexto ou um modelo maior.

Isto será testado, não presumido.

Comparações futuras:

```text
Tiny isolada
vs.
Tiny + contexto bruto
vs.
Tiny + contexto selecionado
vs.
Tiny + sistema integrado por etapas
vs.
modelo maior
```

Medir: acerto, consistência, chamadas, tokens/contexto, RAM, CPU, latência, energia, escaladas, necessidade de Web, necessidade de modelo maior e interrupções humanas.

## Relação com o desenvolvimento atual

Esta nota documenta arquitetura e comportamento futuro.

**F0-001 continua exatamente como está:** Event canónico, serialização, SHA-256 e testes. Não adicionar LLM, Web, comparadores, memórias, Logseq, Activepieces ou bases de dados à microtarefa atual por causa desta nota.

A integração desta escalada deve ser especificada em microtarefas futuras, respeitando:

```text
SPEC → IMPLEMENT → TEST → REVIEW → PASS → próxima microtarefa
```
