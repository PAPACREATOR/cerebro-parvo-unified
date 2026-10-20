# Pendências e portões atuais

Este ficheiro descreve apenas pendências vigentes. Pendências Activepieces/Memory Provider de 28-09 pertencem à genealogia em Git/histórico.

## P0 — fechar o PC físico

- sincronizar uma única cópia Nexus;
- executar core, blocks, practical, all;
- executar gates de confinamento/autoridade/bidirecionalidade;
- produzir relatórios locais;
- não confundir CI com PASS do hardware real.

## P1 — provisioning protegido

Os entrypoints de instalação externa estão deliberadamente bloqueados até existir provisioning protegido demonstrado.

PASS exige:
- inventário do que já existe;
- pin/proveniência/licença;
- staging delimitado;
- verificação antes de execução;
- instalação sem autoridade Nexus;
- cleanup/recovery;
- health check;
- sem fallback inseguro.

## P2 — OpenNotebook físico completo

Fechar no PC:
`Kernel → fronteira OpenNotebook 1.15 → SurrealDB → modelo local → resultado → Creative → Human Gate → Canonical → restart sem reexecução`.

## P3 — LibreOffice Writer completo

A capability atual prova DOCX/ODT → PDF. Ainda faltam como contratos separados:
- criar/editar ODT/DOCX estruturado;
- estilos de parágrafo/caracter;
- formatos de página;
- margens interior/exterior e gutter;
- cabeçalhos/rodapés e numeração;
- secções/capítulos;
- viúvas/órfãos e keep-with-next;
- imagens/legendas/referências;
- índices/sumário;
- templates de livro;
- grelha editorial;
- export PDF com verificação visual e estrutural;
- round-trip sem perda relevante.

Nenhuma destas capacidades é presumida por existir LibreOffice.

## P4 — Zotero

Ligar como ferramenta externa delimitada para pesquisa/referências, sem autoridade sobre Canonical. Proveniência das fontes deve regressar ao Kernel.

## P5 — multimédia física

- ACE-Step real na RTX 2080;
- Forge real com checkpoint explicitamente licenciado;
- FFmpeg/avatar;
- hashes/proveniência;
- resultados sempre candidate/Creative;
- GPU/VRAM/timeouts/recovery medidos.

## P6 — IMP ainda abertos

Continuar #3 e #4:
- IMP-001 receção/contrato;
- G10/IMP-019 e eliminação controlada.

## Regra

Nenhuma pendência é fechada por documentação ou por número de testes. É fechada por comportamento observado + evidência reproduzível.
