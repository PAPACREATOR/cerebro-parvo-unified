"""Deterministic local MCP boundary for Nexus.

MCP is transport only. No model, agent or reasoning is used here.
The Kernel chooses the tool and arguments; this module only discovers and
executes explicitly allowed local MCP tools.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from typing import Any, Iterable

from nexus.native_mcp import configure
configure()

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from nexus.contracts import Blocked, ROOT


MAX_RESULT_BYTES = 1_000_000
BLOCKED_ENV_KEYS = {
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "GROQ_API_KEY",
}
ALLOWED_EXTRA_ENV_KEYS = {
    "OPEN_NOTEBOOK_URL",
    "MCP_TRANSPORT",
}


@dataclass(frozen=True)
class MCPServerSpec:
    command: str
    args: tuple[str, ...]
    env: dict[str, str] | None = None


def _reduced_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env: dict[str, str] = {}
    for key in ("SystemRoot", "WINDIR", "PATH", "PATHEXT", "TEMP", "TMP"):
        value = os.environ.get(key)
        if value:
            env[key] = value
    if extra:
        for key, value in extra.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise TypeError("MCP env must contain strings")
            upper = key.upper()
            if upper in BLOCKED_ENV_KEYS:
                raise Blocked("Credencial cloud proibida na fronteira MCP Nexus.")
            if upper not in ALLOWED_EXTRA_ENV_KEYS:
                raise Blocked("Variável de ambiente MCP não autorizada pelo Kernel.")
            env[upper] = value
    return env



@asynccontextmanager
async def _native_stdio(params, prepared=None):
    """Adapt the SDK's stdio framing to the verified native Windows process."""
    import anyio
    import mcp.types as types
    from mcp.shared.message import SessionMessage
    from nexus.windows_sandbox import launch_confined, task_environment

    read_sender, read = anyio.create_memory_object_stream(0)
    write, write_receiver = anyio.create_memory_object_stream(0)
    command = Path(params.command)
    if not command.is_absolute() or not command.is_file():
        raise Blocked("Executável MCP não autorizado.")
    with tempfile.TemporaryDirectory(prefix="nexus-mcp-") as temporary:
        work = Path(temporary).resolve()
        environment = task_environment(work)
        # Explicit provider settings are data; task/cache/profile roots cannot be
        # redirected by them, and never receive Host session/cloud credentials.
        protected = {"PATH","TEMP","TMP","USERPROFILE","APPDATA","LOCALAPPDATA","HOME"}
        if params.env:
            environment.update({k:v for k,v in params.env.items() if k.upper() not in protected})
        roots = [ROOT, Path(sys.prefix), Path(sys.base_prefix), command.parent]
        if command.parent.name.lower() == "scripts":
            roots.append(command.parent.parent)
        if prepared is not None:
            (work / "health-snapshot.json").write_text(json.dumps(prepared), encoding="utf-8")
        denied = (ROOT / "runtime",) if (ROOT / "runtime").is_dir() else ()
        from nexus.native_mcp import command_for
        proc = launch_confined(command_for([str(command), *params.args]), cwd=work,
                               env=environment, read_roots=tuple(dict.fromkeys(roots)), deny_roots=denied)

        diagnostic = bytearray()

        async def stdout_reader():
            async with read_sender:
                while True:
                    line = await anyio.to_thread.run_sync(proc.stdout.readline, MAX_RESULT_BYTES + 1)
                    if not line:
                        await anyio.to_thread.run_sync(proc.wait, 5)
                        break
                    if len(line) > MAX_RESULT_BYTES:
                        await read_sender.send(Blocked("Resposta MCP excede o limite Nexus."))
                        proc.kill()
                        break
                    try:
                        message = SessionMessage(types.JSONRPCMessage.model_validate_json(line))
                    except Exception:
                        message = Blocked("Resposta MCP não é JSON-RPC válido.")
                    await read_sender.send(message)

        async def stdin_writer():
            async with write_receiver:
                async for message in write_receiver:
                    raw = (message.message.model_dump_json(by_alias=True, exclude_none=True) + "\n").encode("utf-8")
                    if len(raw) > MAX_RESULT_BYTES:
                        raise Blocked("Pedido MCP excede o limite Nexus.")
                    await anyio.to_thread.run_sync(proc.stdin.write, raw)

        async def stderr_reader():
            size = 0
            while block := await anyio.to_thread.run_sync(proc.stderr.read, 65536):
                size += len(block)
                if len(diagnostic) < 8000:
                    diagnostic.extend(block[:8000-len(diagnostic)])
                if size > MAX_RESULT_BYTES:
                    proc.kill()
                    raise Blocked("Diagnóstico MCP excede o limite Nexus.")

        try:
            async with anyio.create_task_group() as group:
                group.start_soon(stdout_reader)
                group.start_soon(stdin_writer)
                group.start_soon(stderr_reader)
                try:
                    yield read, write
                finally:
                    proc.kill()  # Includes descendants; unblocks pending pipe reads.
                    group.cancel_scope.cancel()
        finally:
            if proc.returncode not in (None, 0):
                print(f"Nexus MCP exit {proc.returncode:#x}: " + diagnostic.decode("utf-8", errors="replace"), file=sys.stderr)
            proc.close()
            await read.aclose()
            await write.aclose()
            await read_sender.aclose()
            await write_receiver.aclose()

async def _open_session(stack: AsyncExitStack, spec: MCPServerSpec, *, prepared=None) -> ClientSession:
    params = StdioServerParameters(
        command=spec.command,
        args=list(spec.args),
        env=_reduced_env(spec.env),
    )
    if os.name == "nt":
        from nexus.windows_sandbox import inside_native_boundary
        # SDK children of a confined runner inherit its token and job. Direct
        # MCP callers use the same native boundary, never an unrestricted fallback.
        if inside_native_boundary():
            transport = stdio_client
        else:
            from functools import partial
            transport = partial(_native_stdio, prepared=prepared)
    else:
        transport = stdio_client
    read, write = await stack.enter_async_context(transport(params))
    session = await stack.enter_async_context(ClientSession(read, write))
    await session.initialize()
    return session


async def list_tools_async(spec: MCPServerSpec) -> list[dict[str, Any]]:
    async with AsyncExitStack() as stack:
        session = await _open_session(stack, spec)
        response = await session.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema,
            }
            for tool in response.tools
        ]


def _payload_from_result(result) -> dict[str, Any]:
    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        payload = structured
    else:
        texts = [
            part.text for part in result.content
            if getattr(part, "type", None) == "text"
        ]
        if len(texts) != 1:
            raise Blocked("Resposta MCP sem envelope único.")
        try:
            payload = json.loads(texts[0])
        except (TypeError, ValueError) as error:
            raise Blocked("Resposta MCP não é JSON estruturado.") from error

    if not isinstance(payload, dict):
        raise Blocked("Resposta MCP deve ser objeto JSON.")
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(raw) > MAX_RESULT_BYTES:
        raise Blocked("Resposta MCP excede o limite Nexus.")
    return payload


async def call_tool_async(
    spec: MCPServerSpec,
    tool_name: str,
    arguments: dict[str, Any],
    *,
    allowed_tools: Iterable[str],
) -> dict[str, Any]:
    allow = frozenset(allowed_tools)
    if tool_name not in allow:
        raise Blocked("Tool MCP não autorizada pelo Kernel.")
    if not isinstance(arguments, dict):
        raise TypeError("MCP arguments must be dict")

    pending_error: Blocked | None = None
    payload: dict[str, Any] | None = None

    prepared = None
    if (os.name == "nt" and tool_name in {"check_ace_step", "check_forge"}
            and str(ROOT / "mcp_tools_server.py") in spec.args):
        if arguments:
            raise Blocked("O diagnóstico local não aceita parâmetros externos.")
        from nexus.adapters.media_tools import check_ace_step, check_forge
        # Fixed read-only local endpoints are brokered by trusted Host code.
        # No credential/network capability is given to the MCP tool process.
        probe = check_ace_step if tool_name == "check_ace_step" else check_forge
        prepared = {tool_name: probe()}

    async with AsyncExitStack() as stack:
        session = await _open_session(stack, spec, prepared=prepared)
        try:
            available = {tool.name for tool in (await session.list_tools()).tools}
            if tool_name not in available:
                pending_error = Blocked("Tool MCP não existe no servidor.")
            else:
                result = await session.call_tool(tool_name, arguments)
                if result.isError:
                    details = " ".join(getattr(part, "text", "") for part in result.content)[:2000]
                    print("Nexus MCP tool diagnostic: " + details, file=sys.stderr)
                    pending_error = Blocked("Tool MCP devolveu erro.")
                else:
                    payload = _payload_from_result(result)
        except Blocked as error:
            pending_error = error
        except Exception as error:
            pending_error = Blocked("Tool MCP falhou de forma controlada.")
            pending_error.__cause__ = error

    if pending_error is not None:
        raise pending_error
    if payload is None:
        raise Blocked("Tool MCP terminou sem resultado.")
    return payload


def list_tools(spec: MCPServerSpec) -> list[dict[str, Any]]:
    import anyio
    return anyio.run(list_tools_async, spec)


def call_tool(
    spec: MCPServerSpec,
    tool_name: str,
    arguments: dict[str, Any],
    *,
    allowed_tools: Iterable[str],
) -> dict[str, Any]:
    import anyio
    from functools import partial
    return anyio.run(partial(call_tool_async, spec, tool_name, arguments,
                             allowed_tools=allowed_tools))
