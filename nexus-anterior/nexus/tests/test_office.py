import io
import zipfile
import uuid
import json
import subprocess
import pytest
from nexus.adapters.office import document_kind, pdf_bytes, run as convert
from nexus.contracts import Blocked
from nexus.store import Store, HumanDecision, digest
from nexus.tests.test_store import request, result, execution_trace


def odt(extra=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        z.writestr("mimetype", "application/vnd.oasis.opendocument.text")
        z.writestr("content.xml", '<document xmlns="http://example.org">Ensaio</document>')
        if extra:
            z.writestr(*extra)
    return stream.getvalue()


def test_document_detection():
    assert document_kind(odt()) == ".odt"


@pytest.mark.parametrize("raw", [b"", b"fake.docx", odt(("Basic/script.xml", "macro")),
    odt(("links.xml", '<a xlink:href="https://example.com"/>'))],
    ids=["empty", "not-a-document", "macro", "external-link"])
def test_invalid_or_active_document_blocked(raw):
    with pytest.raises(Blocked): document_kind(raw)


@pytest.mark.parametrize("raw", [b"", b"fake PDF", b"%PDF-1.4\nunfinished document"])
def test_invalid_pdf_blocked(tmp_path, raw):
    p = tmp_path / "resultado.pdf"; p.write_bytes(raw)
    with pytest.raises(Blocked): pdf_bytes(p)


def candidate_pdf(store):
    req = request(); req["process"] = "convert_pdf"
    run = store.create(req)
    raw = b"%PDF-1.4\nsynthetic gate fixture\n%%EOF\n"
    (store.path("runs", run) / "resultado.pdf").write_bytes(raw)
    value = result(); value.update(status="UNKNOWN", outcome="candidate", artifact={"name": "resultado.pdf", "sha256": digest(raw)})
    store.accept(run, value, execution_trace(store, run, test=True))
    return run, raw


def test_approval_preserves_pdf_and_restart(tmp_path):
    store = Store(tmp_path); run, raw = candidate_pdf(store)
    state = store.state(run)
    assert state["artifact_sha256"] == digest(raw)
    decision = HumanDecision(uuid.uuid4().hex, "test-human", run, state["candidate_sha256"], "APPROVE")
    store.promote(run, decision)
    assert (store.path("canonical", run) / "resultado.pdf").read_bytes() == raw
    assert Store(tmp_path).state(run)["commit_status"] == "COMMITTED"
    (store.path("canonical", run) / "resultado.pdf").write_bytes(raw+b"changed")
    assert Store(tmp_path).state(run)["commit_status"] == "RECOVERY_REQUIRED"


def test_changed_pdf_blocks_approval(tmp_path):
    store = Store(tmp_path); run, raw = candidate_pdf(store)
    decision = HumanDecision(uuid.uuid4().hex, "test-human", run, store.state(run)["candidate_sha256"], "APPROVE")
    (store.path("creative", run) / "resultado.pdf").write_bytes(raw+b"changed")
    with pytest.raises(Blocked): store.promote(run, decision)
    assert not store.path("canonical", run).exists()


def test_missing_pdf_blocks_acceptance(tmp_path):
    store = Store(tmp_path); req = request(); req["process"] = "convert_pdf"
    run = store.create(req)
    with pytest.raises(Blocked): store.accept(run, result(), execution_trace(store, run))


def configure(tmp_path):
    source = tmp_path / "input.bin"; source.write_bytes(odt())
    exe = tmp_path / "soffice.com"
    (tmp_path / "libreoffice.json").write_text(json.dumps({"executable": str(exe)}))
    return source, exe


def test_missing_office(tmp_path):
    source, _ = configure(tmp_path)
    with pytest.raises(Blocked): convert(source)


def test_office_failure(tmp_path, monkeypatch):
    # Process/timeout unit double only; real native security is tested separately.
    monkeypatch.setattr("nexus.adapters.office.require_native_boundary", lambda: None)
    monkeypatch.setattr(subprocess, "CREATE_NO_WINDOW", getattr(subprocess, "CREATE_NO_WINDOW", 0), raising=False)
    source, exe = configure(tmp_path); exe.touch()
    original = source.read_bytes()
    class Failed:
        stdin = io.BytesIO()
        def wait(self, **kw): return 1
    def failed(*args, **kwargs):
        assert kwargs["stdin"] == subprocess.PIPE
        return Failed()
    monkeypatch.setattr(subprocess, "Popen", failed)
    with pytest.raises(Blocked): convert(source)
    assert source.read_bytes() == original
    assert Failed.stdin.closed


def test_office_timeout_kills_tree(tmp_path, monkeypatch):
    # Process/timeout unit double only; real native security is tested separately.
    monkeypatch.setattr("nexus.adapters.office.require_native_boundary", lambda: None)
    monkeypatch.setattr(subprocess, "CREATE_NO_WINDOW", getattr(subprocess, "CREATE_NO_WINDOW", 0), raising=False)
    monkeypatch.setenv("SystemRoot", str(tmp_path / "Windows"))
    source, exe = configure(tmp_path); exe.touch()
    events = []
    class TimedOut:
        pid = 123
        stdin = io.BytesIO()
        def wait(self, **kw):
            if kw: raise subprocess.TimeoutExpired("soffice", 45)
            return 1
        def kill(self): events.append("kill")
    monkeypatch.setattr(subprocess, "Popen", lambda *a, **kw: TimedOut())
    monkeypatch.setattr(subprocess, "run", lambda cmd, **kw: events.append(cmd))
    with pytest.raises(Blocked): convert(source)
    assert events[0][-4:] == ["/PID", "123", "/T", "/F"]
    assert events[-1] == "kill"
    assert TimedOut.stdin.closed


def test_http_pdf_requires_session_and_unchanged_bytes(tmp_path):
    import threading
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
    from nexus.host import Host
    from nexus.app import make_server
    host = Host(tmp_path); run, raw = candidate_pdf(host.store)
    server = make_server(host)
    worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
    url = "http://127.0.0.1:" + str(server.server_port) + "/api/pdf/" + run
    try:
        with pytest.raises(HTTPError): urlopen(url)
        req = Request(url, headers={"X-Nexus-Session": host.session})
        with urlopen(req) as response:
            assert response.headers["Content-Type"] == "application/pdf"
            assert response.read() == raw
        (host.store.path("creative", run) / "resultado.pdf").write_bytes(raw+b"changed")
        with pytest.raises(HTTPError): urlopen(req)
        with pytest.raises(Blocked): host.prepare_approval(run, host.session)
    finally:
        server.shutdown(); server.server_close(); worker.join()


@pytest.mark.parametrize("extra", [
    ("Object 1/content.xml", "<office:document/>"),
    ("ObjectReplacements/Object 1", "binary"),
    ("word/embeddings/oleObject1.bin", "binary"),
    ("content.xml", '<draw:object xlink:href="./Object 1"/>'),
])
def test_embedded_writer_objects_are_blocked(extra):
    with pytest.raises(Blocked):
        document_kind(odt(extra))


@pytest.mark.parametrize("extra", [
    ("../outside.xml", "x"),
    ("/absolute.xml", "x"),
    ("C:/drive.xml", "x"),
    ("links.xml", '<a xlink:href="ftp://example.invalid/file"/>'),
    ("links.xml", '<a xlink:href="//server/share"/>'),
    ("links.xml", '<a xlink:href="smb://server/share"/>'),
])
def test_writer_internal_path_traversal_and_external_uri_are_blocked(extra):
    with pytest.raises(Blocked):
        document_kind(odt(extra))


def test_writer_raw_backslash_member_is_blocked():
    safe = b"folder/windows-path.xml"
    hostile = b"folder\\windows-path.xml"
    raw = odt(("folder/windows-path.xml", "x"))
    assert raw.count(safe) >= 2
    raw = raw.replace(safe, hostile)
    assert hostile in raw
    with pytest.raises(Blocked):
        document_kind(raw)
