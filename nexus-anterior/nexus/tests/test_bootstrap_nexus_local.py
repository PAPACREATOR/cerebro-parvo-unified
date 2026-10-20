from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "windows" / "bootstrap-nexus-local.ps1").read_text(encoding="utf-8")


def test_bootstrap_runs_sync_then_core_then_inventory_then_plan():
    sync = SCRIPT.index("sync-nexus-code.ps1")
    prepare = SCRIPT.index("prepare-nexus-core.ps1")
    inventory = SCRIPT.index("inventory-external-tools.ps1")
    plan = SCRIPT.index("plan-external-provisioning.ps1")
    assert sync < prepare < inventory < plan
    assert "NEXUS_STEP_FAILED" in SCRIPT


def test_bootstrap_never_calls_guarded_provisioning():
    ARCHIVE_REDACTED_04 = (
        "sync-nexus-pc.ps1",
        "install-media-tools.ps1",
        "install-windows.ps1",
        "setup-isolation.ps1",
        "Start-ACE-Step-Nexus.cmd",
        "Start-Forge-Nexus.cmd",
    )
    for token in ARCHIVE_REDACTED_04:
        assert token not in SCRIPT
    assert "external_provisioning = 'BLOCKED_BY_POLICY'" in SCRIPT


def test_bootstrap_requires_core_report_matching_current_head():
    assert "pc-core-report.json" in SCRIPT
    assert "NEXUS_CORE_REPORT_MISSING" in SCRIPT
    assert "NEXUS_CORE_REPORT_MISMATCH" in SCRIPT
    assert "$core.head -ne $head" in SCRIPT


def test_bootstrap_requires_external_inventory_report():
    assert "external-tools-inventory.json" in SCRIPT
    assert "NEXUS_EXTERNAL_INVENTORY_MISSING" in SCRIPT
    assert "external_inventory = $inventoryReport" in SCRIPT


def test_bootstrap_requires_external_plan_report():
    assert "external-provision-plan.json" in SCRIPT
    assert "NEXUS_EXTERNAL_PLAN_MISSING" in SCRIPT
    assert "external_plan = $planReport" in SCRIPT


def test_bootstrap_writes_single_final_report():
    assert "local-bootstrap-report.json" in SCRIPT
    assert "NEXUS LOCAL BOOTSTRAP = PASS" in SCRIPT
    assert "Code synchronized and Nexus core prepared/tested." in SCRIPT


def test_bootstrap_does_not_clone_or_reset_repository():
    lowered = SCRIPT.lower()
    assert "git clone" not in lowered
    assert "reset --hard" not in lowered


def test_bootstrap_selects_one_git_executable_deterministically():
    assert "Get-Command git.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1" in SCRIPT
