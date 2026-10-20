"""Actual Windows bootstrap and Git; preparation peers never install software."""
import json
import os
from pathlib import Path
import shutil

import pytest

from nexus.tests.test_code_sync_functional import (
    BRANCH, OFFICIAL, git, run, setup_repositories,
)

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows bootstrap execution NOT RUN on this OS")


@pytest.fixture
def checkout(tmp_path):
    _remote, _seed, repo = setup_repositories(tmp_path)
    windows = repo / "nexus/windows"
    windows.mkdir(parents=True)
    for name in ["bootstrap-nexus-local.ps1", "sync-nexus-code.ps1", "nexus-launcher.py"]:
        shutil.copyfile(ROOT / "windows" / name, windows / name)
    (repo / ".gitignore").write_text(".venv/\nnexus/runtime/\n", encoding="utf-8")
    (windows / "prepare-nexus-core.ps1").write_text(r'''
param($RepoRoot,$ToolsRoot)
$ErrorActionPreference='Stop'
$null=New-Item -ItemType Directory -Force -Path $ToolsRoot
$scripts=Join-Path $RepoRoot '.venv\Scripts'
$null=New-Item -ItemType Directory -Force -Path $scripts
$python=Join-Path $scripts 'python.exe'
Set-Content -LiteralPath $python -Value 'test fixture, never executed'
Set-Content -LiteralPath (Join-Path $scripts 'pythonw.exe') -Value 'test fixture, never executed'
Set-Content -LiteralPath (Join-Path $ToolsRoot 'preparation-called') -Value 'called'
$head=(& git.exe -C $RepoRoot rev-parse HEAD).Trim()
@{status='PASS';head=$head;python=$python}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $ToolsRoot 'pc-core-report.json') -Encoding UTF8
''', encoding="utf-8")
    for name, report in [("inventory-external-tools.ps1", "external-tools-inventory.json"),
                         ("plan-external-provisioning.ps1", "external-provision-plan.json")]:
        (windows / name).write_text(
            "param($ToolsRoot)\n@{status='fixture'}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $ToolsRoot '" + report + "') -Encoding UTF8\n",
            encoding="utf-8")
    git(repo, "config", "user.name", "Nexus Test")
    git(repo, "config", "user.email", "nexus-test@example.invalid")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "bootstrap peers")
    git(repo, "push", "origin", BRANCH)
    return repo, tmp_path / "tools"


def bootstrap(repo, tools, *args):
    return run("powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
               "-File", repo / "nexus/windows/bootstrap-nexus-local.ps1",
               "-RepoRoot", repo, "-ToolsRoot", tools, *args, cwd=repo, check=False)


def test_bootstrap_without_explicit_human_authorization_has_no_effects(checkout):
    repo, tools = checkout
    before = git(repo, "rev-parse", "HEAD").stdout.strip()
    result = bootstrap(repo, tools)
    assert result.returncode != 0
    assert "NEXUS_PREPARE_AUTHORIZATION_REQUIRED" in result.stdout + result.stderr
    assert not tools.exists()
    assert git(repo, "rev-parse", "HEAD").stdout.strip() == before
    assert git(repo, "status", "--porcelain").stdout == ""


def test_bootstrap_core_exact_head_binds_existing_thin_launcher(checkout):
    repo, tools = checkout
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    result = bootstrap(repo, tools, "-AuthorizePrepare", "-ExpectedHead", head)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((tools / "local-bootstrap-report.json").read_text("utf-8-sig"))
    assert report["head"] == head
    assert report["external_provisioning"] == "BLOCKED_BY_POLICY"
    config = json.loads((tools / "bin/nexus-launcher.json").read_text("utf-8-sig"))
    assert config["expected_head"] == head
    assert config["expected_origin"] == OFFICIAL
    assert Path(config["repo_root"]).resolve() == repo.resolve()
    assert (tools / "bin/nexus-launcher.py").read_bytes() == (repo / "nexus/windows/nexus-launcher.py").read_bytes()
    assert (tools / "Nexus.lnk").is_file()
    assert git(repo, "status", "--porcelain").stdout == ""


@pytest.mark.parametrize("fault", ["missing-head", "wrong-head", "dirty", "untracked", "origin"])
def test_bootstrap_blocks_unaccepted_checkout_before_preparation(checkout, fault):
    repo, tools = checkout
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    args = ["-AuthorizePrepare"]
    if fault != "missing-head":
        args += ["-ExpectedHead", "0" * 40 if fault == "wrong-head" else head]
    if fault == "dirty":
        (repo / "state.bin").write_bytes(b"uncommitted-human-bytes")
    elif fault == "untracked":
        (repo / "unknown.py").write_text("# unreviewed", encoding="utf-8")
    elif fault == "origin":
        git(repo, "remote", "set-url", "origin", "https://example.invalid/repo.git")
    before = {p: p.read_bytes() for p in [repo / "state.bin", repo / "nexus/windows/bootstrap-nexus-local.ps1"]}
    result = bootstrap(repo, tools, *args)
    assert result.returncode != 0
    assert not tools.exists()
    assert git(repo, "rev-parse", "HEAD").stdout.strip() == head
    assert all(p.read_bytes() == data for p, data in before.items())


def test_bootstrap_legitimate_update_requires_new_explicit_binding(checkout):
    repo, tools = checkout
    old = git(repo, "rev-parse", "HEAD").stdout.strip()
    first = bootstrap(repo, tools, "-AuthorizePrepare", "-ExpectedHead", old)
    assert first.returncode == 0, first.stdout + first.stderr
    (repo / "state.bin").write_bytes(b"approved-new-version")
    git(repo, "add", "state.bin")
    git(repo, "commit", "-m", "approved update")
    current = git(repo, "rev-parse", "HEAD").stdout.strip()
    refused = bootstrap(repo, tools, "-AuthorizePrepare", "-ExpectedHead", old)
    assert refused.returncode != 0
    config = tools / "bin/nexus-launcher.json"
    assert json.loads(config.read_text("utf-8-sig"))["expected_head"] == old
    accepted = bootstrap(repo, tools, "-AuthorizePrepare", "-ExpectedHead", current)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    assert json.loads(config.read_text("utf-8-sig"))["expected_head"] == current
