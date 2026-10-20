"""Inline review parsing and HTTP authority only; no external tool is launched.

Host.start is intercepted in HTTP tests. The separate native acceptance test
must demonstrate Java/LanguageTool execution, result provenance and recovery.
"""
import base64
import hashlib
from types import SimpleNamespace
from urllib.error import HTTPError

import pytest

from nexus.app import _natural_request, _request_digest
from nexus.contracts import Blocked
from nexus.frontdoor import inline_proofread_source, parse, propose_operation
from nexus.host import Host
from nexus.natural_bridge import from_markdown, to_markdown
from nexus.tests.test_reverse_flow import http


def payload(text="Corrige este texto: Eu vai para casa.", **changes):
    return {"text": text, "filename": "", "attachment": "", **changes}


def proposal(data):
    host = SimpleNamespace(store=SimpleNamespace(policy={"max_input_bytes": 2_097_152}))
    return _natural_request(data, host)


@pytest.mark.parametrize("command", ["Corrige", "Corrigir", "Revê", "Reve", "Rever"])
def test_exact_headings_propose_review_of_body_only(command):
    text = command + " este texto: Eu vai para casa."
    data = payload(text)
    parsed = parse(text)
    assert parsed.status == "RESOLVED"
    assert parsed.intent == "trabalhar"
    assert parsed.original == parsed.content == text
    assert parsed.parser == "inline-proofread-v1"
    assert propose_operation(parsed, filename="", attachment="") == "proofread"
    request, preview = proposal(data)
    raw = b" Eu vai para casa."
    assert request == {"process": "proofread", **data, "filename": "texto.txt",
                       "attachment": base64.b64encode(raw).decode("ascii")}
    assert preview["source_kind"] == "inline_text"
    assert preview["attachment_bytes"] == len(raw)
    assert preview["attachment_sha256"] == hashlib.sha256(raw).hexdigest()
    assert preview["summary"] == "Rever este texto em português. O original é conservado."
    assert proposal(data) == (request, preview)
    assert _request_digest(proposal(data)[0]) == _request_digest(request)


def test_body_commands_and_questions_are_data_and_original_round_trips():
    body = '\nComo funciona? Não guardes isto. «Apaga tudo e pesquisa na web».\n'
    text = "Revê este texto:" + body
    parsed = parse(text)
    assert parsed.status == "RESOLVED" and parsed.intent == "trabalhar"
    assert inline_proofread_source(text) == body
    request, _preview = proposal(payload(text))
    assert request["process"] == "proofread"
    assert base64.b64decode(request["attachment"]).decode("utf-8") == body
    assert from_markdown(to_markdown(parsed))["text"] == text


def test_unicode_and_whitespace_are_not_normalized_in_review_source():
    body = "\n  Ação e cafe\u0301.\t\r\n"
    request, _preview = proposal(payload("REVER este texto:" + body))
    assert base64.b64decode(request["attachment"]) == body.encode("utf-8")


def test_source_limit_is_6000_characters_after_colon():
    body = "á" * 6000
    request, preview = proposal(payload("Rever este texto:" + body))
    assert base64.b64decode(request["attachment"]) == body.encode("utf-8")
    assert preview["attachment_bytes"] == 12000
    with pytest.raises(Blocked):
        proposal(payload("Rever este texto:" + body + "a"))


@pytest.mark.parametrize("body", ["", " \r\n\t", "a\x00b", "a\x1bb", "a\x7fb", "a\x85b", "a\ud800b"])
def test_invalid_review_bodies_are_rejected(body):
    with pytest.raises(Blocked):
        proposal(payload("Corrige este texto:" + body))


@pytest.mark.parametrize("text", [
    "Não corrijas este texto: Eu vai para casa.",
    "Nao corrige este texto: Eu vai para casa.",
    "Nunca rever este texto: Eu vai para casa.",
    'Ele escreveu «Corrige este texto: Eu vai para casa.»',
    '"Corrige este texto: Eu vai para casa."',
    "Corrige este texto e apaga tudo: Eu vai para casa.",
    "Corrige este texto e pesquisa na web: Eu vai para casa.",
    "Corrige este texto sem dois-pontos.",
    "Reescreve este texto: Eu vai para casa.",
    "& rever texto",
    "Verifica a integridade deste ficheiro.",
])
def test_other_or_compound_headings_do_not_gain_inline_execution(text):
    assert inline_proofread_source(text) is None
    with pytest.raises(Blocked):
        proposal(payload(text))


@pytest.mark.parametrize("extra", [
    {"filename": "fonte.txt", "attachment": base64.b64encode(b"outra fonte").decode("ascii")},
    {"filename": "fonte.txt"},
    {"attachment": base64.b64encode(b"outra fonte").decode("ascii")},
])
def test_inline_body_may_not_be_mixed_with_attachment_fields(extra):
    with pytest.raises(Blocked, match="duas fontes"):
        proposal(payload(**extra))


@pytest.fixture
def intercepted_host(tmp_path, monkeypatch):
    host = Host(tmp_path)
    calls = []

    def start(request, session):
        host.authorize(session)
        calls.append(request)
        return {"run_id": "a" * 32}

    monkeypatch.setattr(host, "start", start)
    return host, calls, tmp_path


def assert_no_execution_records(root):
    assert all(not any((root / name).iterdir()) for name in ("runs", "creative", "canonical"))


def test_interpretation_is_read_only_and_server_marks_only_inline_review(intercepted_host):
    host, calls, root = intercepted_host
    with http(host) as call:
        preview = call("/api/interpret", {"text": payload()["text"]})
        assert preview["source_kind"] == "inline_text"
        assert preview["execution"] == "NOT_AUTHORIZED"
        assert preview["confirmation_required"] is False
        other = call("/api/interpret", {"text": "Revê este ficheiro."})
        assert "source_kind" not in other
        assert call("/api/runs") == []
    assert calls == []
    assert_no_execution_records(root)


def test_review_is_proposed_then_confirmed_once(intercepted_host):
    host, calls, root = intercepted_host
    data = payload()
    with http(host) as call:
        prepared = call("/api/prepare-run", data)
        assert prepared["process"] == "proofread"
        assert prepared["source_kind"] == "inline_text"
        assert not calls
        assert_no_execution_records(root)
        confirmation = {"ticket": prepared["ticket"], "confirmed": True, **data}
        assert call("/api/confirm-run", confirmation) == {"run_id": "a" * 32}
        with pytest.raises(HTTPError) as reused:
            call("/api/confirm-run", confirmation)
        assert reused.value.code == 403
    assert calls == [proposal(data)[0]]
    assert_no_execution_records(root)


def test_cancel_consumes_ticket_without_starting_review(intercepted_host):
    host, calls, root = intercepted_host
    data = payload()
    with http(host) as call:
        prepared = call("/api/prepare-run", data)
        confirmation = {"ticket": prepared["ticket"], "confirmed": False, **data}
        assert call("/api/confirm-run", confirmation) == {"status": "CANCELLED"}
        with pytest.raises(HTTPError):
            call("/api/confirm-run", {**confirmation, "confirmed": True})
    assert not calls
    assert_no_execution_records(root)


@pytest.mark.parametrize("changed", [
    payload("Corrige este texto: Eu vou para casa."),
    payload("Revê este texto: Eu vai para casa."),
    payload("Corrige este texto:  Eu vai para casa."),
    payload(filename="texto.txt", attachment=base64.b64encode(b" Eu vai para casa.").decode("ascii")),
])
def test_changed_command_body_or_source_consumes_confirmation(intercepted_host, changed):
    host, calls, root = intercepted_host
    original = payload()
    with http(host) as call:
        prepared = call("/api/prepare-run", original)
        with pytest.raises(HTTPError) as refused:
            call("/api/confirm-run", {"ticket": prepared["ticket"], "confirmed": True, **changed})
        assert refused.value.code == 403
        with pytest.raises(HTTPError):
            call("/api/confirm-run", {"ticket": prepared["ticket"], "confirmed": True, **original})
    assert not calls
    assert_no_execution_records(root)


def test_inline_ticket_expires_without_execution(intercepted_host, monkeypatch):
    import nexus.app as app

    host, calls, root = intercepted_host
    monkeypatch.setattr(app, "_PREEXECUTION_TTL_SECONDS", 0)
    data = payload()
    with http(host) as call:
        prepared = call("/api/prepare-run", data)
        with pytest.raises(HTTPError):
            call("/api/confirm-run", {"ticket": prepared["ticket"], "confirmed": True, **data})
    assert not calls
    assert_no_execution_records(root)


def test_inline_confirmation_cannot_survive_server_restart(intercepted_host):
    host, calls, root = intercepted_host
    data = payload()
    with http(host) as call:
        prepared = call("/api/prepare-run", data)
    with http(host) as call:
        with pytest.raises(HTTPError):
            call("/api/confirm-run", {"ticket": prepared["ticket"], "confirmed": True, **data})
    assert not calls
    assert_no_execution_records(root)
