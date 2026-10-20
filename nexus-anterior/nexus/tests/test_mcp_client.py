import sys
from pathlib import Path

import pytest

from nexus.contracts import Blocked
from nexus.mcp_client import MCPServerSpec, call_tool, list_tools

ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(sys.executable).resolve()


def spec():
    return MCPServerSpec(
        command=str(PYTHON),
        args=("-u", str(ROOT / "tests/fixtures/mcp_test_server.py")),
    )


def test_real_mcp_discovers_tools():
    names = {item["name"] for item in list_tools(spec())}
    assert names == {"ping", "double", "explode"}


def test_real_mcp_bidirectional_unicode_roundtrip():
    original = "olá ação 日本語"
    result = call_tool(spec(), "ping", {"value": original}, allowed_tools={"ping"})
    assert result == {"echo": original, "authority": "NONE"}
    assert result["echo"].encode("utf-8") == original.encode("utf-8")


def test_mcp_allowlist_blocks_before_call():
    with pytest.raises(Blocked, match="não autorizada"):
        call_tool(spec(), "double", {"value": 5}, allowed_tools={"ping"})


def test_mcp_missing_tool_is_blocked():
    with pytest.raises(Blocked, match="não existe"):
        call_tool(spec(), "missing", {}, allowed_tools={"missing"})


def test_mcp_tool_error_is_blocked():
    with pytest.raises(Blocked, match="devolveu erro"):
        call_tool(spec(), "explode", {}, allowed_tools={"explode"})


def test_mcp_cloud_credentials_are_rejected():
    bad = MCPServerSpec(
        command=str(PYTHON),
        args=("-u", str(ROOT / "tests/fixtures/mcp_test_server.py")),
        env={"OPENAI_API_KEY": "ARCHIVE_REDACTED_04"},
    )
    with pytest.raises(Blocked, match="Credencial cloud"):
        list_tools(bad)


@pytest.mark.parametrize("key", [
    "NEXUS_SESSION",
    "OPEN_NOTEBOOK_PASSWORD",
    "PASSWORD",
    "TOKEN",
    "AWS_SECRET_ACCESS_KEY",
    "CUSTOM_PATH",
])
def test_mcp_arbitrary_environment_is_rejected(key):
    bad = MCPServerSpec(
        command=str(PYTHON),
        args=("-u", str(ROOT / "tests/fixtures/mcp_test_server.py")),
        env={key: "ARCHIVE_REDACTED_04"},
    )
    with pytest.raises(Blocked, match="Variável de ambiente MCP"):
        list_tools(bad)


def test_mcp_only_explicit_open_notebook_transport_environment_is_allowed():
    allowed = MCPServerSpec(
        command=str(PYTHON),
        args=("-u", str(ROOT / "tests/fixtures/mcp_test_server.py")),
        env={"OPEN_NOTEBOOK_URL": "http://127.0.0.1:1", "MCP_TRANSPORT": "stdio"},
    )
    names = {item["name"] for item in list_tools(allowed)}
    assert names == {"ping", "double", "explode"}


def test_mcp_reduced_environment_drops_pythonpath(monkeypatch):
    from nexus.mcp_client import _reduced_env
    monkeypatch.setenv("PYTHONPATH", "C:/untrusted/import/path")
    env = _reduced_env()
    assert "PYTHONPATH" not in env
