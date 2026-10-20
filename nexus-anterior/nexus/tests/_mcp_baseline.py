"""Frozen transport A for regression only; never imported by the product.

The former diagnostic sandbox wrapper belongs to this protocol fixture.
Production execution remains owned by Host, which has separate native E2E.
"""
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

if __package__ in (None, ""):
    import importlib.util
    package_root = Path(__file__).absolute().parents[1]
    spec = importlib.util.spec_from_file_location(
        "nexus", package_root / "__init__.py", submodule_search_locations=[str(package_root)])
    package = importlib.util.module_from_spec(spec)
    sys.modules["nexus"] = package
    spec.loader.exec_module(package)

from nexus.adapters.runner import PROCESS_TO_TOOL, collect_artifact, prepare_task
from nexus.contracts import Blocked, ROOT, strict_json


def _confined(process, input_path):
    from nexus.windows_sandbox import launch_confined, task_environment
    path = Path(input_path).resolve()
    with tempfile.TemporaryDirectory(prefix=".nexus-task-", dir=path.parent.parent.parent.parent) as temporary:
        work = Path(temporary) / "runs" / uuid.uuid4().hex
        work.mkdir(parents=True)
        roots = prepare_task(process, path, work)
        command = [sys.executable, "-I", str(Path(__file__).absolute()), process, str(work / "input.bin")]
        with launch_confined(command, cwd=work, env=task_environment(work), read_roots=roots,
                             deny_roots=(path.parent.parent.parent,)) as proc:
            stdout, stderr = proc.communicate(timeout=150 if process in {"interpret", "video", "podcast", "visual_podcast"} else 75)
            if proc.returncode:
                raise Blocked("A execução MCP de diagnóstico falhou.")
        envelope = strict_json(stdout)
        if not isinstance(envelope, dict) or set(envelope) != {"result", "trace"}:
            raise Blocked("Resposta de diagnóstico inválida.")
        collect_artifact(envelope, work, path.parent)
        return envelope


def execute(process, input_path):
    tool = PROCESS_TO_TOOL.get(process)
    if tool is None:
        raise Blocked("Processo indisponível.")
    if os.name == "nt":
        from nexus.windows_sandbox import inside_native_boundary
        if not inside_native_boundary():
            return _confined(process, input_path)
    from nexus.mcp_client import MCPServerSpec, call_tool
    result = call_tool(MCPServerSpec(command=sys.executable,
                                    args=("-I", str(ROOT / "mcp_tools_server.py"))),
                       tool, {"input_path": str(Path(input_path).resolve())}, allowed_tools={tool})
    trace = {"engine": "nexus/python-mcp", "version": "1.0.0", "process": process,
             "summary": {"usage": {"total_tokens": 0}, "agents_executed": [tool]},
             "events": [{"type": "mcp.tool.completed", "step": tool}]}
    return {"result": result, "trace": trace}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        print(json.dumps(execute(*sys.argv[1:3]), ensure_ascii=False))
    except Exception:
        print("MCP de diagnóstico rejeitado.", file=sys.stderr)
        raise SystemExit(1)
