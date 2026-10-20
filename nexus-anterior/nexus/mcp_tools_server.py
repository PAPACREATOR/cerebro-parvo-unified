"""Nexus-owned deterministic MCP tool server.

Transport only. No model, agent, memory, approval or Store access.
Each tool delegates to an already-bounded adapter. Authority remains in
Host/Store. External-tool health probes never mutate Nexus state.
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# Load the known package directly: LPAC can read Nexus without being granted
# directory listing/read access to the repository or the human's parent folder.
if __package__ in (None, ""):
    import importlib.util
    package_root = Path(__file__).absolute().parents[0]
    package_spec = importlib.util.spec_from_file_location(
        "nexus", package_root / "__init__.py",
        submodule_search_locations=[str(package_root)])
    package = importlib.util.module_from_spec(package_spec)
    sys.modules["nexus"] = package
    package_spec.loader.exec_module(package)

from nexus.native_mcp import configure
configure()

from mcp.server.fastmcp import FastMCP

from nexus.adapters.verify_direct import execute as verify
from nexus.adapters.notebook import run as interpret
from nexus.adapters.languagetool import run as proofread
from nexus.adapters.office import run as convert_pdf
from nexus.adapters.product_routes import run_open_notebook as run_product_plan
from nexus.adapters.product_routes import run_music as run_music_plan
from nexus.adapters.product_routes import run_web as run_web_plan
from nexus.adapters.media_tools import check_ace_step as ace_health
from nexus.adapters.media_tools import check_forge as forge_health
from nexus.contracts import Blocked, strict_json


mcp = FastMCP("nexus-local-tools")


def _input(value: str) -> Path:
    if os.name == "nt":
        from nexus.windows_sandbox import require_native_boundary
        require_native_boundary()
    if not isinstance(value, str) or not value:
        raise Blocked("Input MCP inválido.")
    path = Path(value)
    if os.name == "nt" and path.parent.resolve() != Path.cwd().resolve():
        raise Blocked("Input MCP fora da área atribuída.")
    if not path.is_absolute() or path.name != "input.bin" or not path.is_file():
        raise Blocked("Input MCP não autorizado.")
    parent = path.parent
    if parent.name == "" or parent.parent.name != "runs":
        raise Blocked("Input MCP fora de um run Nexus.")
    return path.resolve()


@mcp.tool()
def verify_file(input_path: str) -> dict:
    return verify(_input(input_path))["result"]


@mcp.tool()
def interpret_file(input_path: str) -> dict:
    return interpret(_input(input_path))


@mcp.tool()
def proofread_file(input_path: str) -> dict:
    return proofread(_input(input_path))


@mcp.tool()
def convert_pdf_file(input_path: str) -> dict:
    return convert_pdf(_input(input_path))


@mcp.tool()
def video_plan_file(input_path: str) -> dict:
    return run_product_plan(_input(input_path), "video")


@mcp.tool()
def podcast_plan_file(input_path: str) -> dict:
    return run_product_plan(_input(input_path), "podcast")


@mcp.tool()
def visual_podcast_plan_file(input_path: str) -> dict:
    return run_product_plan(_input(input_path), "visual_podcast")


@mcp.tool()
def book_file(input_path: str) -> dict:
    return convert_pdf(_input(input_path))


@mcp.tool()
def music_plan_file(input_path: str) -> dict:
    return run_music_plan(_input(input_path))


@mcp.tool()
def web_plan_file(input_path: str) -> dict:
    return run_web_plan(_input(input_path))


def _health(name, probe):
    if os.name != "nt":
        return probe()
    from nexus.windows_sandbox import require_native_boundary
    require_native_boundary()
    snapshot = Path.cwd() / "health-snapshot.json"
    if not snapshot.is_file():
        raise Blocked("Falta o diagnóstico delimitado do Host.")
    value = strict_json(snapshot.read_bytes()).get(name)
    expected = "http://127.0.0.1:8001" if name == "check_ace_step" else "http://127.0.0.1:7861"
    if not isinstance(value, dict) or value.get("authority") != "NONE" or value.get("endpoint") != expected:
        raise Blocked("Diagnóstico local inválido.")
    return value


@mcp.tool()
def check_ace_step() -> dict:
    return _health('check_ace_step', ace_health)


@mcp.tool()
def check_forge() -> dict:
    return _health('check_forge', forge_health)


if __name__ == "__main__":
    mcp.run(transport="stdio")
