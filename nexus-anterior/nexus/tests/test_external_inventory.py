from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "windows" / "inventory-external-tools.ps1").read_text(encoding="utf-8")


def test_inventory_is_read_only_except_report_directory():
    ARCHIVE_REDACTED_04 = (
        "winget", "choco", "scoop", "pip install", "git clone", "Start-Process",
        "New-LocalUser", "Set-Acl", "Invoke-WebRequest", "curl.exe",
    )
    lowered = SCRIPT.lower()
    for token in ARCHIVE_REDACTED_04:
        assert token.lower() not in lowered
    assert "external-tools-inventory.json" in SCRIPT


def test_inventory_covers_expected_external_tools():
    for name in (
        "java", "libreoffice", "zotero", "ffmpeg", "open_notebook",
        "languagetool", "ace_step", "forge", "git", "python",
    ):
        assert name in SCRIPT


def test_inventory_preserves_guarded_provisioning():
    for name in ("ace_step", "forge", "avatar_models", "isolation_account"):
        assert name in SCRIPT
    assert SCRIPT.count("BLOCKED_BY_POLICY") >= 5
    assert "Guarded provisioning was not executed." in SCRIPT


def test_inventory_does_not_claim_open_notebook_or_languagetool_from_path_without_evidence():
    assert "MISSING_OR_EXTERNAL" in SCRIPT
    assert "FOUND_PATH" in SCRIPT


def test_inventory_writes_machine_readable_missing_list():
    assert "$missing = @(" in SCRIPT
    assert "'missing'" in SCRIPT
    assert "NEXUS EXTERNAL INVENTORY = PASS" in SCRIPT
