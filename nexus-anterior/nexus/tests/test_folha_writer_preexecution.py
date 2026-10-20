"""Writer PDF export is available only through exact Folha text and one-use human tickets.

No real Writer launches here; live Windows LPAC and PDF assertions are in
test_native_writer_route_real.py. These cases prove product HTTP authority.
"""
import base64
import io
import struct
import zipfile
from urllib.error import HTTPError

import pytest

from nexus.host import Host
from nexus.tests.test_reverse_flow import http


def doc():
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("mimetype", "application/vnd.oasis.opendocument.text")
        archive.writestr("content.xml", '<?xml version="1.0"?><office:document-content '
            'xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"/>')
    return stream.getvalue()


def proposal(text="& converter para pdf", *, filename="original.odt", raw=None):
    content = doc() if raw is None else raw
    return {"text": text, "filename": filename,
            "attachment": base64.b64encode(content).decode("ascii")}


def unsupported_zip_compression():
    raw = bytearray(doc())
    # Change the same member's method in local and central directory headers.
    # zipfile.ZipFile can enumerate it but .read() raises NotImplementedError.
    local = raw.index(b"PK\x03\x04")
    central = raw.index(b"PK\x01\x02")
    struct.pack_into("<H", raw, local + 8, 99)
    struct.pack_into("<H", raw, central + 10, 99)
    return bytes(raw)


@pytest.mark.parametrize(("text", "expected"), (
    ("& converter para pdf", "convert_pdf"),
    ("& exportar manuscrito para pdf", "book"),
))
def test_writer_requires_preexecution_human_ticket(tmp_path, monkeypatch, text, expected):
    host = Host(tmp_path)
    calls = []
    def capture(request, session):
        host.authorize(session)
        calls.append(request)
        return {"run_id": "a" * 32}
    monkeypatch.setattr(host, "start", capture)
    data = proposal(text)
    with http(host) as call:
        with pytest.raises(HTTPError) as ARCHIVE_REDACTED_04:
            call("/api/run", {"process": expected, **data})
        assert ARCHIVE_REDACTED_04.value.code == 403
        prepared = call("/api/prepare-run", data)
        assert prepared["process"] == expected
        assert prepared["attachment_bytes"] == len(doc())
        assert prepared["attachment_sha256"] != ""
        assert not calls
        assert call("/api/runs") == []
        approved = call("/api/confirm-run", {"ticket": prepared["ticket"],
                                            "confirmed": True, **data})
        assert approved["run_id"] == "a" * 32
        with pytest.raises(HTTPError) as replayed:
            call("/api/confirm-run", {"ticket": prepared["ticket"],
                                     "confirmed": True, **data})
        assert replayed.value.code == 403
    assert calls == [{"process": expected, **data}]
    for root in ("runs", "creative", "canonical"):
        assert not list((tmp_path / root).iterdir())


@pytest.mark.parametrize("data", (
    proposal("& converter para pdf e executa script"),
    proposal("& nao converter para pdf"),
    proposal("& exportar manuscrito para pdf e pesquisar na web"),
    proposal("& converter para pdf", filename="original.docx"),
    proposal("& converter para pdf", raw=b"not a document"),
    proposal("& converter para pdf", raw=unsupported_zip_compression()),
    proposal("& exportar manuscrito para pdf", filename="malicioso.txt"),
    {"text": "& converter para pdf", "filename": "", "attachment": ""},
    proposal("converter para pdf"),
))
def test_writer_ambiguous_or_invalid_document_never_gets_ticket(tmp_path, data):
    host = Host(tmp_path)
    with http(host) as call:
        with pytest.raises(HTTPError) as refused:
            call("/api/prepare-run", data)
        assert refused.value.code == 403
        assert call("/api/runs") == []
    for root in ("runs", "creative", "canonical"):
        assert not list((tmp_path / root).iterdir())


@pytest.mark.parametrize("process", ("convert_pdf", "book"))
def test_edit_after_review_and_cancel_cannot_execute_writer(tmp_path, monkeypatch, process):
    host = Host(tmp_path)
    monkeypatch.setattr(host, "start", lambda *_: pytest.fail("Writer executed without a matching ticket"))
    data = proposal("& converter para pdf" if process == "convert_pdf" else "& exportar manuscrito para pdf")
    with http(host) as call:
        first = call("/api/prepare-run", data)
        altered = {**data, "text": data["text"] + " agora"}
        with pytest.raises(HTTPError):
            call("/api/confirm-run", {"ticket": first["ticket"],
                                      "confirmed": True, **altered})
        with pytest.raises(HTTPError):
            call("/api/confirm-run", {"ticket": first["ticket"],
                                      "confirmed": True, **data})
        second = call("/api/prepare-run", data)
        assert call("/api/confirm-run", {"ticket": second["ticket"],
                                         "confirmed": False, **data}) == {"status": "CANCELLED"}
        with pytest.raises(HTTPError):
            call("/api/confirm-run", {"ticket": second["ticket"],
                                      "confirmed": True, **data})
        assert call("/api/runs") == []
    for root in ("runs", "creative", "canonical"):
        assert not list((tmp_path / root).iterdir())
