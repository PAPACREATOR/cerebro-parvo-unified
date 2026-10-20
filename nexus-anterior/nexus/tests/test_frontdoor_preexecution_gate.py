"""Pre-execution human gate for the single approved natural verify route."""
import base64
import os
import time
from urllib.error import HTTPError

import pytest

from nexus.host import Host
from nexus.tests.test_reverse_flow import http


def payload(text="Verifica a integridade deste ficheiro.", raw=b"conteudo original", filename="prova.txt"):
    return {
        "text": text,
        "filename": filename,
        "attachment": base64.b64encode(raw).decode("ascii"),
    }


def confirm(prepared, value, confirmed=True):
    return {
        "ticket": prepared["ticket"],
        "confirmed": confirmed,
        **value,
    }


def assert_empty(root):
    for name in ("runs", "creative", "canonical"):
        assert not list((root / name).iterdir())


def test_product_server_rejects_direct_run_even_with_valid_session(tmp_path):
    """A valid local session must not bypass the pre-execution human gate."""
    host = Host(tmp_path)
    value = {"process": "verify", **payload()}
    with http(host) as call:
        with pytest.raises(HTTPError) as error:
            call("/api/run", value)
        assert error.value.code == 403
        assert call("/api/runs") == []
    assert_empty(tmp_path)
    assert not host.busy.locked()


def test_natural_verify_is_only_proposed_then_explicitly_confirmed(tmp_path, monkeypatch):
    host = Host(tmp_path)
    calls = []

    def fake_start(request, session):
        host.authorize(session)
        calls.append(request)
        return {"run_id": "a" * 32}

    monkeypatch.setattr(host, "start", fake_start)
    value = payload()
    with http(host) as call:
        prepared = call("/api/prepare-run", value)
        assert calls == []
        assert_empty(tmp_path)
        assert prepared["process"] == "verify"
        assert prepared["filename"] == value["filename"]
        assert prepared["attachment_bytes"] == len(b"conteudo original")
        assert len(prepared["attachment_sha256"]) == 64

        started = call("/api/confirm-run", confirm(prepared, value))
        assert started["run_id"] == "a" * 32

    assert len(calls) == 1
    assert calls[0] == {"process": "verify", **value}


@pytest.mark.parametrize("value", [
    payload(text="Revê este ficheiro."),
    payload(text="Não verifiques a integridade deste ficheiro."),
    payload(text='Ele escreveu «verifica a integridade deste ficheiro»'),
    payload(text="Verifica a integridade deste ficheiro e pesquisa na web."),
    {"text": "Verifica a integridade deste ficheiro.", "filename": "", "attachment": ""},
    payload(raw=b"", filename="vazio.txt"),
    payload(filename="../fora.txt"),
])
def test_unmapped_ambiguous_or_invalid_natural_request_never_prepares_execution(tmp_path, value):
    host = Host(tmp_path)
    with http(host) as call:
        with pytest.raises(HTTPError) as error:
            call("/api/prepare-run", value)
        assert error.value.code == 403
        assert call("/api/runs") == []
    assert_empty(tmp_path)
    assert not host.busy.locked()


def test_edit_after_review_consumes_ticket_and_never_executes(tmp_path, monkeypatch):
    host = Host(tmp_path)
    monkeypatch.setattr(host, "start", lambda *_: pytest.fail("changed request must not execute"))
    original = payload()
    changed = payload(raw=b"outros bytes")
    with http(host) as call:
        prepared = call("/api/prepare-run", original)
        with pytest.raises(HTTPError):
            call("/api/confirm-run", confirm(prepared, changed))
        with pytest.raises(HTTPError):
            call("/api/confirm-run", confirm(prepared, original))
    assert_empty(tmp_path)


def test_reject_consumes_ticket_without_execution(tmp_path, monkeypatch):
    host = Host(tmp_path)
    monkeypatch.setattr(host, "start", lambda *_: pytest.fail("rejected request must not execute"))
    value = payload()
    with http(host) as call:
        prepared = call("/api/prepare-run", value)
        cancelled = call("/api/confirm-run", confirm(prepared, value, confirmed=False))
        assert cancelled == {"status": "CANCELLED"}
        with pytest.raises(HTTPError):
            call("/api/confirm-run", confirm(prepared, value))
    assert_empty(tmp_path)


def test_expired_pre_execution_ticket_never_executes(tmp_path, monkeypatch):
    import nexus.app as app

    host = Host(tmp_path)
    monkeypatch.setattr(app, "_PREEXECUTION_TTL_SECONDS", 0)
    monkeypatch.setattr(host, "start", lambda *_: pytest.fail("expired ticket must not execute"))
    value = payload()
    with http(host) as call:
        prepared = call("/api/prepare-run", value)
        with pytest.raises(HTTPError) as error:
            call("/api/confirm-run", confirm(prepared, value))
        assert error.value.code == 403
        assert call("/api/runs") == []
    assert_empty(tmp_path)
    assert not host.busy.locked()


def test_pre_execution_ticket_does_not_survive_server_restart(tmp_path, monkeypatch):
    first = Host(tmp_path)
    value = payload()
    with http(first) as call:
        prepared = call("/api/prepare-run", value)

    restarted = Host(tmp_path)
    monkeypatch.setattr(restarted, "start", lambda *_: pytest.fail("stale ticket must not execute"))
    with http(restarted) as call:
        with pytest.raises(HTTPError):
            call("/api/confirm-run", confirm(prepared, value))
    assert_empty(tmp_path)


def test_normal_folha_does_not_expose_process_radio_buttons():
    from nexus.contracts import ROOT

    html = (ROOT / "ui" / "index.html").read_text("utf-8")
    javascript = (ROOT / "ui" / "app.js").read_text("utf-8")
    assert 'name="process"' not in html
    assert "input[name=\"process\"]" not in javascript
    assert "/api/prepare-run" in javascript
    assert "/api/confirm-run" in javascript


@pytest.mark.skipif(os.name != "nt", reason="Real protected verify execution requires Windows")
def test_natural_verify_real_windows_reaches_canonical_and_restart_without_replay(tmp_path, monkeypatch):
    host = Host(tmp_path)
    value = payload(raw=b"Nexus natural verify acceptance bytes")
    with http(host) as call:
        prepared = call("/api/prepare-run", value)
        assert call("/api/runs") == []
        started = call("/api/confirm-run", confirm(prepared, value))
        run_id = started["run_id"]

        deadline = time.monotonic() + 65
        state = {}
        while time.monotonic() < deadline:
            state = call("/api/runs/" + run_id)
            if state["status"] != "RUNNING":
                break
            time.sleep(.2)

        assert state["status"] == "HUMAN_REQUIRED", state
        assert state["result"]["ai_calls"] == 0
        assert (tmp_path / "creative" / run_id / "content.md").is_file()
        assert not (tmp_path / "canonical" / run_id).exists()

        approval = call("/api/prepare", {"run_id": run_id})
        final = call("/api/approve", {
            "run_id": run_id,
            "ticket": approval["ticket"],
            "confirmed": True,
        })
        assert final["status"] == "PASS"
        expected_content = call("/api/runs/" + run_id)["content"]

    def ARCHIVE_REDACTED_04(*_args, **_kwargs):
        pytest.fail("Restart must not reexecute the verified capability")

    monkeypatch.setattr("nexus.host.launch_confined", ARCHIVE_REDACTED_04)
    restarted = Host(tmp_path)
    with http(restarted) as call:
        restored = call("/api/runs/" + run_id)
        assert restored["status"] == "PASS"
        assert restored["content"] == expected_content
        assert restarted.tickets == {}
