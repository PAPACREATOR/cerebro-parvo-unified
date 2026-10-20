from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "windows" / "plan-external-provisioning.ps1").read_text(encoding="utf-8")


def test_provision_plan_is_strictly_plan_only():
    ARCHIVE_REDACTED_04 = (
        "winget", "choco", "scoop", "git clone", "git.exe", "uv sync",
        "pip install", "Start-Process", "Invoke-WebRequest", "curl.exe",
        "New-LocalUser", "Set-Acl", "webui.bat", "acestep-api",
    )
    lowered = SCRIPT.lower()
    for token in ARCHIVE_REDACTED_04:
        assert token.lower() not in lowered
    assert "mode = 'PLAN_ONLY'" in SCRIPT
    assert "execution_authorized = $false" in SCRIPT


def test_provision_plan_requires_real_inventory_first():
    assert "external-tools-inventory.json" in SCRIPT
    assert "NEXUS_EXTERNAL_INVENTORY_REQUIRED" in SCRIPT
    assert "nexus.external-inventory.v1" in SCRIPT


def test_provision_plan_preserves_known_media_pins_and_licenses():
    assert "ca1e85fe9430179831e6bc6be790c332190a3866" in SCRIPT
    assert "dfdcbab685e57677014f05a3309b48cc87383167" in SCRIPT
    assert "315d5255af2a5132aada41c94d5c3c5dc8e837aa" in SCRIPT
    assert "MIT" in SCRIPT
    assert "AGPL-3.0" in SCRIPT


def test_provision_plan_covers_expected_external_tools():
    for name in (
        "ace_step", "forge", "libreoffice", "zotero",
        "open_notebook", "languagetool", "ffmpeg",
    ):
        assert name in SCRIPT


def test_provision_plan_writes_machine_readable_output():
    assert "external-provision-plan.json" in SCRIPT
    assert "NEXUS EXTERNAL PROVISION PLAN = PASS" in SCRIPT
