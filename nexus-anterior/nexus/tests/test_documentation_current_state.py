from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CURRENT_DOCS = (
    "README.md",
    "AGENTS.md",
    "CEREBRO_CONSTITUTION.md",
    "CEREBRO_ARCHITECTURE.md",
    "IMPLEMENTATION_PLAN.md",
    "INSTALLATION_PLAN.md",
    "COMPATIBILITY-MATRIX.md",
)

FORBIDDEN_CURRENT_CLAIMS = (
    "Activepieces fornece WebUI/Chat UI",
    "Activepieces é o motor executivo",
    "Activepieces executa; não decide conhecimento",
    "Activepieces é a peça central",
    "Activepieces é o método padrão",
    "Memory Provider local SQLite/MCP",
)


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_current_documents_do_not_reactivate_superseded_runtime():
    for path in CURRENT_DOCS:
        body = read(path)
        for phrase in FORBIDDEN_CURRENT_CLAIMS:
            assert phrase not in body, (path, phrase)


def test_current_architecture_names_kernel_and_mcp_roles():
    body = read("CEREBRO_ARCHITECTURE.md")
    assert "Kernel / Host / Store" in body
    assert "MCP" in body
    assert "Transporte determinístico" in body
    assert "Activepieces, Memory Provider, Spiff e Conductor" in body
    assert "Não são runtime obrigatório atual" in body


def test_constitution_keeps_human_authority_and_canonical_gate():
    body = read("CEREBRO_CONSTITUTION.md")
    assert "a pessoa é a autoridade final" in body
    assert "promoção para Canonical exige Human Gate" in body
    assert "similaridade/paráfrase nunca autoriza eliminação" in body


def test_writer_conversion_is_not_misrepresented_as_full_writer():
    f007 = read("nexus/docs/F007-LIBREOFFICE.md")
    writer = read("nexus/docs/CAPABILITY-WRITER-EDITORIAL.md")
    assert "não prova Writer completo" in f007
    assert "W001" in writer and "W020" in writer
    assert "WRITER_EDITORIAL=PASS" in writer
    assert "Até lá, F007 continua corretamente descrita apenas como conversão DOCX/ODT → PDF." in writer


def test_writer_contract_preserves_authority_and_original():
    body = read("nexus/docs/CAPABILITY-WRITER-EDITORIAL.md")
    assert "original fornecido pela pessoa nunca é alterado" in body
    assert "LibreOffice não escreve diretamente em Creative/Canonical" in body
    assert "Human Gate" in body
    assert "Canonical vazio antes da decisão" in body
