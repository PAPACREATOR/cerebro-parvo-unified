> **Estado atual (06-10-2026):** capability ativa limitada e provada para Writer **DOCX/ODT → PDF** com original conservado, hash do artefacto e Human Gate. A implementação ativa usa runner/MCP + adapter LibreOffice, não Conductor. Isto **não prova Writer completo**: criação/edição estruturada, estilos, paginação, gutter, viúvas/órfãos, templates de livro, índices, imagens/legendas e round-trip continuam pendentes. O contrato detalhado está em [CAPABILITY-WRITER-EDITORIAL.md](CAPABILITY-WRITER-EDITORIAL.md).

# F007 — documento para PDF local

INPUT: anexo DOCX ou ODT até 2 MB e LibreOffice instalado.
OUTPUT: PDF até 8 MB e relatório em Creative, original conservado; zero IA.
LEIS: aprovação vinculada ao relatório e hash do PDF; alteração posterior bloqueia promoção; nenhuma eliminação.
DEPENDÊNCIAS: LibreOffice existente, Python/Conductor; nenhuma nova biblioteca do produto.
TESTES: conversão real, PDF descarregável, original intacto, input inválido, ferramenta ausente, timeout, PDF adulterado, gate e recuperação com artefacto; regressão.

O contrato atual só transporta Markdown: não pode entregar nem aprovar o PDF. Extensão mínima: uma referência fixa a resultado.pdf e SHA-256 no JSON; Host verifica e copia para Creative e vincula o hash ao relatório aprovado. Sem caminhos arbitrários nem base64 do PDF no protocolo.

Âmbito inicial: ficheiros artificiais/localmente confiáveis. Perfil LibreOffice separado por execução; não é sandbox Windows. Validação estrutural básica do PDF não garante fidelidade visual. Não aceitar macros ou ligações externas declaradas nos pacotes nesta etapa.

## Evidência — 01-10-2026

Regressão: **109 passed, 21.72 s, exit 0**. Inclui documento inválido/ativo, PDF incompleto, ferramenta ausente, timeout controlado com terminação da árvore, hash adulterado, gate, recuperação e download HTTP autenticado. Testes de gate usam PDF sintético; não são provas de conversão.

Ensaio real independente ODT → Host → Conductor → LibreOffice → Creative: **PASS, 15.17 s**, PDF 14431 bytes, original intacto, zero IA, Canonical vazio, bypass BLOCK. Extração por pypdf confirmou uma página e «Ensaio Nexus — ação, informação, Windows.»; renderização por Poppler e inspeção visual confirmaram texto legível e acentos. Essas ferramentas de auditoria já pertenciam ao ambiente de trabalho; não foram adicionadas ao runtime Nexus.

O formato DOCX é reconhecido, mas não teve ensaio real nesta ronda. A opção e download estão na Folha; teste visual completo da interface ainda pendente. Documento de ensaio simples não prova fidelidade de tabelas, fontes ou documentos complexos. Filtros de pacotes e perfil separado não substituem isolamento Windows.
