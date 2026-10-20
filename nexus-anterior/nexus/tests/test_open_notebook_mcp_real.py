import shutil

import pytest

from nexus.contracts import Blocked
from nexus.mcp_client import MCPServerSpec, call_tool, list_tools

EXPECTED = {
    "search_capabilities",
    "list_notebooks","get_notebook","create_notebook","update_notebook","delete_notebook",
    "list_sources","get_source","create_source","update_source","delete_source",
    "list_notes","get_note","create_note","update_note","delete_note",
    "search","ask_question","ask_simple",
    "list_models","get_model","create_model","delete_model","get_default_models",
    "list_chat_sessions","create_chat_session","get_chat_session","update_chat_session",
    "delete_chat_session","execute_chat","get_chat_context",
    "get_settings","update_settings",
}


def real_spec():
    executable = shutil.which("open-notebook-mcp")
    assert executable, "open-notebook-mcp executable missing"
    return MCPServerSpec(
        command=executable,
        args=(),
        env={
            "OPEN_NOTEBOOK_URL": "http://127.0.0.1:1",
            "MCP_TRANSPORT": "stdio",
        },
    )


def test_real_open_notebook_mcp_exact_tool_inventory():
    names = {item["name"] for item in list_tools(real_spec())}
    assert names == EXPECTED
    assert len(names) == 33


def test_real_open_notebook_mcp_search_capabilities_without_backend():
    result = call_tool(
        real_spec(),
        "search_capabilities",
        {"query": "", "detail": "name", "limit": 50},
        allowed_tools={"search_capabilities"},
    )
    names = {item["name"] for item in result["matches"]}
    assert result["count"] == 33
    assert names == EXPECTED


def test_real_open_notebook_mcp_capability_search_is_deterministic_except_request_id():
    first = call_tool(
        real_spec(),
        "search_capabilities",
        {"query": "notebook", "detail": "summary", "limit": 10},
        allowed_tools={"search_capabilities"},
    )
    second = call_tool(
        real_spec(),
        "search_capabilities",
        {"query": "notebook", "detail": "summary", "limit": 10},
        allowed_tools={"search_capabilities"},
    )
    first.pop("request_id")
    second.pop("request_id")
    assert first == second
    assert all("notebook" in (
        item["name"] + " " + item["summary"] + " " + " ".join(item["tags"])
    ).lower() for item in first["matches"])


def test_real_open_notebook_mcp_backend_absence_is_controlled():
    with pytest.raises(Blocked, match="devolveu erro"):
        call_tool(
            real_spec(),
            "list_notebooks",
            {"archived": False, "order_by": "updated desc", "limit": 5},
            allowed_tools={"list_notebooks"},
        )


def test_real_open_notebook_mcp_kernel_allowlist_still_wins():
    with pytest.raises(Blocked, match="não autorizada"):
        call_tool(
            real_spec(),
            "delete_notebook",
            {"notebook_id": "notebook:ARCHIVE_REDACTED_04"},
            allowed_tools={"search_capabilities"},
        )
