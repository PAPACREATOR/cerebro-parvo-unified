from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "windows" / "install-media-tools.ps1").read_text(encoding="utf-8")


def test_external_tools_are_pinned():
    assert "ca1e85fe9430179831e6bc6be790c332190a3866" in SCRIPT
    assert "dfdcbab685e57677014f05a3309b48cc87383167" in SCRIPT


def test_external_tools_are_not_vendored_into_nexus():
    assert "[string]$ToolsRoot = 'C:\\Nexus-Tools'" in SCRIPT
    assert "Join-Path $ToolsRoot 'ACE-Step-1.5'" in SCRIPT
    assert "Join-Path $ToolsRoot 'Forge'" in SCRIPT


def test_services_are_loopback_only():
    assert "127.0.0.1" in SCRIPT
    assert "--port $AcePort" in SCRIPT
    assert "--port $ForgePort" in SCRIPT
    assert "--listen" not in SCRIPT
    assert "--share" not in SCRIPT
    assert "0.0.0.0" not in SCRIPT


def test_ace_step_is_low_vram_and_kernel_authority_safe():
    assert "ACESTEP_INIT_LLM=false" in SCRIPT
    assert "ACESTEP_LM_BACKEND=pt" in SCRIPT
    assert "Kernel is the brain; ACE-Step and Forge are external tools." in SCRIPT


def test_forge_is_bootstrapped_but_model_is_not_silently_downloaded():
    assert "webui.bat --exit" in SCRIPT
    assert "model = 'NOT_INSTALLED'" in SCRIPT
    assert "each model has its own license" in SCRIPT


def test_licenses_are_explicit_and_separate():
    assert "$AceLicense = 'MIT'" in SCRIPT
    assert "$ForgeLicense = 'AGPL-3.0'" in SCRIPT
    assert "Nexus does not vendor it" in SCRIPT


def test_installation_is_reproducible_and_refuses_dirty_checkouts():
    assert "fetch','--depth','1','origin',$Commit" in SCRIPT
    assert "checkout','--detach',$Commit" in SCRIPT
    assert "Refusing to overwrite local changes" in SCRIPT
    assert "Invoke-Checked $uv @('sync','--frozen') $ace" in SCRIPT


def test_report_and_launchers_are_created():
    assert "nexus-media-tools.json" in SCRIPT
    assert "Start-ACE-Step-Nexus.cmd" in SCRIPT
    assert "Start-Forge-Nexus.cmd" in SCRIPT
    assert "Check-Nexus-Media-Tools.cmd" in SCRIPT
    assert "health_check_launcher" in SCRIPT
