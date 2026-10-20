# Cérebro Independente / Nexus

Sistema local-first de criação, conhecimento e execução governada para uma pessoa. A pessoa usa linguagem natural; o sistema compõe processos e ferramentas nos bastidores; a pessoa continua autoridade final.

## Código desta versão

O protótipo Windows está em [nexus/](nexus/README.md). Consultar o [estado testado e pendências](nexus/docs/PONTO-DE-SITUACAO.md). As pastas `implementacao/` e `historico/` conservam versões anteriores; não são necessárias para executar Nexus.

## Estado atual em uma frase

**Protótipo candidato: Folha em linguagem natural + Kernel/Host/Store Python + MCP determinístico + ferramentas externas + Creative/Human Gate/Canonical.**

A continuação está na [PR #23](https://github.com/PAPACREATOR/cerebro-parvo-/pull/23), branch `lab-open-notebook-avatar-20261004`; ainda não é a versão integrada em `main`. PASS de uma suite não significa release. O [ponto de situação](nexus/docs/PONTO-DE-SITUACAO.md) distingue a última referência verde, os testes do SHA analisado e os gates pendentes.

A arquitetura conceptual está estável. A implementação física continua sujeita a testes: nenhuma integração é declarada resolvida antes de PASS real.

## Modelo mental

Nexus é um **launcher metódico, com memória, leis e templates executáveis**, que usa as ferramentas disponíveis para atingir um fim. Não tenta reprogramar capacidades maduras.

A pessoa escreve na Folha. Kernel/Host/Store validam e executam o processo; MCP transporta chamadas às ferramentas. Os resultados são verificados e guardados em Creative. Só decisão humana permite promoção para Canonical. O percurso completo de cada capacidade exige prova própria.


## Separação de responsabilidades

As responsabilidades M1–M14 continuam aplicáveis. Os contratos, testes e a evidência datada da implementação estão em `nexus/docs/`.

### Folha Nexus
Interface inicial mínima. Texto natural, anexos, resultados e decisões humanas. YAML, JSON, Markdown, IDs e infraestrutura ficam escondidos na utilização normal.

### Kernel e MCP
O runtime candidato usa Kernel/Host/Store Python. MCP é transporte determinístico, sem IA nem autoridade de aprovação. Conductor/Spiff foram retirados do runtime ativo; as comparações e decisões anteriores permanecem como genealogia, incluindo a [PR #21](https://github.com/PAPACREATOR/cerebro-parvo-/pull/21).

### Open Notebook
**Bancada de trabalho, ponto.** Não é memória soberana, Canonical, Creative, arquivo, Wiki, autoridade nem interface principal. Recebe um pacote de trabalho limitado, permite trabalho cognitivo com tiny local e devolve resultado estruturado. Deve poder ser destruído/substituído sem perda de conhecimento Nexus.

### Nexus / Windows
É dono da memória e da continuidade: Raw/entrada, Creative, Canonical, arquivo, proveniência, eventos, regras, processos/templates, schemas e histórico. Formatos preferidos: Markdown + JSON + YAML + fontes originais/hashes; SQLite/FTS5 pode ser usado como índice/estado quando justificar, sem tornar a memória dependente de uma aplicação externa.

### Capabilities
LibreOffice, Zotero, LanguageTool, web, imagem, áudio, Whisper/TTS e outras ferramentas entram apenas quando um processo precisa delas. `LIGAR > CONFIGURAR > ADAPTAR > CRIAR` continua a regra.

## O que é nosso

- autoridade humana invariável;
- Creative e Canonical separados;
- promoção para Canonical apenas por Human Gate;
- IA/provider com autoridade zero;
- PASS / FAIL / UNKNOWN;
- proveniência direta e inversa;
- contradições preservadas;
- eliminação automática apenas para duplicação absolutamente exata;
- agentes como microprocessos reconstruíveis: tiny + prompt + contexto + regras + ferramentas permitidas + schema + objetivo;
- experiência validada pode tornar-se processo/template reutilizável;
- ferramentas e bancadas substituíveis;
- desmontar deve ser tão fácil como montar.

## Contratos e processos

O runtime candidato executa processos Python validados. O esquema abaixo conserva a proposta histórica de templates; `process.yaml` não é uma dependência do executor atual:

```text
process.yaml
input.schema.json
output.schema.json
prompts/
rules.yaml
tests/
```

Se o processo é conhecido, executa-se com o mínimo de IA. Se não é conhecido, a bancada ajuda a descobrir/decompor; o resultado só se torna template reutilizável depois de testes e aprovação humana.

## Prova mínima

1. linguagem natural na Folha;
2. routing pelo Kernel;
3. tarefa cognitiva enviada à bancada Open Notebook/tiny;
4. resultado JSON válido;
5. gravação em Creative;
6. tentativa de escrita direta em Canonical bloqueada;
7. Human Gate permite promoção explícita;
8. destruir/reconstruir bancada sem perder memória Nexus;
9. recuperar proveniência do resultado até ao pedido/fontes;
10. repetir tarefa semelhante e medir reutilização do processo.

Esta lista é um critério de aceitação, não uma declaração de que todos os percursos estão comprovados. Consultar a evidência por capacidade no ponto de situação.

## Benchmark externo único

Para evitar dispersão, o projeto externo de comparação escolhido em 30-09-2026 é **Negentropy-Laby/OpenDoge**. Não é dependência do Nexus nem modelo a copiar. Serve apenas para aprender e falsificar decisões: local-first/single-operator, workflow templates, contracts, approvals, evidence/replay e slots/capabilities substituíveis. O Nexus mantém a sua redução própria: Folha única, memória soberana exterior à IA, Open Notebook apenas como bancada descartável e aprendizagem processual sem crescimento de autoridade.

## Regra permanente

- **LIGAR > CONFIGURAR > ADAPTAR > CRIAR.**
- **NENHUM COMPONENTE ENTRA SEM UM FAIL QUE O JUSTIFIQUE.**
- **SE NÃO PODE SER DESLIGADO SEM DESTRUIR O RESTO, ESTÁ MAL INTEGRADO.**
- **MEMÓRIA NÃO É AUTORIDADE.**
- **IA NÃO É AUTORIDADE.**
- **PROMOTE_TO_CANONICAL só acontece após decisão humana.**
- **Similaridade nunca autoriza eliminação; apenas duplicação exata.**

## Licença do projeto

Código/documentação próprios: PolyForm Noncommercial 1.0.0. Dependências mantêm as suas próprias licenças; antes de redistribuição devem ser fixadas versões e `THIRD_PARTY_NOTICES`.

[Estado operacional](nexus/docs/PONTO-DE-SITUACAO.md) · [Arranque](nexus/README.md) · [Constituição](CEREBRO_CONSTITUTION.md) · [Arquitetura e genealogia](CEREBRO_ARCHITECTURE.md) · [Decisões](DECISIONS.md)

Os documentos conceptuais e planos datados preservam etapas anteriores (incluindo Activepieces/Conductor); a composição executável atual deve ser conferida no código, na PR #23 e na evidência por SHA. A organização documental não altera as invariantes M1–M14.
