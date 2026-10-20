# Plano de implementação vigente

Objetivo: fechar um protótipo local funcional no PC, mantendo o Kernel estável e acrescentando capacidades por adapters/contratos.

## Regra de execução

Cada micro-passo segue:

`contrato → implementação mínima → teste direto → teste inverso/bloqueio → adversarial/limites → regressão do bloco → regressão total → E2E`.

FAIL é preservado. Não se avança enquanto a causa não estiver corrigida e o bloco repetido.

## Fase 0 — sincronização segura

- localizar uma única cópia oficial;
- recusar múltiplos checkouts;
- recusar árvore suja;
- `fetch + switch + merge --ff-only`;
- nunca `reset --hard`;
- não criar clone redundante.

## Fase 1 — preparar o Core no PC

- Python 3.12 local;
- `.venv`;
- dependências de teste;
- Core;
- Blocks;
- Practical;
- All;
- autoridade;
- confinamento;
- bidirecionalidade;
- recovery;
- relatório por HEAD.

## Fase 2 — inventário real

Detetar sem instalar:
- Git/Python/Java;
- LibreOffice;
- Zotero;
- LanguageTool;
- OpenNotebook;
- FFmpeg;
- ACE-Step;
- Forge.

O inventário não autoriza provisioning.

## Fase 3 — plano do que falta

Para cada ferramenta:
- estado atual;
- fonte;
- versão/pin;
- licença;
- destino;
- tipo de instalação;
- gate necessário;
- health check;
- rollback/cleanup.

Modo inicial: PLAN_ONLY.

## Fase 4 — provisioning protegido

Só depois do seu gate próprio:
- staging delimitado;
- verificação de pin/hash/licença;
- instalação externa;
- nenhum acesso a Store/Creative/Canonical;
- nenhum arranque automático não autorizado;
- cleanup e recovery;
- health check;
- relatório.

ACE-Step, Forge, modelos/avatar e isolamento de instalação pertencem aqui.

## Fase 5 — capacidades editoriais

### LibreOffice Writer
Expandir o adapter atual, que hoje prova apenas DOCX/ODT → PDF:
- estilos;
- páginas/espelhos;
- gutter;
- cabeçalhos/rodapés;
- numeração;
- viúvas/órfãos;
- secções/capítulos;
- imagens/legendas;
- índices;
- templates de livro;
- round-trip;
- verificação PDF.

### Zotero
- leitura local;
- pesquisa;
- referências;
- citações;
- proveniência;
- escrita apenas com gate humano aplicável.

## Fase 6 — cognição e multimédia físicas

- OpenNotebook 1.15 + SurrealDB + modelo local real;
- ACE-Step na RTX 2080;
- Forge com checkpoint licenciado;
- avatar/FFmpeg;
- resultados sempre candidate/Creative;
- hashes e proveniência;
- limites GPU/VRAM/timeouts medidos.

## Fase 7 — adaptabilidade

Nova capability:
`adapter → contrato → tests → MCP/runner → Kernel → Creative → humano → Canonical`.

Não redesenhar o núcleo por ferramenta.

## Fora do plano ativo

Activepieces, Memory Provider, Spiff e Conductor permanecem na genealogia e comparação histórica. Não são dependências do runtime candidato atual.
