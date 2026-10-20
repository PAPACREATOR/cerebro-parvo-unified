from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading

import pytest

from nexus.adapters.media_tools import check_ace_step, check_forge
from nexus.contracts import Blocked
from nexus.tests._loopback_fixture import isolated_connections, remap_address


class Server(ThreadingHTTPServer):
    allow_reuse_address = False
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    mode = "ok"

    def log_message(self, *_args):
        return

    def _write(self, code, value, *, raw=False):
        body = value if raw else json.dumps(value).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if type(self).mode == "redirect":
            self.send_response(302)
            self.send_header("Location", "http://example.com/")
            self.end_headers()
            return
        if type(self).mode == "malformed":
            self._write(200, b"{", raw=True)
            return
        if type(self).mode == "oversize":
            self._write(200, b"x" * 1_000_001, raw=True)
            return

        if self.server.tool == "ace":
            service = "wrong" if type(self).mode == "wrong-service" else "ACE-Step API"
            self._write(200, {
                "data": {
                    "status": "ok",
                    "service": service,
                    "version": "1.0",
                    "models_initialized": False,
                    "llm_initialized": False,
                },
                "code": 200,
                "error": None,
                "timestamp": 1,
                "extra": None,
            })
            return

        if self.path == "/sdapi/v1/options":
            if type(self).mode == "wrong-options":
                self._write(200, [])
            else:
                self._write(200, {"sd_model_checkpoint": ""})
            return
        if self.path == "/sdapi/v1/samplers":
            if type(self).mode == "wrong-samplers":
                self._write(200, [{"bad": "x"}])
            else:
                self._write(200, [{"name": "Euler"}, {"name": "DPM++ 2M"}])
            return
        self._write(404, {"detail": "not found"})


@contextmanager
def local_tools(mode="ok"):
    Handler.mode = mode
    ace = Server(("127.0.0.1", 0), Handler)
    forge = Server(("127.0.0.1", 0), Handler)
    ace.tool, forge.tool = "ace", "forge"
    ta = threading.Thread(target=ace.serve_forever, daemon=True)
    tf = threading.Thread(target=forge.serve_forever, daemon=True)
    ta.start(); tf.start()
    try:
        with isolated_connections({8001: ace.server_port, 7861: forge.server_port}):
            yield
    finally:
        ace.shutdown(); forge.shutdown()
        ace.server_close(); forge.server_close()
        ta.join(timeout=3); tf.join(timeout=3)


def test_ace_health_is_bounded_and_has_no_authority():
    with local_tools():
        value = check_ace_step()
    assert value == {
        "tool": "ace-step", "status": "PASS", "authority": "NONE",
        "endpoint": "http://127.0.0.1:8001", "service": "ACE-Step API",
        "version": "1.0", "models_initialized": False, "llm_initialized": False,
    }


def test_forge_health_is_bounded_and_has_no_authority():
    with local_tools():
        value = check_forge()
    assert value == {
        "tool": "forge", "status": "PASS", "authority": "NONE",
        "endpoint": "http://127.0.0.1:7861", "api": "sdapi-v1",
        "sampler_count": 2, "checkpoint_configured": False,
    }


@pytest.mark.parametrize("mode", ["redirect", "malformed", "oversize", "wrong-service"])
def test_ace_rejects_bad_boundary(mode):
    with local_tools(mode):
        with pytest.raises(Blocked):
            check_ace_step()


@pytest.mark.parametrize("mode", ["redirect", "malformed", "oversize", "wrong-options", "wrong-samplers"])
def test_forge_rejects_bad_boundary(mode):
    with local_tools(mode):
        with pytest.raises(Blocked):
            check_forge()


def test_fixture_routing_preserves_external_ipv6_and_unmapped_destinations():
    routes = {8001: 49153}
    assert remap_address(("127.0.0.1", 8001), routes) == ("127.0.0.1", 49153)
    for address in (("localhost", 8001), ("127.0.0.2", 8001),
                    ("example.com", 8001), ("::1", 8001),
                    ("::1", 8001, 0, 0), ("127.0.0.1", 7861)):
        assert remap_address(address, routes) is address
