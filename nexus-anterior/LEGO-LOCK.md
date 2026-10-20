# Componentes, proveniência e estado

Seleção documental não significa instalação, integração nem licença verificada nesta tarefa.

| Componente | Papel corrente | Estado |
| --- | --- | --- |
| Python / stdlib / SQLite / Markdown | Core, contratos, persistência/representação | Baseline; protocolo de persistência G10 ainda aberto |
| Activepieces | Flows/Pieces executam capacidades, sem autoridade Canonical | Fronteira no candidato é callback; integração real NOT RUN |
| Second-Brain | Candidato a storage/lock/receipt/journal/recovery | Origem histórica stancsz/second-brain; commit/licença/ficheiros por fixar |
| LibreOffice / Zotero / LanguageTool | Capacidades de documentos, fontes e língua | Integração NOT RUN |
| IA | Capacidade residual/opcional isolada | Integração e sandbox NOT RUN |
| Joplin / Logseq | Genealogia e mecanismos estudados | Não são interface obrigatória |
| knowledge-worker / GBrain / Will / Pith | Reutilização seletiva ou padrões | Não são serviços a instalar automaticamente |

Antes de copiar terceiro: URL + commit/tag + ficheiro/função + hash + licença/notices + dependências/permissões + alterações + testes. A biblioteca citada no README do candidato não se torna dependência automaticamente. Não converter descrições históricas de licenças em verificação atual.

As dependências de auditoria estão fixadas em [requirements-auditoria.txt](requirements-auditoria.txt). Os Actions oficiais têm SHA fixo resolvido em 27/09/2026. Não foi reutilizado código novo desses projetos nesta reconciliação.

[Seleção histórica de 24/09](historico/repositorio-2026-09-24/LEGO-LOCK.md) · [Genealogia](docs/GENEALOGIA.md).
