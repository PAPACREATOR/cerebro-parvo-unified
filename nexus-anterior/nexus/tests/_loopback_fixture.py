"""Test-only TCP routing; production endpoint validation remains unchanged.

Fixtures bind port zero, while adapters still receive their exact production
URLs. Only the socket destination for an explicitly mapped IPv4 loopback port
changes. Windows Host brokers HTTP before confinement; Linux MCP subprocesses
use this test-only bootstrap. No product file imports or enables this helper.
"""
from contextlib import contextmanager
from dataclasses import replace
import json
import os
from pathlib import Path
import runpy
import socket
import sys
from unittest.mock import patch


LOGICAL_PORTS = frozenset({8001, 7861, 5055})


def checked_routes(routes):
    if (not isinstance(routes, dict) or not routes
            or any(type(logical) is not int or logical not in LOGICAL_PORTS
                   or type(actual) is not int or not 0 < actual < 65536
                   or actual in LOGICAL_PORTS
                   for logical, actual in routes.items())):
        raise ValueError("Invalid test-only loopback routing")
    return dict(routes)


def remap_address(address, routes):
    if (type(address) is tuple and len(address) == 2
            and address[0] == "127.0.0.1" and type(address[1]) is int
            and address[1] in routes):
        return ("127.0.0.1", routes[address[1]])
    return address


@contextmanager
def isolated_connections(routes, *, mcp_subprocess=False):
    routes = checked_routes(routes)
    original_connection = socket.create_connection

    def create_connection(address, *args, **kwargs):
        return original_connection(remap_address(address, routes), *args, **kwargs)

    with patch.object(socket, "create_connection", create_connection):
        if not mcp_subprocess or os.name == "nt":
            yield
            return
        from nexus import mcp_client
        original_open_session = mcp_client._open_session
        server = str(Path(__file__).resolve().parents[1] / "mcp_tools_server.py")

        async def open_session(stack, spec, *, prepared=None):
            if server in spec.args:
                spec = replace(spec, args=("-I", str(Path(__file__).resolve()),
                                          json.dumps(routes), server))
            return await original_open_session(stack, spec, prepared=prepared)

        with patch.object(mcp_client, "_open_session", open_session):
            yield


if __name__ == "__main__":
    # Linux test subprocess only; no environment or product allowlist changes.
    routes = {int(key): value for key, value in json.loads(sys.argv[1]).items()}
    with isolated_connections(routes):
        runpy.run_path(sys.argv[2], run_name="__main__")
