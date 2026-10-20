"""Product Folha: registered N-tool proposals must use the same human gate.

Host.start is intercepted to prove pre-execution authority only. Separate
native Windows tests prove confined execution and Canonical persistence.
"""
import base64
from urllib.error import HTTPError

import pytest

from nexus.capability_router import BUILTIN_CAPABILITIES
from nexus.host import Host
from nexus.tests.test_reverse_flow import http
from nexus.tests.test_folha_writer_preexecution import doc


def payload(capability):
    raw = doc() if capability.process in {"book", "convert_pdf"} else b"fonte de teste\n"
    return {
        "text": ("@ " if capability.intent == "web" else "& ") + capability.command,
        "filename": "original.odt" if capability.process in {"book", "convert_pdf"} else "fonte.txt",
        "attachment": base64.b64encode(raw).decode("ascii"),
    }


@pytest.mark.parametrize("capability", BUILTIN_CAPABILITIES, ids=lambda c: c.process)
def test_all_registered_adapters_use_http_human_gate(tmp_path, monkeypatch, capability):
    host = Host(tmp_path)
    calls = []

    def start(request, session):
        host.authorize(session)
        calls.append(request)
        return {"run_id": "a" * 32}

    monkeypatch.setattr(host, "start", start)
    data = payload(capability)
    with http(host) as call:
        with pytest.raises(HTTPError) as denied_direct:
            call("/api/run", {"process": capability.process, **data})
        assert denied_direct.value.code == 403
        prepared = call("/api/prepare-run", data)
        assert prepared["process"] == capability.process
        assert not calls
        assert call("/api/runs") == []

        with pytest.raises(HTTPError) as tampered:
            call("/api/confirm-run", {
                "ticket": prepared["ticket"], "confirmed": True,
                **dict(data, attachment=base64.b64encode(b"alterado").decode("ascii")),
            })
        assert tampered.value.code == 403
        assert not calls

        prepared = call("/api/prepare-run", data)
        assert call("/api/confirm-run", {
            "ticket": prepared["ticket"], "confirmed": False, **data,
        }) == {"status": "CANCELLED"}
        assert not calls
        with pytest.raises(HTTPError):
            call("/api/confirm-run", {"ticket": prepared["ticket"], "confirmed": True, **data})

        prepared = call("/api/prepare-run", data)
        assert call("/api/confirm-run", {
            "ticket": prepared["ticket"], "confirmed": True, **data,
        }) == {"run_id": "a" * 32}
        with pytest.raises(HTTPError):
            call("/api/confirm-run", {"ticket": prepared["ticket"], "confirmed": True, **data})

    assert calls == [{"process": capability.process, **data}]
    assert not list((tmp_path / "runs").iterdir())
    assert not list((tmp_path / "creative").iterdir())
    assert not list((tmp_path / "canonical").iterdir())


def test_two_distinct_tool_requests_require_independent_confirmations(tmp_path, monkeypatch):
    host = Host(tmp_path)
    calls = []
    monkeypatch.setattr(host, "start", lambda request, session: (
        host.authorize(session), calls.append(request), {"run_id": str(len(calls)).zfill(32)}
    )[-1])

    first = payload(next(c for c in BUILTIN_CAPABILITIES if c.process == "verify"))
    second = payload(next(c for c in BUILTIN_CAPABILITIES if c.process == "interpret"))
    with http(host) as call:
        a = call("/api/prepare-run", first)
        b = call("/api/prepare-run", second)
        assert not calls
        assert call("/api/confirm-run", {"ticket": a["ticket"], "confirmed": True, **first})["run_id"] == "0" * 31 + "1"
        assert len(calls) == 1
        assert call("/api/confirm-run", {"ticket": b["ticket"], "confirmed": False, **second}) == {"status": "CANCELLED"}
        assert len(calls) == 1
        c = call("/api/prepare-run", second)
        assert call("/api/confirm-run", {"ticket": c["ticket"], "confirmed": True, **second})["run_id"] == "0" * 31 + "2"
    assert [value["process"] for value in calls] == ["verify", "interpret"]


@pytest.mark.parametrize("raw", (
    "& preparar plano de podcast e apagar ficheiros",
    "& executar shell",
    "@ pesquisar e enviar email",
    "& nao rever texto",
))
def test_unknown_compound_and_negative_requests_stay_blocked(tmp_path, monkeypatch, raw):
    host = Host(tmp_path)
    monkeypatch.setattr(host, "start", lambda *_: pytest.fail("Unapproved dispatch"))
    value = {"text": raw, "filename": "fonte.txt",
             "attachment": base64.b64encode(b"fonte").decode("ascii")}
    with http(host) as call:
        with pytest.raises(HTTPError) as blocked:
            call("/api/prepare-run", value)
        assert blocked.value.code == 403
        assert call("/api/runs") == []
