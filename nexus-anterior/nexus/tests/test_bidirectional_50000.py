"""50,000 bidirectional cases: 25k internal + 25k real external MCP calls.

Counts are explicit. External means a real stdio MCP server process and JSON-RPC
round-trip. Calls are split across bounded persistent sessions so the production
1 MB diagnostic limit remains unchanged; mocks do not count as external calls.
"""
from __future__ import annotations

import asyncio
import os
from contextlib import AsyncExitStack
from pathlib import Path
import sys

import pytest

from nexus.frontdoor import ParsedInput
from nexus.natural_bridge import (
    from_markdown,
    kernel_from_notebook_boundary,
    kernel_to_notebook,
    to_markdown,
)
from nexus.mcp_client import MCPServerSpec, _open_session, _payload_from_result

ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(sys.executable).resolve()

INTERNAL_CASES = 25_000
EXTERNAL_CALLS = 25_000
TOTAL_CASES = INTERNAL_CASES + EXTERNAL_CALLS
EXTERNAL_BATCH_SIZE = 2_500
EXTERNAL_SESSIONS = EXTERNAL_CALLS // EXTERNAL_BATCH_SIZE
EXTERNAL_CONCURRENCY = 100

pytestmark = pytest.mark.skipif(os.environ.get("NEXUS_RUN_50K") != "1", reason="explicit 50k stress gate")


def _text(i: int) -> str:
    alphabets = (
        "ação memória proveniência",
        "日本語 dados",
        "Δλ matemática",
        "livro—capítulo",
        "[]{}!? 0123456789",
    )
    return f"{i:05d}|" + "|".join(
        part[(i + n) % len(part):] + part[:(i + n) % len(part)]
        for n, part in enumerate(alphabets)
    )


def test_internal_bidirectional_25000_exact_roundtrips():
    count = 0
    intents = ("arquivo", "web", "fontes", "trabalhar", "perguntar", "calcular", "tema")
    for i in range(INTERNAL_CASES):
        original = _text(i)
        parsed = ParsedInput(
            status="RESOLVED",
            intent=intents[i % len(intents)],
            original=original,
            content=original,
            parser="stress-explicit-v1",
            explicit=bool(i & 1),
        )
        markdown = to_markdown(parsed)
        decoded = from_markdown(markdown)
        assert decoded["text"].encode("utf-8") == original.encode("utf-8"), i
        assert decoded["intent"] == parsed.intent, i
        packet = kernel_to_notebook(markdown)
        restored_markdown = kernel_from_notebook_boundary(packet)
        assert restored_markdown.encode("utf-8") == markdown.encode("utf-8"), i
        assert from_markdown(restored_markdown)["text"] == original, i
        count += 1
    assert count == INTERNAL_CASES


def _spec() -> MCPServerSpec:
    return MCPServerSpec(
        command=str(PYTHON),
        args=("-u", str(ROOT / "tests/fixtures/mcp_test_server.py")),
    )


async def _external_25000() -> int:
    count = 0

    async def one(session, i: int) -> int:
        original = _text(i)
        result = await session.call_tool("ping", {"value": original})
        assert result.isError is False, i
        payload = _payload_from_result(result)
        assert payload == {"echo": original, "authority": "NONE"}, i
        assert payload["echo"].encode("utf-8") == original.encode("utf-8"), i
        return 1

    for batch in range(EXTERNAL_SESSIONS):
        async with AsyncExitStack() as stack:
            session = await _open_session(stack, _spec())
            start = batch * EXTERNAL_BATCH_SIZE
            stop = start + EXTERNAL_BATCH_SIZE
            for chunk_start in range(start, stop, EXTERNAL_CONCURRENCY):
                chunk_stop = min(chunk_start + EXTERNAL_CONCURRENCY, stop)
                completed = await asyncio.gather(
                    *(one(session, i) for i in range(chunk_start, chunk_stop))
                )
                count += sum(completed)
    return count


def test_external_mcp_real_stdio_25000_bidirectional_calls():
    count = asyncio.run(_external_25000())
    assert count == EXTERNAL_CALLS


def test_declared_total_is_exactly_50000():
    assert INTERNAL_CASES == 25_000
    assert EXTERNAL_CALLS == 25_000
    assert TOTAL_CASES == 50_000
    assert EXTERNAL_BATCH_SIZE == 2_500
    assert EXTERNAL_SESSIONS == 10
    assert EXTERNAL_CONCURRENCY == 100
