from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = (ROOT / "windows" / "install-nexus-complete.ps1").read_text(encoding="utf-8")
MEDIA = (ROOT / "windows" / "install-media-tools.ps1").read_text(encoding="utf-8")
AVATAR = (ROOT / "lab" / "open_notebook_avatar" / "install-windows.ps1").read_text(encoding="utf-8")
MODELS = (ROOT / "lab" / "open_notebook_avatar" / "provision_models.py").read_text(encoding="utf-8")
ROUTER = (ROOT / "lab" / "open_notebook_avatar" / "install_router.py").read_text(encoding="utf-8")
LAUNCHER = (ROOT / "windows" / "nexus-launcher.py").read_text(encoding="utf-8")
OPEN_CONFIG = (ROOT / "windows" / "configure-open-notebook-local.py").read_text(encoding="utf-8")
MPT_CONFIG = (ROOT / "windows" / "configure-moneyprinterturbo-local.py").read_text(encoding="utf-8")
DOCUMENTARY = (ROOT / "windows" / "documentary_bridge.py").read_text(encoding="utf-8")


def test_complete_installer_requires_explicit_human_authorization():
    assert "[switch]$AuthorizeInstall" in MASTER
    assert "if (-not $AuthorizeInstall)" in MASTER
    assert "NEXUS_INSTALL_AUTHORIZATION_REQUIRED" in MASTER
    assert MASTER.index("if (-not $AuthorizeInstall)") < MASTER.index("Ensure-WingetPackage 'Git.Git'")


def test_nested_installers_remain_fail_closed_without_authorization():
    for script in (MEDIA, AVATAR):
        assert "[switch]$AuthorizeInstall" in script
        assert "if (-not $AuthorizeInstall)" in script
        assert "NEXUS_INSTALL_AUTHORIZATION_REQUIRED" in script
    assert "-AuthorizeInstall" in MASTER


def test_model_download_is_authorized_explicitly_not_by_ambient_state():
    assert "authorize_install=False" in MODELS
    assert "authorize_install is not True" in MODELS
    assert '--authorize-install' in MODELS
    assert "'--authorize-install'" in AVATAR


def test_installer_pins_the_external_source_trees_and_binary_hashes():
    expected = (
        "315d5255af2a5132aada41c94d5c3c5dc8e837aa",
        "993994f7984bf3fe9655b267448328cf66fccb42",
        "ca1e85fe9430179831e6bc6be790c332190a3866",
        "dfdcbab685e57677014f05a3309b48cc87383167",
        "d9426c121eddadc76648be20034bc087acd0240c",
        "55c7e05ee2b68ec0d8b86c4b588e9b9807f257af8c15c05d17074514c64d8c91",
        "53600506b399bb5ffe1e4c8dec794fd378212f14aaf38ccef9b6f89314d11631",
        "6ce0161689b3853acaa03779ec93eafe75a02f4ced659bee03f50797806fa2fa",
        "68eb5a68b93cfe338198b3dfb151f6d5ec2fe4e5",
    )
    joined = MASTER + MEDIA
    for value in expected:
        assert value in joined


def test_installer_uses_current_zotero_and_expected_windows_dependencies():
    for package in (
        "Git.Git", "Python.Python.3.12", "OpenJS.NodeJS.LTS",
        "Microsoft.OpenJDK.17", "TheDocumentFoundation.LibreOffice",
        "DigitalScholar.Zotero", "Gyan.FFmpeg", "astral-sh.uv", "ggml.llamacpp",
    ):
        assert package in MASTER


def test_installer_prepares_local_models_needed_for_later_physical_acceptance():
    for value in (
        "Qwen3-1.7B-Q8_0.gguf", "Qwen3-Embedding-0.6B-Q8_0.gguf",
        "061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a",
        "06507c7b42688469c4e7298b0a1e16deff06caf291cf0a5b278c308249c3e439",
        "speaches-ai/Kokoro-82M-v1.0-ONNX",
        "acestep-v15-turbo", "wav2lip.pth", "s3fd.pth",
    ):
        assert value in MASTER or value in AVATAR or value in MODELS


def test_installer_has_no_fake_pending_binding_after_local_configuration():
    assert "OPEN_NOTEBOOK_MODEL_AND_TRANSFORMATION_BINDING" not in MASTER
    assert "FORGE_IMAGE_CHECKPOINT_SELECTION" not in MASTER
    assert "model='NOT_SELECTED'" not in MASTER
    assert "configure-open-notebook-local.py" in MASTER
    assert "INSTALLED_BUILT_CONFIGURED" in MASTER


def test_forge_and_deforum_receive_a_verified_sd15_baseline():
    assert "v1-5-pruned-emaonly.safetensors" in MASTER
    assert "6ce0161689b3853acaa03779ec93eafe75a02f4ced659bee03f50797806fa2fa" in MASTER
    assert "CreativeML Open RAIL-M" in MASTER
    assert "RUNTIME_AND_BASE_MODEL_INSTALLED" in MASTER
    assert "REQUIRES_REAL_FORGE_AND_DEFORUM_RENDER_ACCEPTANCE" in MASTER


def test_installer_never_writes_or_deletes_nexus_vaults():
    lowered = MASTER.lower()
    for ARCHIVE_REDACTED_04 in (
        "join-path $runtime 'canonical'",
        "join-path $runtime 'creative'",
        "store.promote",
        "shutil.rmtree",
        "reset --hard",
        "git clean",
    ):
        assert ARCHIVE_REDACTED_04 not in lowered


def test_launcher_is_thin_and_uses_validated_external_python_and_git():
    assert '"python"' in LAUNCHER
    assert '"git"' in LAUNCHER
    assert '"expected_origin"' in LAUNCHER
    assert '"-m", "nexus.app"' in LAUNCHER
    assert "PyInstaller" not in LAUNCHER
    assert "nexus.host" not in LAUNCHER
    assert "nexus.store" not in LAUNCHER


def test_avatar_router_matches_the_pinned_open_notebook_version():
    assert 'version != "1.15.0"' in ROUTER
    assert "Open Notebook 1.15.0" in ROUTER
    assert "app.include_router(podcasts.router" in ROUTER


def test_deforum_is_installed_inside_forge_but_not_claimed_functional_without_render():
    assert "https://github.com/deforum/sd-forge-deforum.git" in MEDIA
    assert "d9426c121eddadc76648be20034bc087acd0240c" in MEDIA
    assert "INSTALLED_DEPENDENCIES_TESTED" in MEDIA
    assert "REQUIRES_REAL_RENDER_ACCEPTANCE" in MEDIA
    assert "NEXUS_DEFORUM_INSTALL_NOT_VERIFIED" in MASTER


def test_open_notebook_install_excludes_unused_legacy_runtime_packages():
    assert "'--no-install-package'" in MASTER
    assert "OPEN_NOTEBOOK_LLAMACPP_COMPAT=PASS" in MASTER
    assert "openai-compatible" in MASTER
    assert "127.0.0.1:18081/v1" in MASTER
    assert "127.0.0.1:18082/v1" in MASTER


def test_open_notebook_configuration_uses_public_api_and_local_models():
    for value in (
        "/api/credentials", "/api/models", "/api/models/defaults",
        "/api/settings", "/api/transformations", "/api/speaker-profiles", "/api/episode-profiles",
        "nexus-qwen3-1.7b", "nexus-qwen3-embedding-0.6b", "speaches-ai/Kokoro-82M-v1.0-ONNX",
        "Nexus Local Test Speaker", "Nexus Local Test Episode", "nexus_strict_cognitive_v1",
    ):
        assert value in OPEN_CONFIG
    assert '"auto_delete_files": "no"' in OPEN_CONFIG
    assert "NEXUS_INSTALL_AUTHORIZATION_REQUIRED" in OPEN_CONFIG


def test_open_notebook_config_fails_on_conflict_instead_of_overwriting():
    assert "Credential base URL conflict" in OPEN_CONFIG
    assert "Existing model is linked to another credential" in OPEN_CONFIG
    assert "Existing Nexus speaker profile conflicts" in OPEN_CONFIG
    assert "Existing Nexus episode profile conflicts" in OPEN_CONFIG
    assert 'api.call("PUT", "/api/credentials/' not in OPEN_CONFIG


def test_complete_installer_starts_only_loopback_configuration_services():
    for value in (
        "'127.0.0.1:8000'", "'127.0.0.1','--port','8969'",
        "'127.0.0.1','--port','5055'",
        "$LlamaLanguagePort = 18081", "$LlamaEmbeddingPort = 18082",
    ):
        assert value in MASTER
    assert "open-notebook-local-config.json" in MASTER


def test_nexus_interpret_config_is_bound_to_real_open_notebook_ids():
    assert "open-notebook.json" in MASTER
    assert "model_id=$openConfig.models.language.id" in MASTER
    assert "transformation_id=$openConfig.transformation.id" in MASTER
    assert "Return ONLY one valid JSON object" in OPEN_CONFIG
    assert "exact verbatim substrings" in OPEN_CONFIG


def test_heavy_install_requires_disk_headroom_before_downloads():
    assert "NEXUS_DISK_SPACE_REQUIRED" in MASTER
    assert "70 * 1GB" in MASTER
    assert MASTER.index("NEXUS_DISK_SPACE_REQUIRED") < MASTER.index("LanguageTool-6.6.zip")


def test_moneyprinter_is_pinned_and_documentary_path_has_no_tts_dependency():
    assert "https://github.com/harry0703/MoneyPrinterTurbo.git" in MASTER
    assert "68eb5a68b93cfe338198b3dfb151f6d5ec2fe4e5" in MASTER
    assert "INSTALLED_CONFIGURED_CLI_TESTED" in MASTER
    assert 'llm_provider = "openai"' in MPT_CONFIG
    assert 'openai_base_url = "http://127.0.0.1:18081/v1"' in MPT_CONFIG
    assert 'openai_model_name = "nexus-qwen3-1.7b"' in MPT_CONFIG
    assert 'subtitle_provider = "whisper"' in MPT_CONFIG
    assert '"provider": "none"' in MPT_CONFIG
    assert "kokoro:" not in DOCUMENTARY.lower()
    assert "speaches" not in DOCUMENTARY.lower()
    assert '"--voice-name", "no-voice"' in DOCUMENTARY
    assert '"--custom-audio-file"' in DOCUMENTARY
    assert '"--no-subtitle-enabled"' in DOCUMENTARY



def test_complete_installer_uses_llamacpp_and_zotero_writer_is_structural():
    assert "Zotero_OpenOffice_Integration.oxt" in MASTER
    assert "OXT_REGISTERED_JAVA_LIBREOFFICE_VERIFIED" in MASTER
    assert "unopkg" in MASTER.lower()
    assert "ggml.llamacpp" in MASTER
    assert "NEXUS_LLAMACPP_LANGUAGE_PROBE_FAILED" in MASTER
    assert "NEXUS_LLAMACPP_EMBEDDING_PROBE_FAILED" in MASTER

def test_documentary_output_is_candidate_only_and_never_promotes():
    assert '"canonical_write": False' in DOCUMENTARY
    assert "store.promote" not in DOCUMENTARY
    assert "path(\"canonical\"" not in DOCUMENTARY.lower()
    assert " / \"canonical\"" not in DOCUMENTARY.lower()
    assert "PASS_CANDIDATE" in DOCUMENTARY
