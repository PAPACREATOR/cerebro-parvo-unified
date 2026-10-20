"""Real loopback Nexus app/Host/Store behind optional Node gateway.

No modifications to the sealed Python runtime. Tests use temporary Store data
and never start an external tool. The lost-reply case promotes a fixture only
after explicit human approval, then reconciles the real Store without replay.
"""

import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path

import pytest

from nexus.app import application


REPO = Path(__file__).resolve().parents[2]


def _unused_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _request(port, path, *, method="GET", token=None, payload=None):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
    headers = {}
    if token is not None:
        headers["X-Nexus-Session"] = token
    raw = None
    if payload is not None:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    try:
        connection.request(method, path, body=raw, headers=headers)
        response = connection.getresponse()
        return response.status, response.read()
    finally:
        connection.close()


def _optional_gateway_installed():
    """Only the dedicated Node gateway CI installs Express by design.

    The main Python/Windows suite must not gain an npm install dependency:
    it exercises the Python authority independently. The dedicated gateway
    workflow runs the full test on both Windows and Linux after npm install.
    """
    node = shutil.which("node")
    if node is None:
        return False
    probe = subprocess.run(
        [node, "-e", "require.resolve('express')"],
        cwd=REPO, capture_output=True, timeout=10, check=False,
    )
    return probe.returncode == 0


@pytest.mark.skipif(
    not _optional_gateway_installed(),
    reason="Optional Express not installed; full E2E required in nexus-gateway.yml on Windows and Linux",
)
def test_gateway_forwards_to_real_host_and_one_store_without_modifying_core(tmp_path):
    with application(tmp_path / "memory") as (host, server):
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        port = _unused_port()
        env = dict(os.environ, PORT=str(port), NEXUS_BACKEND_PORT=str(server.server_port))
        gateway = subprocess.Popen(
            [shutil.which("node"), "server.js"], cwd=REPO, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        try:
            for _ in range(80):
                if gateway.poll() is not None:
                    pytest.fail("Optional gateway exited before opening loopback listener: " +
                                gateway.stderr.read().decode("utf-8", errors="replace")[:4000])
                try:
                    code, payload = _request(port, "/")
                    if code == 200:
                        assert b"Folha Nexus" in payload
                        break
                except (ConnectionError, OSError):
                    time.sleep(0.05)
            else:
                pytest.fail("Optional gateway did not start.")

            status, _ = _request(port, "/api/runs")
            assert status == 403

            status, raw = _request(port, "/api/runs", token="wrong-session")
            assert status == 403
            assert b"error" in raw

            status, raw = _request(port, "/api/runs", token=host.session)
            assert status == 200
            assert json.loads(raw) == []

            text = "?? perguntar sobre a memória do Nexus"
            status, raw = _request(
                port, "/api/interpret", method="POST", token=host.session,
                payload={"text": text},
            )
            assert status == 200
            interpreted = json.loads(raw)
            assert interpreted["original"] == text
            assert interpreted["execution"] == "NOT_AUTHORIZED"

            status, raw = _request(
                port, "/api/approve", method="POST", token=host.session,
                payload={"run_id": "a" * 32, "ticket": "not-approved", "confirmed": True},
            )
            assert status == 403

            assert host.list_runs(host.session) == []
            assert not any((tmp_path / "memory" / "runs").iterdir())

            # Real FTS5 search traverses Node -> Python app -> Host -> Store
            # using the existing isolated WikiBridge implementation.
            from nexus.tests.test_memory_search_http import stored
            draft = stored(host, "findthisnote rascunho não aprovado")
            approved = stored(host, "findthisnote conhecimento aprovado", approved=True)
            data = {"query": "findthisnote", "include_creative": False, "limit": 8}
            status, raw = _request(port, "/api/search", method="POST",
                                   token=host.session, payload=data)
            assert status == 200
            assert [x["run_id"] for x in json.loads(raw)["results"]] == [approved]
            data["include_creative"] = True
            status, raw = _request(port, "/api/search", method="POST",
                                   token=host.session, payload=data)
            assert status == 200
            assert {x["run_id"] for x in json.loads(raw)["results"]} == {draft, approved}
            assert host.store.state(draft)["status"] == "HUMAN_REQUIRED"
        finally:
            gateway.terminate()
            try:
                gateway.wait(timeout=5)
            except subprocess.TimeoutExpired:
                gateway.kill()
                gateway.wait(timeout=5)
            server.shutdown()
            thread.join(timeout=5)


@pytest.mark.skipif(
    not _optional_gateway_installed(),
    reason="Optional Express absent; dedicated gateway CI runs the real authority E2E",
)
def test_lost_approval_reply_is_unknown_and_real_store_is_reconciled_without_replay(tmp_path):
    """Drop a real Host reply at the socket boundary, after explicit approval.

    Host, app and Store are original: no monkeypatch, fake authority or tool.
    The candidate is a temporary fixture; only the approved request promotes it.
    """
    from nexus.tests.test_memory_search_http import stored

    with application(tmp_path / "memory") as (host, server):
        backend_thread = threading.Thread(target=server.serve_forever, daemon=True)
        backend_thread.start()
        effects = []
        run = stored(host, "Material temporário — aprovação explícita 🇵🇹")
        # Closed fixture routes: request input selects trusted paths, never
        # becomes an outbound URL or a response header.
        routes = (("GET", "/"), ("GET", "/api/runs"),
                  ("GET", f"/api/runs/{run}"),
                  ("POST", "/api/prepare"), ("POST", "/api/approve"))

        class LostReply(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def forward(self):
                selected = [route for route in routes if route == (self.command, self.path)]
                if not selected:
                    self.send_error(403, "Route outside the fault fixture")
                    return
                method, target = selected[0]
                length = int(self.headers.get("Content-Length", "0"))
                body = self.rfile.read(length) if length else None
                headers = {"Host": f"127.0.0.1:{server.server_port}",
                           "X-Nexus-Session": self.headers.get("X-Nexus-Session", "")}
                if body is not None:
                    headers["Content-Type"] = "application/json"
                connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                try:
                    connection.request(method, target, body=body, headers=headers)
                    reply = connection.getresponse()
                    status, raw = reply.status, reply.read()
                finally:
                    connection.close()
                if target == "/api/approve" and status == 200:
                    effects.append("real-approved-reply-lost")
                    self.close_connection = True
                    self.connection.shutdown(socket.SHUT_RDWR)
                    self.connection.close()
                    return
                self.send_response(status)
                self.send_header("Content-Type", "text/html; charset=utf-8" if target == "/"
                                 else "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            do_GET = forward
            do_POST = forward

        proxy = ThreadingHTTPServer(("127.0.0.1", 0), LostReply)
        proxy_thread = threading.Thread(target=proxy.serve_forever, daemon=True)
        proxy_thread.start()
        port = _unused_port()
        gateway = subprocess.Popen(
            [shutil.which("node"), "server.js"], cwd=REPO,
            env=dict(os.environ, PORT=str(port), NEXUS_BACKEND_PORT=str(proxy.server_port)),
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        try:
            for _ in range(80):
                if gateway.poll() is not None:
                    pytest.fail("Gateway exited during lost-reply E2E")
                try:
                    if _request(port, "/")[0] == 200:
                        break
                except (ConnectionError, OSError):
                    time.sleep(0.05)
            else:
                pytest.fail("Gateway startup timeout")

            # Exercise the fixture itself, before reaching the production gate.
            for ARCHIVE_REDACTED_04 in ("http://127.0.0.1:1/other", "/api/../other", "/api/runs?other=1"):
                assert _request(proxy.server_port, ARCHIVE_REDACTED_04, token=host.session)[0] == 403
            assert _request(proxy.server_port, "/api/runs", method="POST", token=host.session,
                            payload={})[0] == 403
            assert effects == []
            assert host.store.state(run)["status"] == "HUMAN_REQUIRED"
            status, raw = _request(port, "/api/prepare", method="POST", token=host.session,
                                   payload={"run_id": run})
            assert status == 200
            rejected_ticket = json.loads(raw)["ticket"]
            status, _ = _request(port, "/api/approve", method="POST", token=host.session,
                                 payload={"run_id": run, "ticket": rejected_ticket, "confirmed": False})
            assert status == 403
            assert host.store.state(run)["status"] == "HUMAN_REQUIRED"
            assert effects == []

            status, raw = _request(port, "/api/prepare", method="POST", token=host.session,
                                   payload={"run_id": run})
            assert status == 200
            approval = {"run_id": run, "ticket": json.loads(raw)["ticket"], "confirmed": True}
            status, raw = _request(port, "/api/approve", method="POST", token=host.session, payload=approval)
            assert status == 503
            # A real effect occurred; failure to receive its reply cannot undo it.
            assert effects == ["real-approved-reply-lost"]
            assert host.store.state(run)["status"] == "PASS"
            error = json.loads(raw)
            assert error["outcome"] == "UNKNOWN"
            assert "nenhuma operação" not in error["error"].casefold()

            status, raw = _request(port, "/api/runs", token=host.session)
            assert status == 200
            assert [entry["run_id"] for entry in json.loads(raw)] == [run]
            status, raw = _request(port, f"/api/runs/{run}", token=host.session)
            assert status == 200
            assert json.loads(raw)["status"] == "PASS"
            status, _ = _request(port, "/api/approve", method="POST", token=host.session, payload=approval)
            assert status == 403
            assert effects == ["real-approved-reply-lost"]
            assert host.store.state(run)["status"] == "PASS"
        finally:
            gateway.terminate()
            try:
                gateway.wait(timeout=5)
            except subprocess.TimeoutExpired:
                gateway.kill()
                gateway.wait(timeout=5)
            proxy.shutdown()
            proxy_thread.join(timeout=5)
            proxy.server_close()
            server.shutdown()
            backend_thread.join(timeout=5)
