"""Isolated product-candidate convergence gates, sourced from validated Folha lab findings.

The parser is not authority. Every negative/invalid instruction remains non-executable
and the source bytes remain exactly unchanged. Tests use existing Host and HTTP path.
"""
import base64
from urllib.error import HTTPError
import pytest

from nexus.frontdoor import parse, propose_operation
from nexus.host import Host
from nexus.tests.test_reverse_flow import http


ARCHIVE_REFUSALS = (
    "Evita guardar esta nota.",
    "Quero evitar guardar este ficheiro.",
    "Sem guardar o documento, continua.",
    "Proíbo guardar o meu texto.",
    "Deixa de guardar as minhas notas.",
)
VERIFY_REFUSALS = (
    "Evita verificar a integridade deste ficheiro.",
    "Sem verificar a integridade deste ficheiro, continua.",
    "Proíbo verificar a integridade deste ficheiro.",
    "Deixa de verificar a integridade deste ficheiro.",
)


@pytest.mark.parametrize("original", ARCHIVE_REFUSALS + VERIFY_REFUSALS)
def test_negated_natural_proposals_require_human_clarification(original):
    parsed = parse(original)
    assert parsed.status == "UNRESOLVED", (original, parsed.as_dict())
    assert parsed.intent is None
    assert parsed.original.encode("utf-8") == original.encode("utf-8")
    assert propose_operation(parsed, filename="prova.txt", attachment="YQ==") is None


@pytest.mark.parametrize("original", VERIFY_REFUSALS)
def test_negative_verify_with_attachment_never_prepares_a_product_run(tmp_path, original):
    host = Host(tmp_path)
    request = {"text": original, "filename": "prova.txt",
               "attachment": base64.b64encode(b"original").decode("ascii")}
    with http(host) as call:
        with pytest.raises(HTTPError) as failure:
            call("/api/prepare-run", request)
        assert failure.value.code == 403
        assert call("/api/runs") == []
    assert not list((tmp_path / "runs").iterdir())
    assert not list((tmp_path / "creative").iterdir())
    assert not list((tmp_path / "canonical").iterdir())


@pytest.mark.parametrize("codepoint", range(0x7F, 0xA0))
@pytest.mark.parametrize("template", ("@@ conteúdo {control} nota", "Guarda {control} esta nota."))
def test_nonprinting_del_c1_cannot_resolve_a_proposal(codepoint, template):
    original = template.format(control=chr(codepoint))
    parsed = parse(original)
    assert parsed.status == "BLOCKED", (hex(codepoint), parsed.as_dict())
    assert parsed.intent is None
    assert parsed.original == original
    assert propose_operation(parsed, filename="prova.txt", attachment="YQ==") is None


@pytest.mark.parametrize("original", (
    "Guarda esta nota.", "@@ Guarda esta nota.",
    "Verifica a integridade deste ficheiro.",
))
def test_positive_existing_behavior_is_retained(original):
    parsed = parse(original)
    assert parsed.status == "RESOLVED", (original, parsed.as_dict())
    assert parsed.original == original
