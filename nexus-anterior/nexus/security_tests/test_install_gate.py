"""Provisioning contract: real entrypoints must refuse before any changes.

The first baseline uses tripwires to observe unsafe paths without performing
their side effects. Native repetitions after the guard use no such overrides.
"""
import os
import subprocess
import sys

import pytest
from nexus.contracts import ROOT

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Real Windows entrypoints only")
LEGACY_MARKER = "NEXUS_PROTECTED_PROVISIONING_PENDING"
AUTHORIZED_INSTALL_MARKER = "NEXUS_INSTALL_AUTHORIZATION_REQUIRED"
TRIPWIRE = "NEXUS_TEST_UNPROTECTED_SIDE_EFFECT"
PS_CASES = [
    ("windows/install-nexus-complete.ps1", "ToolsRoot", [], None, AUTHORIZED_INSTALL_MARKER),
    ("windows/install-media-tools.ps1", "ToolsRoot", [], None, AUTHORIZED_INSTALL_MARKER),
    ("windows/install-media-tools.ps1", "ToolsRoot", ["SkipAceStep", "SkipForge"], None, AUTHORIZED_INSTALL_MARKER),
    ("windows/sync-nexus-pc.ps1", "ToolsRoot", [], None, LEGACY_MARKER),
    ("windows/sync-nexus-pc.ps1", "ToolsRoot", ["SkipMediaInstall", "SkipMediaStart"], None, LEGACY_MARKER),
    ("lab/open_notebook_avatar/install-windows.ps1", "OpenNotebookRoot", [], "cpu", AUTHORIZED_INSTALL_MARKER),
    ("lab/open_notebook_avatar/install-windows.ps1", "OpenNotebookRoot", [], "cuda", AUTHORIZED_INSTALL_MARKER),
    ("windows/setup-isolation.ps1", None, [], None, LEGACY_MARKER),
]

@pytest.mark.parametrize("relative,root_parameter,flags,device,marker", PS_CASES)
@pytest.mark.parametrize("mode", ["tripwires", "native"])
def test_windows_provisioning_refuses_before_changes(tmp_path, relative, root_parameter, flags, device, marker, mode):
    target = tmp_path / "not-created"
    original = tmp_path / "original"
    original.write_bytes(b"original")
    wrapper = tmp_path / "invoke-guard.ps1"
    overrides = ""
    if mode == "tripwires":
        overrides = "".join(
            f"function global:{name} {{ throw '{TRIPWIRE}' }}\n"
            for name in ("New-Item", "Get-Command", "Resolve-Path", "Read-Host",
                         "Get-LocalUser", "New-LocalUser", "Start-Process", "Invoke-WebRequest"))
    options = "$Options = @{}\n"
    if root_parameter:
        options += f"$Options['{root_parameter}'] = $Target\n"
    for flag in flags:
        options += f"$Options['{flag}'] = $true\n"
    if device:
        options += f"$Options['ApiPython'] = $ApiPython\n$Options['Device'] = '{device}'\n"
    wrapper.write_text(
        "param([string]$Source, [string]$Target, [string]$ApiPython)\n"
        "$ErrorActionPreference = 'Stop'\n" + overrides + options +
        "& $Source @Options\n", encoding="utf-8-sig")
    result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-File",
        str(wrapper), str(ROOT / relative), str(target), sys.executable], cwd=tmp_path,
        capture_output=True, text=True, timeout=15)
    observed = result.stdout + result.stderr
    assert result.returncode != 0, observed
    assert marker in observed, observed
    assert TRIPWIRE not in observed, observed
    assert not target.exists()
    assert original.read_bytes() == b"original"


@pytest.mark.parametrize("entry", ["cli", "function"])
@pytest.mark.parametrize("mode", ["tripwires", "native"])
def test_model_provisioning_refuses_before_downloads(tmp_path, entry, mode):
    target = tmp_path / "not-created"
    original = tmp_path / "original"
    original.write_bytes(b"original")
    wrapper = """
import pathlib, runpy, sys, types, urllib.request
source, target, entry, mode = sys.argv[1:]
def unprotected(*args, **kwargs):
    raise RuntimeError("NEXUS_TEST_UNPROTECTED_SIDE_EFFECT")
if mode == "tripwires":
    pathlib.Path.mkdir = unprotected
    urllib.request.urlopen = unprotected
    sys.modules["gdown"] = types.SimpleNamespace(download=unprotected)
if entry == "cli":
    sys.argv = [source, target]
    runpy.run_path(source, run_name="__main__")
else:
    runpy.run_path(source)["provision"](pathlib.Path(target))
"""
    result = subprocess.run([sys.executable, "-I", "-B", "-c", wrapper,
        str(ROOT / "lab/open_notebook_avatar/provision_models.py"), str(target), entry, mode],
        cwd=tmp_path, capture_output=True, text=True, timeout=15)
    observed = result.stdout + result.stderr
    assert result.returncode != 0, observed
    assert AUTHORIZED_INSTALL_MARKER in observed, observed
    assert TRIPWIRE not in observed, observed
    assert not target.exists()
    assert original.read_bytes() == b"original"
