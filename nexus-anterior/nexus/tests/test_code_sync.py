from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC = (ROOT / "windows" / "sync-nexus-code.ps1").read_text(encoding="utf-8")
PROVISION = (ROOT / "windows" / "sync-nexus-pc.ps1").read_text(encoding="utf-8")


def test_provisioning_script_remains_hard_blocked_before_operations():
    marker = "NEXUS_PROTECTED_PROVISIONING_PENDING"
    assert marker in PROVISION
    throw_at = PROVISION.index("throw 'NEXUS_PROTECTED_PROVISIONING_PENDING")
    for token in ("Get-Command", "Push-Location", "Start-Process", "install-media-tools.ps1"):
        assert throw_at < PROVISION.index(token)


def test_code_sync_is_single_checkout_fast_forward_only():
    assert "reset --hard" not in SYNC.lower()
    assert "merge','--ff-only" in SYNC
    assert "git clone" not in SYNC.lower()
    assert "@('clone'" not in SYNC
    assert '"clone"' not in SYNC
    assert "backup-nexus" not in SYNC.lower()
    assert "Nexus-old" not in SYNC


def test_code_sync_refuses_dirty_tree_and_wrong_origin():
    assert "status --porcelain" in SYNC
    assert "NEXUS_DIRTY_TREE" in SYNC
    assert "NEXUS_WRONG_ORIGIN" in SYNC
    assert "$OfficialOrigin = 'https://github.com/PAPACREATOR/cerebro-parvo-.git'" in SYNC


def test_code_sync_can_find_one_official_checkout_without_recursive_disk_scan():
    assert "C:\\Nexos" in SYNC
    assert "C:\\Nexus" in SYNC
    assert "C:\\work\\nexus-publicacao" in SYNC
    assert "Get-ChildItem" in SYNC
    assert "-Recurse" not in SYNC
    assert "NEXUS_MULTIPLE_REPOSITORIES" in SYNC
    assert "Não foi criado clone novo" in SYNC


def test_code_sync_does_not_provision_or_start_external_tools():
    ARCHIVE_REDACTED_04 = (
        "winget", "pip install", "-m venv", "Start-Process",
        "install-media-tools.ps1", "Start-ACE-Step-Nexus.cmd",
        "Start-Forge-Nexus.cmd", "check-media-tools.ps1",
    )
    for token in ARCHIVE_REDACTED_04:
        assert token not in SYNC
    assert "Provisioning/instalação não foi executado." in SYNC


def test_code_sync_requires_remote_head_match():
    assert 'rev-parse "origin/$Branch"' in SYNC
    assert "NEXUS_SYNC_MISMATCH" in SYNC
    assert "NEXUS CODE SYNC = PASS" in SYNC


def test_code_sync_selects_one_git_executable_deterministically():
    assert "Get-Command git.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1" in SYNC
