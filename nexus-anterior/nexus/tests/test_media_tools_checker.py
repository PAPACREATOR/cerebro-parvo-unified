from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = (ROOT / "windows" / "check_media_tools.py").read_text(encoding="utf-8")
PS = (ROOT / "windows" / "check-media-tools.ps1").read_text(encoding="utf-8")


def test_physical_checker_uses_nexus_mcp_tools_not_direct_shell_commands():
    assert 'call_tool(spec, "check_ace_step"' in PY
    assert 'call_tool(spec, "check_forge"' in PY
    assert 'allowed_tools={"check_ace_step"}' in PY
    assert 'allowed_tools={"check_forge"}' in PY


def test_physical_checker_preserves_zero_authority():
    assert '"authority": "NONE"' in PY
    assert "Ferramenta externa tentou declarar autoridade" in PY


def test_physical_checker_has_bounded_wait_and_single_report():
    assert "--wait-seconds" in PY
    assert "default=90" in PY
    assert "time.sleep(2)" in PY
    assert "media-health.json" in PS
    assert "media-health.previous" not in PS


def test_powershell_wrapper_never_starts_or_installs_tools():
    ARCHIVE_REDACTED_04 = ["git clone", "winget install", "Start-Process", "webui.bat", "acestep-api"]
    for token in ARCHIVE_REDACTED_04:
        assert token not in PS
    assert "NEXUS MEDIA HEALTH = PASS" in PS
    assert "NEXUS MEDIA HEALTH = FAIL" in PS
