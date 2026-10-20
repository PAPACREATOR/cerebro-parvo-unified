"""Real Nexus MCP stdio proof for the new public product routes.

The three OpenNotebook routes consume a deterministic prepared response so CI
does not claim a model ran. Music/web exercise their deterministic adapters.
Book is excluded here because its real proof is LibreOffice Writer.
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

import pytest

from nexus.adapters.runner import PROCESS_TO_TOOL
from nexus.tests._mcp_baseline import execute
from nexus.contracts import validate


pytestmark = pytest.mark.skipif(
    os.name == "nt",
    reason="Direct MCP route proof runs outside the Windows native boundary; Windows is covered by confinement/post-install gates.",
)


def _run_dir(tmp_path: Path) -> Path:
    run = tmp_path / "runs" / uuid.uuid4().hex
    run.mkdir(parents=True)
    return run


def _write_notebook_case(run: Path, route: str, index: int = 1) -> Path:
    source = f"Fonte factual {index}: Coimbra recebeu vinte caixas."
    path = run / "input.bin"
    path.write_text(source, encoding="utf-8")
    output = json.dumps({
        "title": f"{route} local",
        "body": f"Conteúdo candidato {route}.",
        "steps": ["primeiro passo", "segundo passo"],
        "quotes": [source],
    }, ensure_ascii=False)
    (run / "product-plan-response.json").write_text(json.dumps({
        "output": output,
        "model_id": "model:local-test",
        "transformation_id": "transformation:product-test",
    }, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.mark.parametrize("route", ["video", "podcast", "visual_podcast"])
def test_notebook_product_routes_cross_real_mcp_stdio(tmp_path, route):
    source = _write_notebook_case(_run_dir(tmp_path), route)
    envelope = execute(route, source)
    assert set(envelope) == {"result", "trace"}
    assert envelope["trace"]["process"] == route
    assert envelope["trace"]["summary"]["agents_executed"] == [PROCESS_TO_TOOL[route]]
    result = envelope["result"]
    assert validate("result", result)["outcome"] == "candidate"
    assert result["status"] == "UNKNOWN"
    assert result["ai_calls"] == 1
    assert result["evidence"][0]["capability"] == "open-notebook/product-plan"


def test_music_route_crosses_real_mcp_stdio(tmp_path):
    run = _run_dir(tmp_path)
    source = run / "input.bin"
    source.write_text(
        "Tema: memória e regresso\n"
        "Letra: Volto à rua onde cresci.\n"
        "Estilo: folk acústico português",
        encoding="utf-8",
    )
    envelope = execute("music", source)
    result = envelope["result"]
    assert envelope["trace"]["summary"]["agents_executed"] == ["music_plan_file"]
    assert validate("result", result)["outcome"] == "candidate"
    assert result["ai_calls"] == 0
    assert result["evidence"][0]["capability"] == "ace-step/production-spec"


def test_web_route_crosses_real_mcp_stdio_without_inventing_sources(tmp_path):
    run = _run_dir(tmp_path)
    source = run / "input.bin"
    source.write_text("Consulta: história da imprensa em Portugal", encoding="utf-8")
    envelope = execute("web", source)
    result = envelope["result"]
    assert envelope["trace"]["summary"]["agents_executed"] == ["web_plan_file"]
    assert validate("result", result)["outcome"] == "candidate"
    assert result["ai_calls"] == 0
    assert result["evidence"] == [{
        "capability": "web/query-spec",
        "status": "UNKNOWN",
        "value": "história da imprensa em Portugal",
    }]


def test_book_route_is_bound_to_writer_tool():
    assert PROCESS_TO_TOOL["book"] == "book_file"
