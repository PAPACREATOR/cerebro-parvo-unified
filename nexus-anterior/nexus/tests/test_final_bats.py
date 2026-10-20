"""Contracts for the external Windows launchers.

The two final .bat launchers are intentionally NOT tracked in the repository.
The repository owns the bounded PowerShell entrypoints and their security tests;
the user receives the .bat files separately.
"""
from nexus.contracts import ROOT


REPO = ROOT.parent
INSTALL = (ROOT / "windows" / "install-nexus-complete.ps1").read_text(encoding="utf-8")
POST = (ROOT / "windows" / "test-post-install.ps1").read_text(encoding="utf-8")


def test_final_bat_launchers_are_external_not_repository_files():
    assert not (REPO / "INSTALAR-NEXUS-COMPLETO.bat").exists()
    assert not (REPO / "TESTAR-NEXUS-POS-INSTALACAO.bat").exists()


def test_install_entrypoint_is_explicit_and_password_free():
    assert "[switch]$AuthorizeInstall" in INSTALL
    assert "NEXUS_INSTALL_AUTHORIZATION_REQUIRED" in INSTALL
    assert "C:\\Nexus-Tools" in INSTALL
    for ARCHIVE_REDACTED_04 in (
        "New-LocalUser",
        "Add-LocalGroupMember",
        "Read-Host",
        "setup-isolation.ps1",
        "NexusTool",
    ):
        assert ARCHIVE_REDACTED_04 not in INSTALL


def test_post_install_acceptance_runs_exact_stress_and_security_gates():
    required = (
        "test_product_flows_5000.py",
        "test_product_system_50000.py",
        "test_public_product_routes_10000.py",
        "test_public_product_routes_all_50000.py",
        "test_product_themes_canonical_200k.py",
        "test_system_varied_200k.py",
        "test_bidirectional_50000.py",
        "test_authority_10000.py",
        "test_native_boundary.py",
        "test_confinement_gate.py",
        "NEXUS_RUN_50K",
        "CreateAppContainerProfile",
        "AssignProcessToJobObject",
        "install.models.llamacpp.language.alias",
        "install.models.llamacpp.embedding.alias",
        "llamacpp-language-real",
        "llamacpp-embedding-real",
        "test_windows_stack_structural_300k.py",
        "torch.cuda.is_available",
        "MoneyPrinterTurbo",
        "NEXUS_REAL_WRITER",
        "test_writer_real_libreoffice.py",
    )
    for token in required:
        assert token.lower() in POST.lower()


def test_post_install_acceptance_never_promotes_or_creates_accounts():
    for ARCHIVE_REDACTED_04 in (
        "store.promote",
        ".promote(",
        "New-LocalUser",
        "Add-LocalGroupMember",
        "Read-Host",
    ):
        assert ARCHIVE_REDACTED_04 not in POST
    assert "legacy_accounts_present" in POST
    assert "per-task AppContainer" in POST
