"""Functional Windows tests for the code-only Nexus sync script.

Uses disposable local Git repositories. The checkout still contains the literal
official GitHub origin; Git's insteadOf mechanism redirects network I/O to a
local bare repository only inside the disposable checkout.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "windows" / "sync-nexus-code.ps1"
BRANCH = "lab-open-notebook-avatar-20261004"
OFFICIAL = "https://github.com/PAPACREATOR/cerebro-parvo-.git"


pytestmark = pytest.mark.skipif(os.name != "nt", reason="PowerShell/Git Windows functional gate")


def run(*args, cwd=None, env=None, check=True):
    result = subprocess.run(
        [str(a) for a in args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if check and result.returncode:
        raise AssertionError(result.stdout + result.stderr)
    return result


def git(cwd, *args, check=True):
    return run("git.exe", *args, cwd=cwd, check=check)


def setup_repositories(tmp_path):
    remote = tmp_path / "remote.git"
    seed = tmp_path / "seed"
    checkout = tmp_path / "checkout"

    git(tmp_path, "init", "--bare", remote)
    git(tmp_path, "init", seed)
    git(seed, "config", "user.email", "nexus-test@example.invalid")
    git(seed, "config", "user.name", "Nexus Test")
    git(seed, "switch", "-c", BRANCH)
    (seed / "state.bin").write_bytes(b"v1\x00\n")
    git(seed, "add", "state.bin")
    git(seed, "commit", "-m", "v1")
    git(seed, "remote", "add", "origin", remote)
    git(seed, "push", "-u", "origin", BRANCH)

    git(tmp_path, "clone", "--branch", BRANCH, remote, checkout)
    git(checkout, "remote", "set-url", "origin", OFFICIAL)

    # Preserve the literal official remote while redirecting Git transport
    # inside this disposable test checkout only.
    local_url = remote.resolve().as_uri()
    git(checkout, "config", f"url.{local_url}.insteadOf", OFFICIAL)
    assert git(checkout, "config", "--get", "remote.origin.url").stdout.strip() == OFFICIAL
    return remote, seed, checkout


def advance(seed: Path, value: str):
    (seed / "state.bin").write_bytes(value.encode("ascii") + b"\x00\n")
    git(seed, "add", "state.bin")
    git(seed, "commit", "-m", value)
    git(seed, "push", "origin", BRANCH)
    return git(seed, "rev-parse", "HEAD").stdout.strip()


def invoke_sync(checkout: Path):
    return run(
        "powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
        "-File", SCRIPT, "-RepoRoot", checkout, "-Branch", BRANCH,
        cwd=checkout, check=False,
    )


def test_clean_checkout_fast_forwards_exactly_to_remote(tmp_path):
    _remote, seed, checkout = setup_repositories(tmp_path)
    target = advance(seed, "v2")

    result = invoke_sync(checkout)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "NEXUS CODE SYNC = PASS" in result.stdout
    assert git(checkout, "rev-parse", "HEAD").stdout.strip() == target
    assert (checkout / "state.bin").read_bytes() == b"v2\x00\n"
    assert git(checkout, "status", "--porcelain").stdout == ""


def test_dirty_checkout_refuses_remote_update_without_losing_local_bytes(tmp_path):
    _remote, seed, checkout = setup_repositories(tmp_path)
    target_v2 = advance(seed, "v2")
    first = invoke_sync(checkout)
    assert first.returncode == 0, first.stdout + first.stderr
    assert git(checkout, "rev-parse", "HEAD").stdout.strip() == target_v2

    local = b"LOCAL-UNCOMMITTED-\xc3\xa7\xc3\xa3o\n"
    (checkout / "state.bin").write_bytes(local)
    target_v3 = advance(seed, "v3")
    assert target_v3 != target_v2

    result = invoke_sync(checkout)

    assert result.returncode != 0
    assert "NEXUS_DIRTY_TREE" in (result.stdout + result.stderr)
    assert git(checkout, "rev-parse", "HEAD").stdout.strip() == target_v2
    assert (checkout / "state.bin").read_bytes() == local
    assert git(checkout, "status", "--porcelain").stdout.strip()
