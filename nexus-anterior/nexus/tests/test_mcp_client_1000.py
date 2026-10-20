"""1000-request real MCP stdio stress batch.

This is transport stress only: no model, no prompt, no agent, no AI.
"""
import asyncio
from contextlib import AsyncExitStack
from pathlib import Path
import sys

from nexus.mcp_client import MCPServerSpec, _open_session, _payload_from_result

ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(sys.executable).resolve()


def spec():
    return MCPServerSpec(
        command=str(PYTHON),
        args=("-u", str(ROOT / "tests/fixtures/mcp_test_server.py")),
    )


async def _run_1000():
    async with AsyncExitStack() as stack:
        session = await _open_session(stack, spec())
        count = 0

        # 700 exact Unicode ida/volta.
        alphabet = ("abcXYZ012345", "áéíóúçãõ", "日本語", "Δλ", "—_ []{}!?")
        for i in range(700):
            original = f"{i:04d}|" + "|".join(
                part[(i + n) % len(part):] + part[:(i + n) % len(part)]
                for n, part in enumerate(alphabet)
            )
            result = await session.call_tool("ping", {"value": original})
            assert result.isError is False, i
            payload = _payload_from_result(result)
            assert payload == {"echo": original, "authority": "NONE"}, i
            assert payload["echo"].encode("utf-8") == original.encode("utf-8"), i
            count += 1

        # 200 deterministic numeric calls, including negatives and zero.
        for i in range(200):
            value = (i - 100) * 1000003
            result = await session.call_tool("double", {"value": value})
            assert result.isError is False, i
            assert _payload_from_result(result) == {"value": value * 2}, i
            count += 1

        # 100 live rediscoveries: server stays stable and tool inventory does not drift.
        for i in range(100):
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            assert names == {"ping", "double", "explode"}, i
            count += 1

        assert count == 1000


def test_mcp_real_stdio_1000_request_batch():
    asyncio.run(_run_1000())
