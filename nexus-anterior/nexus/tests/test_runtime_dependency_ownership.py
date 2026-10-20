"""Fail-first contracts for the approved internal transport simplification."""
import subprocess
import sys
from types import SimpleNamespace

import pytest

from nexus.adapters import runner
from nexus.contracts import Blocked, ROOT


def test_core_constructs_host_without_importing_optional_mcp_runtime(tmp_path):
    script = r'''
import importlib.abc, sys
class NoOptionalMCP(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'mcp','trio','anyio'} or fullname in {
                'nexus.mcp_client','nexus.native_mcp','nexus.mcp_tools_server'}:
            raise ImportError('Optional MCP reached by the core: '+fullname)
sys.meta_path.insert(0, NoOptionalMCP())
from nexus.host import Host
host = Host(sys.argv[1])
run = host.store.create({'process':'verify','text':'original','filename':'','attachment':''})
assert host.store.state(run)['status'] == 'RUNNING'
'''
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path / "data")],
                            cwd=ROOT.parent, capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr.decode(errors="replace")


def test_runner_outside_native_boundary_cannot_own_a_product_launch(tmp_path, monkeypatch):
    from nexus import windows_sandbox
    source = tmp_path / "runs" / ("a" * 32) / "input.bin"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"original")
    launches = []
    def ARCHIVE_REDACTED_04_launch(*args, **kwargs):
        launches.append(args)
        pytest.fail("Runner created a second product sandbox instead of refusing")
    def refuse():
        raise Blocked("Falta a fronteira nativa do Host.")
    monkeypatch.setattr(runner, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(windows_sandbox, "inside_native_boundary", lambda: False)
    monkeypatch.setattr(windows_sandbox, "require_native_boundary", refuse)
    monkeypatch.setattr(windows_sandbox, "launch_confined", ARCHIVE_REDACTED_04_launch)
    with pytest.raises(Blocked):
        runner.execute("verify", source)
    assert not launches
    assert source.read_bytes() == b"original"


def test_core_dependencies_do_not_force_the_optional_transport():
    assert (ROOT / "requirements.txt").read_text("utf-8").splitlines() == ["jsonschema==4.26.0"]
    assert (ROOT / "requirements-mcp.txt").read_text("utf-8").splitlines() == ["mcp==1.23.2", "trio==0.34.0"]
    test_requirements = (ROOT / "requirements-test.txt").read_text("utf-8").splitlines()
    assert "-r requirements.txt" in test_requirements
    assert "-r requirements-mcp.txt" in test_requirements
