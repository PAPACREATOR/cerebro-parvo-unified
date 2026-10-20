from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "windows" / "prepare-nexus-core.ps1").read_text(encoding="utf-8")


def test_core_prepare_keeps_provisioning_separate():
    assert "sync-nexus-pc.ps1" in SCRIPT
    assert "install-media-tools.ps1" in SCRIPT
    assert "NEXUS_PROTECTED_PROVISIONING_PENDING" in SCRIPT
    assert "BLOCKED_BY_POLICY" in SCRIPT
    assert "Start-ACE-Step-Nexus.cmd" not in SCRIPT
    assert "Start-Forge-Nexus.cmd" not in SCRIPT


def test_core_prepare_only_creates_local_venv_and_reports():
    assert "'.venv'" in SCRIPT
    assert "nexus/requirements-test.txt" in SCRIPT
    assert "C:\\Nexus-Tools" in SCRIPT
    assert "pc-core-report.json" in SCRIPT
    assert "winget" not in SCRIPT.lower()
    assert "New-LocalUser" not in SCRIPT
    assert "Set-Acl" not in SCRIPT


def test_core_prepare_runs_same_main_suites():
    for suite in ("core", "blocks", "practical", "all"):
        assert f"'{suite}'" in SCRIPT
    assert "check-nexus.ps1" in SCRIPT


def test_core_prepare_runs_bidirectional_and_security_gates():
    for name in (
        "test_authority_10000.py", "test_state_concurrency.py", "test_install_gate.py",
        "test_native_boundary.py", "test_windows_hash.py", "test_confinement_gate.py",
        "test_reverse_flow.py", "test_open_notebook_kernel_e2e.py",
    ):
        assert name in SCRIPT


def test_core_prepare_refuses_wrong_or_dirty_repository():
    assert "NEXUS_WRONG_ORIGIN" in SCRIPT
    assert "NEXUS_DIRTY_TREE" in SCRIPT
    assert "https://github.com/PAPACREATOR/cerebro-parvo-.git" in SCRIPT


def test_core_prepare_requires_python_312_instead_of_installing_system_python():
    assert "NEXUS_PYTHON_312_REQUIRED" in SCRIPT
    assert "winget" not in SCRIPT.lower()
    assert "Python 3.12" in SCRIPT


def test_core_prepare_is_powershell_5_compatible_for_security_arguments():
    assert "*$security" not in SCRIPT
    assert "$securityArgs = @('-m','pytest') + $security + @('-q','-o','pythonpath=.')" in SCRIPT
    assert "-ArgumentList $securityArgs" in SCRIPT


def test_core_prepare_selects_one_git_executable_deterministically():
    assert "Get-Command git.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1" in SCRIPT


def test_core_prepare_selects_one_python_launcher_deterministically():
    assert "Get-Command py.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1" in SCRIPT
    assert "Get-Command python.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1" in SCRIPT
