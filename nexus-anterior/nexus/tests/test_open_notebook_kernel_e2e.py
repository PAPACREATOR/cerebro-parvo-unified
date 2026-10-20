"""Practical end-to-end OpenNotebook boundary through the real Nexus MCP stdio path.

The HTTP peer is a deterministic loopback stand-in for the OpenNotebook
transformation endpoint. It proves the Nexus path and contracts without
claiming that a full OpenNotebook database/model stack ran in CI.
"""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import threading
import time

import pytest

from nexus.tests._mcp_baseline import execute
from nexus.contracts import Blocked
from nexus.host import Host
from nexus.tests.test_reverse_flow import http
from nexus.tests._loopback_fixture import isolated_connections


SOURCE = "Lisboa recebeu 12 caixas."
CONFIG = {
    "base_url": "http://127.0.0.1:5055",
    "password": "ARCHIVE_REDACTED_05",
    "model_id": "model:local",
    "transformation_id": "transformation:test",
}
GOOD = {
    "title": "Entrega",
    "summary": "Foram recebidas caixas em Lisboa.",
    "quotes": [SOURCE],
}


class ReusableHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = False
    daemon_threads = True


class OpenNotebookHandler(BaseHTTPRequestHandler):
    mode = "ok"
    calls = 0
    last_request = None

    def log_message(self, *_args):
        return

    def _json(self, status, value):
        raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        if self.path != "/api/transformations/execute":
            self._json(404, {"detail": "not found"})
            return
        if self.headers.get("Authorization") != "Bearer ARCHIVE_REDACTED_05":
            self._json(401, {"detail": "unauthorized"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
        except Exception:
            self._json(400, {"detail": "invalid json"})
            return

        type(self).calls += 1
        type(self).last_request = payload

        if type(self).mode == "http-error":
            self._json(500, {"detail": "synthetic failure"})
            return
        if type(self).mode == "malformed-output":
            output = "not-json"
        elif type(self).mode == "wrong-quote":
            output = json.dumps({**GOOD, "quotes": ["Porto recebeu 99 caixas."]}, ensure_ascii=False)
        else:
            output = json.dumps(GOOD, ensure_ascii=False)

        self._json(200, {
            "output": output,
            "transformation_id": payload.get("transformation_id"),
            "model_id": payload.get("model_id"),
        })


@contextmanager
def fake_open_notebook(mode="ok"):
    OpenNotebookHandler.mode = mode
    OpenNotebookHandler.calls = 0
    OpenNotebookHandler.last_request = None
    server = ReusableHTTPServer(("127.0.0.1", 0), OpenNotebookHandler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        with isolated_connections({5055: server.server_port}, mcp_subprocess=True):
            yield OpenNotebookHandler
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


def write_config(directory):
    (directory / "open-notebook.json").write_text(
        json.dumps(CONFIG, ensure_ascii=False), encoding="utf-8"
    )


def prepared_input(tmp_path):
    run = tmp_path / "runs" / ("a" * 32)
    run.mkdir(parents=True)
    source = run / "input.bin"
    source.write_text(SOURCE, encoding="utf-8")
    write_config(run)
    return source


def test_runner_real_mcp_stdio_to_open_notebook_loopback_and_back(tmp_path):
    source = prepared_input(tmp_path)
    with fake_open_notebook() as backend:
        response = execute("interpret", source)

    assert backend.calls == 1
    assert backend.last_request == {
        "model_id": CONFIG["model_id"],
        "transformation_id": CONFIG["transformation_id"],
        "input_text": SOURCE,
    }
    assert response["trace"]["engine"] == "nexus/python-mcp"
    assert response["trace"]["summary"]["usage"]["total_tokens"] == 0
    result = response["result"]
    assert result["status"] == "UNKNOWN"
    assert result["outcome"] == "candidate"
    assert result["ai_calls"] == 1
    assert result["title"] == GOOD["title"]
    assert SOURCE in result["markdown"]
    assert result["evidence"][0]["capability"] == "open-notebook/local-model"


@pytest.mark.parametrize("mode", ["malformed-output", "wrong-quote", "http-error"])
def test_runner_rejects_bad_open_notebook_results_after_mcp_boundary(tmp_path, mode):
    source = prepared_input(tmp_path)
    with fake_open_notebook(mode):
        with pytest.raises(Blocked):
            execute("interpret", source)


@pytest.mark.skipif(os.name != "nt", reason="Full Host subprocess environment is Windows-specific")
def test_frontdoor_kernel_mcp_open_notebook_creative_human_gate_canonical_restart(tmp_path):
    data_root = tmp_path / "nexus-data"
    data_root.mkdir()
    write_config(data_root)
    request = {
        "process": "interpret",
        "text": SOURCE,
        "filename": "",
        "attachment": "",
    }

    host = Host(data_root)
    with fake_open_notebook() as backend, http(host, allow_direct_run=True) as call:
        run_id = call("/api/run", request)["run_id"]
        deadline = time.monotonic() + 60
        state = call("/api/runs/" + run_id)
        while state["status"] == "RUNNING" and time.monotonic() < deadline:
            time.sleep(0.05)
            state = call("/api/runs/" + run_id)

        assert state["status"] == "HUMAN_REQUIRED", state
        assert state["result"]["status"] == "UNKNOWN"
        assert state["result"]["outcome"] == "candidate"
        assert state["result"]["ai_calls"] == 1
        assert state["content"].encode("utf-8") == (
            data_root / "creative" / run_id / "content.md"
        ).read_bytes()

        ticket = call("/api/prepare", {"run_id": run_id})["ticket"]
        approved = call("/api/approve", {
            "run_id": run_id,
            "ticket": ticket,
            "confirmed": True,
        })
        assert approved["status"] == "PASS"
        assert backend.calls == 1

    # The external peer is now gone. Restart must use durable evidence and must
    # not need OpenNotebook/MCP/model execution to expose the approved result.
    restored = Host(data_root)
    with http(restored) as call:
        final = call("/api/runs/" + run_id)
        assert final["status"] == "PASS"
        assert final["result"]["ai_calls"] == 1
        assert final["content"].encode("utf-8") == (
            data_root / "canonical" / run_id / "content.md"
        ).read_bytes()

    canonical = data_root / "canonical" / run_id
    assert (canonical / "content.md").is_file()
    assert (canonical / "approval.json").is_file()
    assert (canonical / "provenance.json").is_file()
