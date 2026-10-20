"""Pure contract tests for the documentary lab bridge.

No model, network service, GPU or external tool is invoked here. Real rendering
remains a separate Windows acceptance gate.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from nexus.contracts import ROOT


def load_bridge():
    path = ROOT / "windows" / "documentary_bridge.py"
    spec = importlib.util.spec_from_file_location("nexus_documentary_bridge_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


bridge = load_bridge()


def valid_storyboard():
    return {
        "title": "Teste documental",
        "script": "Texto factual suficientemente longo para ultrapassar o limite mínimo de validação. " * 3,
        "scenes": [
            {"visual_prompt": f"Documentary scene {index}", "seconds": 8}
            for index in range(1, 7)
        ],
    }


def test_storyboard_contract_accepts_minimum_shape():
    value = bridge.validate_storyboard(valid_storyboard())
    assert value["title"] == "Teste documental"
    assert len(value["scenes"]) == 6


@pytest.mark.parametrize(
    "mutation",
    [
        lambda v: v.update(extra=True),
        lambda v: v["scenes"][0].update(extra=True),
        lambda v: v["scenes"][0].update(seconds=True),
        lambda v: v["scenes"][0].update(seconds=2),
        lambda v: v["scenes"][0].update(visual_prompt=""),
        lambda v: v.update(script="curto"),
    ],
)
def test_storyboard_contract_fails_closed(mutation):
    value = valid_storyboard()
    mutation(value)
    with pytest.raises(bridge.BridgeError):
        bridge.validate_storyboard(value)


@pytest.mark.parametrize("aspect,expected", [
    ("16:9", (768, 432)),
    ("9:16", (432, 768)),
    ("1:1", (512, 512)),
])
def test_forge_dimensions_are_bounded(aspect, expected):
    assert bridge.forge_dimensions(aspect) == expected


def test_forge_dimensions_reject_unknown_ratio():
    with pytest.raises(bridge.BridgeError):
        bridge.forge_dimensions("4:3")


def test_source_contract_preserves_research_and_brief(tmp_path):
    source = tmp_path / "fontes.txt"
    source.write_text("Facto A\nFacto B", encoding="utf-8")
    value = bridge.load_source(source, "Documentário de teste", 4)
    assert "Documentário de teste" in value
    assert "Approximately 4 minutes" in value
    assert "Facto A" in value


def test_source_contract_rejects_binary_nul(tmp_path):
    source = tmp_path / "fontes.txt"
    source.write_bytes(b"abc\x00def")
    with pytest.raises(bridge.BridgeError):
        bridge.load_source(source, "Teste", 4)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/v1",
        "http://192.168.1.10:5055/api",
        "file:///C:/Windows/win.ini",
    ],
)
def test_network_helpers_reject_non_local_endpoints_before_io(url):
    with pytest.raises(bridge.BridgeError, match="Non-local"):
        bridge.get_local_json(url)


def test_moneyprinter_runtime_shape_is_exact(tmp_path):
    output = tmp_path / "out"
    output.mkdir()
    with pytest.raises(bridge.BridgeError, match="wrong shape"):
        bridge.run_moneyprinter(
            {"root": str(tmp_path)},
            valid_storyboard(),
            [],
            output,
            "16:9",
        )
