from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "windows" / "sync-nexus-pc.ps1").read_text(encoding="utf-8")


def test_pc_provisioning_is_closed_before_any_command():
    marker = "NEXUS_PROTECTED_PROVISIONING_PENDING"
    assert marker in SCRIPT
    stop = SCRIPT.index("throw 'NEXUS_PROTECTED_PROVISIONING_PENDING")
    for token in (
        "Get-Command", "Push-Location", "New-Item",
        "Start-Process", "install-media-tools.ps1", "check-media-tools.ps1",
    ):
        assert stop < SCRIPT.index(token)


def test_pc_provisioning_has_no_bypass_before_guard():
    prefix = SCRIPT[:SCRIPT.index("throw 'NEXUS_PROTECTED_PROVISIONING_PENDING")]
    assert "SkipMediaInstall" in prefix  # parameters may exist for genealogy
    assert "if (" not in prefix
    assert "Get-Command" not in prefix
    assert "New-Item" not in prefix
    assert "Start-Process" not in prefix


def test_historical_body_is_explicitly_unreachable():
    assert "Historical implementation retained below; unreachable while this gate is closed." in SCRIPT
