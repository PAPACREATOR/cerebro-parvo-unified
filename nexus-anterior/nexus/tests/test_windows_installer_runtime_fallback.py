"""Regression contract for Windows prerequisite installation fallback.

A winget/MSI installer may return a non-zero code even when a usable runtime is
already present (observed with Node.js MSI exit 1603). Nexus must verify the
actual executable boundary before deciding whether installation really failed.
"""

from nexus.contracts import ROOT


INSTALL = (ROOT / "windows" / "install-nexus-complete.ps1").read_text(encoding="utf-8")


def test_installer_checks_real_runtime_before_reinstalling():
    assert "function Test-PackageRuntime" in INSTALL
    assert "'OpenJS.NodeJS.LTS'" in INSTALL
    assert "@('node.exe','node')" in INSTALL
    assert "@('npm.cmd','npm')" in INSTALL
    assert "RUNTIME_PRESENT" in INSTALL


def test_nonzero_winget_exit_is_accepted_only_after_runtime_probe():
    assert "$installExit = $LASTEXITCODE" in INSTALL
    assert "if (Test-PackageRuntime $Id)" in INSTALL
    assert "RUNTIME_PRESENT_AFTER_WINGET_FAILURE_" in INSTALL
    assert "NEXUS_WINGET_INSTALL_FAILED:" in INSTALL


def test_prerequisite_report_keeps_observed_package_state():
    assert "$packageState = Ensure-WingetPackage $id" in INSTALL
    assert "$report.prerequisites[$id] = $packageState" in INSTALL


def test_winget_success_is_not_enough_without_real_executable():
    assert "NEXUS_WINGET_RUNTIME_MISSING_AFTER_INSTALL" in INSTALL
    assert "WINGET_INSTALLED_RUNTIME_VERIFIED" in INSTALL
    assert "winget lists " in INSTALL
    assert "its executable runtime is unavailable" in INSTALL
