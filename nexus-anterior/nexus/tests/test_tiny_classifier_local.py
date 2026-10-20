import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from nexus.contracts import Blocked
from nexus.natural_bridge import resolve_natural_with_tiny, to_markdown, from_markdown
from nexus.tiny_classifier import TinyLocalSpec, classify


VALID = {
    "V0": "arquivo",
    "V1": "web",
    "V2": "fontes",
    "V3": "trabalhar",
    "V4": "perguntar",
    "V5": "calcular",
    "V6": "tema",
}


class Handler(BaseHTTPRequestHandler):
    requests = 0

    def log_message(self, format, *args):
        return

    def do_POST(self):
        type(self).requests += 1
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        request = json.loads(raw.decode("utf-8"))
        assert self.path == "/v1/chat/completions"
        assert request["temperature"] == 0
        assert request["max_tokens"] == 32
        assert "authorization" not in {key.lower() for key in self.headers.keys()}
        text = request["messages"][-1]["content"]

        if "SLOW" in text:
            time.sleep(0.2)

        if "BADENVELOPE" in text:
            payload = {"choices": []}
        else:
            if "INJECT" in text:
                content = json.dumps({"intent": "web", "authority": "CANONICAL"})
            elif "FORBIDDEN" in text:
                content = json.dumps({"intent": "canonical"})
            elif "MALFORMED" in text:
                content = "not-json"
            elif "UNKNOWN" in text:
                content = json.dumps({"intent": "UNKNOWN"})
            else:
                matches = [intent for marker, intent in VALID.items() if marker in text]
                content = json.dumps({"intent": matches[0] if len(matches) == 1 else "UNKNOWN"})
            payload = {"choices": [{"message": {"content": content}}]}

        data = json.dumps(payload).encode("utf-8")
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass


@pytest.fixture(scope="module")
def tiny_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield TinyLocalSpec(
            url=f"http://127.0.0.1:{server.server_port}",
            model="qwen-3b-local",
            timeout=2,
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_tiny_loopback_1000_request_adversarial_batch(tiny_server):
    count = 0
    for i in range(700):
        marker = f"V{i % 7}"
        expected = VALID[marker]
        assert classify(f"pedido opaco {i} {marker}", tiny_server) == [expected]
        count += 1

    for i in range(100):
        assert classify(f"pedido opaco UNKNOWN {i}", tiny_server) == []
        count += 1

    for marker in ("FORBIDDEN", "INJECT", "MALFORMED", "BADENVELOPE"):
        for i in range(50):
            with pytest.raises(Blocked):
                classify(f"pedido {marker} {i}", tiny_server)
            count += 1

    assert count == 1000


@pytest.mark.parametrize(("marker", "intent"), list(VALID.items()))
def test_tiny_resolves_only_after_eliza_is_unresolved(tiny_server, marker, intent):
    original = f"faz lá isto por favor {marker}"
    parsed = resolve_natural_with_tiny(original, tiny_server)
    assert parsed.status == "RESOLVED"
    assert parsed.intent == intent
    assert parsed.parser == "tiny-hint-v1"
    assert parsed.explicit is False
    markdown = to_markdown(parsed)
    back = from_markdown(markdown)
    assert back["text"].encode("utf-8") == original.encode("utf-8")
    assert back["intent"] == intent


def test_eliza_wins_without_tiny_call(tiny_server):
    Handler.requests = 0
    parsed = resolve_natural_with_tiny("pesquisa na web gatos", tiny_server)
    assert parsed.status == "RESOLVED"
    assert parsed.intent == "web"
    assert parsed.parser == "eliza-rules-v1"
    assert Handler.requests == 0


def test_ambiguous_tiny_returns_to_human(tiny_server):
    parsed = resolve_natural_with_tiny("faz lá isto UNKNOWN", tiny_server)
    assert parsed.status == "ASK_HUMAN"
    assert parsed.intent is None
    with pytest.raises(Blocked):
        to_markdown(parsed)


def test_tiny_unavailable_returns_to_human():
    spec = TinyLocalSpec("http://127.0.0.1:1", "qwen-3b-local", timeout=0.1)
    parsed = resolve_natural_with_tiny("faz lá isto", spec)
    assert parsed.status == "ASK_HUMAN"
    assert parsed.intent is None


@pytest.mark.parametrize("url", [
    "https://127.0.0.1:9000",
    "http://example.com:9000",
    "http://192.168.1.2:9000",
])
def test_tiny_never_calls_cloud_or_lan(url):
    with pytest.raises(Blocked):
        classify("pedido V1", TinyLocalSpec(url, "qwen-3b-local"))


def test_tiny_timeout_is_blocked(tiny_server):
    spec = TinyLocalSpec(tiny_server.url, tiny_server.model, timeout=0.01)
    with pytest.raises(Blocked, match="indisponível"):
        classify("SLOW V1", spec)


def test_tiny_blocks_localhost_alias_even_if_machine_resolves_it():
    with pytest.raises(Blocked, match="loopback explícito"):
        classify("pedido V1", TinyLocalSpec("http://localhost:9000", "qwen-3b-local"))


def test_tiny_blocks_query_in_base_url():
    with pytest.raises(Blocked, match="Endpoint tiny inválido"):
        classify("pedido V1", TinyLocalSpec("http://127.0.0.1:9000?proxy=1", "qwen-3b-local"))
