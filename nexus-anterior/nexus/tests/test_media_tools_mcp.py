import sys
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading

from nexus.mcp_client import MCPServerSpec, call_tool, list_tools
from nexus.tests._loopback_fixture import isolated_connections

ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(sys.executable).resolve()


class Server(ThreadingHTTPServer):
    allow_reuse_address = False
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        return

    def _json(self, value):
        raw = json.dumps(value).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.server.tool == "ace":
            self._json({
                "data": {"status": "ok", "service": "ACE-Step API", "version": "1.0",
                         "models_initialized": False, "llm_initialized": False},
                "code": 200, "error": None, "timestamp": 1, "extra": None,
            })
        elif self.path == "/sdapi/v1/options":
            self._json({"sd_model_checkpoint": ""})
        elif self.path == "/sdapi/v1/samplers":
            self._json([{"name": "Euler"}])
        else:
            self.send_response(404); self.end_headers()


@contextmanager
def services():
    servers = [Server(("127.0.0.1", 0), Handler), Server(("127.0.0.1", 0), Handler)]
    servers[0].tool, servers[1].tool = "ace", "forge"
    threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in servers]
    for t in threads: t.start()
    try:
        with isolated_connections({8001: servers[0].server_port, 7861: servers[1].server_port},
                                  mcp_subprocess=True):
            yield
    finally:
        for s in servers: s.shutdown(); s.server_close()
        for t in threads: t.join(timeout=3)


def spec():
    return MCPServerSpec(
        command=str(PYTHON),
        args=("-I", str(ROOT / "mcp_tools_server.py")),
    )


def test_nexus_mcp_discovers_external_media_health_tools():
    names = {item["name"] for item in list_tools(spec())}
    assert {"check_ace_step", "check_forge"} <= names


def test_nexus_mcp_checks_external_media_tools_without_authority():
    with services():
        ace = call_tool(spec(), "check_ace_step", {}, allowed_tools={"check_ace_step"})
        forge = call_tool(spec(), "check_forge", {}, allowed_tools={"check_forge"})
    assert ace["status"] == forge["status"] == "PASS"
    assert ace["authority"] == forge["authority"] == "NONE"
    assert ace["endpoint"] == "http://127.0.0.1:8001"
    assert forge["endpoint"] == "http://127.0.0.1:7861"
