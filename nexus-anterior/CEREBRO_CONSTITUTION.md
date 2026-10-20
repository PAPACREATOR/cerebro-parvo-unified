# Constituição — orientação vigente

A arquitetura conceptual está fechada. A implementação pode trocar mecanismos, mas não pode alterar as invariantes sem decisão humana explícita posterior.

## Precedência

1. decisão humana explícita posterior, com data e âmbito;
2. esta Constituição e as responsabilidades M1–M14;
3. contratos de comportamento/teste aplicáveis;
4. implementação corrente validada;
5. documentos históricos, que explicam a evolução mas não substituem decisões posteriores.

Nenhum agente, workflow, plugin, modelo, provider ou ferramenta externa resolve por si só uma divergência normativa.

## Invariantes

- a pessoa é a autoridade final;
- Folha Única simples em linguagem natural; infraestrutura fica escondida;
- três memórias lógicas: trabalho, comportamental/procedimental e conhecimento persistente;
- Creative e Canonical são domínios de autoridade distintos;
- três comparadores: determinístico, semântico e relacional;
- M1–M14 são responsabilidades, não obrigação de criar 14 serviços;
- proveniência, genealogia e contradições são preservadas;
- instrução humana atual prevalece sobre comportamento aprendido;
- IA e ferramentas externas nunca aprovam conhecimento nem aumentam permissões;
- promoção para Canonical exige Human Gate aplicável;
- similaridade/paráfrase nunca autoriza eliminação;
- eliminação automática só pode decorrer de duplicação absolutamente exata e das regras humanas aplicáveis;
- replay/recuperação não volta a chamar IA/Web/provider para inventar evidência histórica;
- backup só é considerado válido após restauro demonstrado;
- falha, timeout, ausência de evidência e UNKNOWN nunca contam como PASS;
- nenhum componente externo escreve diretamente em Canonical;
- nenhum transporte MCP concede autoridade.

## Implementação operacional atual

A composição candidata validada é:

```text
Pessoa
  ↓
Folha
  ↓
Kernel / Host / Store Python
  ↓
MCP determinístico / adapters delimitados
  ↓
ferramentas externas substituíveis
  ↓
resultado UNTRUSTED/candidate
  ↓
Creative
  ↓
Human Gate
  ↓
Canonical
```

O Kernel/Host/Store conserva autoridade, regras, estado, proveniência, Creative, Human Gate e Canonical.

MCP é transporte. Não é cérebro, memória, agente nem autoridade.

OpenNotebook, LanguageTool, LibreOffice, Zotero, ACE-Step, Forge, modelos locais e outras aplicações são ferramentas externas. Devem poder ser desligadas/substituídas sem destruir conhecimento Nexus.

Activepieces, Spiff e Conductor pertencem à evolução técnica do projeto. A sua análise e evidência são preservadas em `DECISIONS.md`, `historico/` e relatórios datados, mas não são dependências do runtime candidato atual.

## Regra de engenharia

**LIGAR > CONFIGURAR > ADAPTAR > CRIAR.**

Código próprio só entra perante lacuna demonstrada. Uma ferramenta existente não ganha autoridade por ser usada.

Cada nova capacidade segue:

`contrato → teste direto → teste inverso/bloqueio → FAIL real → correção mínima → regressão do bloco → regressão total → E2E`.

## Experiência do utilizador

A pessoa vê linguagem normal, anexos, resultados e decisões.

Markdown, IDs, schemas, SQLite, MCP, adapters, processos e aplicações especializadas ficam ocultos por defeito.

## Regra de continuidade

A evolução histórica nunca é apagada para tornar a documentação “limpa”. Documentação ativa descreve o estado atual; decisões anteriores ficam na genealogia.

[Arquitetura vigente](CEREBRO_ARCHITECTURE.md) · [Decisões e genealogia](DECISIONS.md) · [Estado operacional](nexus/docs/PONTO-DE-SITUACAO.md).
