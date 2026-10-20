import json
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import pytest

from nexus.app import make_server
from nexus.host import Host, process_environment
from nexus.contracts import Blocked
from nexus.tests.test_store import request, candidate


def test_no_secrets_in_child_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("SystemRoot", str(tmp_path / "synthetic-windows"))
    monkeypatch.setenv("OPENAI_API_KEY", "should-never-be-inherited")
    monkeypatch.setenv("NEXUS_SESSION", "should-never-be-inherited")
    monkeypatch.setenv("PSModuleAnalysisCachePath", "untrusted-inherited-cache")
    assert "OPENAI_API_KEY" not in process_environment(tmp_path)
    assert "NEXUS_SESSION" not in process_environment(tmp_path)
    assert "PSModuleAnalysisCachePath" not in process_environment(tmp_path)


def test_gate_requires_session_ticket_and_explicit_action(tmp_path):
    host = Host(tmp_path)
    run = candidate(host.store)
    with pytest.raises(Blocked):
        host.prepare_approval(run, "tool-session")
    with pytest.raises(Blocked):
        host.approve(run, "invented", True, host.session)
    ticket = host.prepare_approval(run, host.session)["ticket"]
    with pytest.raises(Blocked):
        host.approve(run, ticket, "true", host.session)
    ticket = host.prepare_approval(run, host.session)["ticket"]
    host.approve(run, ticket, True, host.session)
    with pytest.raises(Blocked):
        host.approve(run, ticket, True, host.session)


def test_expired_ticket(tmp_path):
    host = Host(tmp_path)
    run = candidate(host.store)
    ticket = host.prepare_approval(run, host.session)["ticket"]
    binding = host.tickets[ticket]
    host.tickets[ticket] = (binding[0], binding[1], 0)
    with pytest.raises(Blocked):
        host.approve(run, ticket, True, host.session)


def test_full_http_flow_and_bypasses(tmp_path):
    host = Host(tmp_path)
    server = make_server(host, allow_direct_run=True)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = "http://127.0.0.1:" + str(server.server_port)
    def call(path, value=None, session=host.session, origin=None):
        headers = {"Content-Type": "application/json", "X-Nexus-Session": session}
        if origin:
            headers["Origin"] = origin
        req = Request(base + path, data=None if value is None else json.dumps(value).encode(), headers=headers)
        with urlopen(req, timeout=15) as response:
            return response.read()
    try:
        assert b"Folha Nexus" in call("/")
        with pytest.raises(HTTPError):
            call("/api/run", request(), session="")
        with pytest.raises(HTTPError):
            call("/api/run", request(), origin="https://untrusted.example")
        run = json.loads(call("/api/run", request()))["run_id"]
        deadline = time.monotonic() + 65
        state = {}
        while time.monotonic() < deadline:
            state = json.loads(call("/api/runs/" + run))
            if state["status"] != "RUNNING":
                break
            time.sleep(.2)
        if state["status"] != "HUMAN_REQUIRED":
            # This test uses a synthetic verify request and no credentials.
            # Retain bounded runner diagnostics instead of hiding the tool error.
            directory = host.store.path("runs", run)
            diagnostics = {"state": state}
            for name in ("failure.json", "execution.stderr.txt", "execution.stdout.json"):
                path = directory / name
                if path.is_file():
                    diagnostics[name] = path.read_text("utf-8", errors="replace")[-8000:]
            pytest.fail(json.dumps(diagnostics, ensure_ascii=False, indent=2))
        assert state["result"]["ai_calls"] == 0
        with pytest.raises(HTTPError):
            call("/api/approve", {"run_id": run, "ticket": "ai-invented", "confirmed": True})
        ticket = json.loads(call("/api/prepare", {"run_id": run}))["ticket"]
        final = json.loads(call("/api/approve", {"run_id": run, "ticket": ticket, "confirmed": True}))
        assert final["status"] == "PASS"
        provenance = json.loads((tmp_path / "canonical" / run / "provenance.json").read_bytes())
        assert provenance["human_approval"]["sha256"] == state["candidate_sha256"]
        assert provenance["execution"]["summary"]["usage"]["total_tokens"] == 0
        assert len(provenance["input_references"]) == 1
    finally:
        server.shutdown()
        server.server_close()


def test_refresh_review_revokes_previous_ticket(tmp_path):
    host = Host(tmp_path)
    run = candidate(host.store)
    old = host.prepare_approval(run, host.session)["ticket"]
    current = host.prepare_approval(run, host.session)["ticket"]
    assert len(host.tickets) == 1
    with pytest.raises(Blocked):
        host.approve(run, old, True, host.session)
    assert host.approve(run, current, True, host.session)["status"] == "PASS"


@pytest.mark.parametrize("output", [b"", b"not JSON", b'{"result":{},"trace":{}}'])
def test_invalid_tool_output_never_promotes(tmp_path, monkeypatch, output):
    class BrokenTool:
        returncode = 0
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def communicate(self, **kwargs):
            return output, b""
    monkeypatch.setattr("nexus.host.launch_confined", lambda *args, **kwargs: BrokenTool())
    host = Host(tmp_path)
    run = host.store.create(request())
    host.busy.acquire()
    host._run(run)
    assert host.store.state(run)["status"] == "BLOCKED"
    assert not list((tmp_path / "canonical").iterdir())
    assert not host.busy.locked()


@pytest.mark.parametrize("reference", [None, 4, [], {}, "../outside"])
def test_invalid_reference_is_blocked(tmp_path, reference):
    host = Host(tmp_path)
    with pytest.raises(Blocked):
        host.prepare_approval(reference, host.session)


def test_wrong_session_cannot_consume_valid_ticket(tmp_path):
    host = Host(tmp_path)
    run = candidate(host.store)
    ticket = host.prepare_approval(run, host.session)["ticket"]

    with pytest.raises(Blocked):
        host.approve(run, ticket, True, "wrong-session")

    assert ticket in host.tickets
    assert not host.store.path("canonical", run).exists()
    assert host.approve(run, ticket, True, host.session)["status"] == "PASS"


def test_ticket_is_bound_to_one_run_and_cannot_approve_another(tmp_path):
    host = Host(tmp_path)
    first = candidate(host.store)
    second = candidate(host.store)
    ticket = host.prepare_approval(first, host.session)["ticket"]

    with pytest.raises(Blocked):
        host.approve(second, ticket, True, host.session)

    assert not host.store.path("canonical", first).exists()
    assert not host.store.path("canonical", second).exists()


def test_pending_approval_ticket_does_not_survive_host_restart(tmp_path):
    first_host = Host(tmp_path)
    run = candidate(first_host.store)
    stale_ticket = first_host.prepare_approval(run, first_host.session)["ticket"]

    restarted = Host(tmp_path)
    assert restarted.tickets == {}
    with pytest.raises(Blocked):
        restarted.approve(run, stale_ticket, True, restarted.session)
    assert not restarted.store.path("canonical", run).exists()

    fresh_ticket = restarted.prepare_approval(run, restarted.session)["ticket"]
    assert restarted.approve(run, fresh_ticket, True, restarted.session)["status"] == "PASS"
