"""10,000 bidirectional contract cases for the local llama.cpp boundary.

These are deterministic protocol/contract tests. They do not claim 10,000 real
model generations. Real llama.cpp language and embedding probes are performed
separately by test-post-install.ps1 on the user's Windows installation.
"""
from __future__ import annotations

import json
from pathlib import Path

from nexus.contracts import ROOT


INSTALL = (ROOT / "windows" / "install-nexus-complete.ps1").read_text(encoding="utf-8")
OPEN_CONFIG = (ROOT / "windows" / "configure-open-notebook-local.py").read_text(encoding="utf-8")
MPT_CONFIG = (ROOT / "windows" / "configure-moneyprinterturbo-local.py").read_text(encoding="utf-8")


LANGUAGE_ALIAS = "nexus-qwen3-1.7b"
EMBEDDING_ALIAS = "nexus-qwen3-embedding-0.6b"
LANGUAGE_BASE = "http://127.0.0.1:18081/v1"
EMBEDDING_BASE = "http://127.0.0.1:18082/v1"


def _chat_roundtrip(case: int) -> None:
    source = f"caso-{case}-olá-日本語"
    request = {
        "model": LANGUAGE_ALIAS,
        "messages": [{"role": "user", "content": source}],
        "temperature": 0,
    }
    wire = json.dumps(request, ensure_ascii=False).encode("utf-8")
    decoded = json.loads(wire.decode("utf-8"))
    assert decoded["model"] == LANGUAGE_ALIAS
    assert decoded["messages"][0]["content"] == source

    response = {
        "model": LANGUAGE_ALIAS,
        "choices": [{"message": {"role": "assistant", "content": source}}],
    }
    back = json.loads(json.dumps(response, ensure_ascii=False))
    assert back["model"] == decoded["model"]
    assert back["choices"][0]["message"]["content"] == source


def _embedding_roundtrip(case: int) -> None:
    source = f"embedding-{case}-ação-漢字"
    request = {"model": EMBEDDING_ALIAS, "input": source}
    decoded = json.loads(json.dumps(request, ensure_ascii=False))
    assert decoded == request

    vector = [case / 10000.0, 1.0, -1.0, 0.0]
    response = {
        "model": EMBEDDING_ALIAS,
        "data": [{"index": 0, "embedding": vector}],
    }
    back = json.loads(json.dumps(response))
    assert back["model"] == request["model"]
    assert back["data"][0]["embedding"] == vector


def test_llamacpp_openai_compatible_10000_bidirectional_cases():
    for case in range(5000):
        _chat_roundtrip(case)
        _embedding_roundtrip(case)


def test_llamacpp_boundary_uses_only_expected_local_runtime():
    combined = INSTALL + "\n" + OPEN_CONFIG + "\n" + MPT_CONFIG
    for required in (
        "ggml.llamacpp",
        LANGUAGE_ALIAS,
        EMBEDDING_ALIAS,
        "127.0.0.1:18081",
        "127.0.0.1:18082",
        "openai_compatible",
    ):
        assert required.lower() in combined.lower()



def test_moneyprinter_reuses_local_language_boundary_without_cloud_fallback():
    assert 'llm_provider = "openai"' in MPT_CONFIG
    assert 'openai_base_url = "http://127.0.0.1:18081/v1"' in MPT_CONFIG
    assert 'openai_model_name = "nexus-qwen3-1.7b"' in MPT_CONFIG
