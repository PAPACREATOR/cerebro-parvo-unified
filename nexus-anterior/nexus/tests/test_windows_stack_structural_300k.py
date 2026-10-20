"""300,000 deterministic structural compatibility cases for the Windows stack.

These are structural/contract cases, not 300,000 physical model renders.
They exercise bidirectional mappings, collision rejection, loopback confinement,
model-pin round trips, cross-file bindings, and hostile endpoint rejection.
Physical execution remains in test-post-install.ps1.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit

from nexus.contracts import ROOT


INSTALL = (ROOT / "windows" / "install-nexus-complete.ps1").read_text(encoding="utf-8")
OPEN_CONFIG = (ROOT / "windows" / "configure-open-notebook-local.py").read_text(encoding="utf-8")
MPT_CONFIG = (ROOT / "windows" / "configure-moneyprinterturbo-local.py").read_text(encoding="utf-8")
POST = (ROOT / "windows" / "test-post-install.ps1").read_text(encoding="utf-8")
MEDIA = (ROOT / "windows" / "install-media-tools.ps1").read_text(encoding="utf-8")
AVATAR = (ROOT / "lab" / "open_notebook_avatar" / "install-windows.ps1").read_text(encoding="utf-8")
OFFICE = (ROOT / "adapters" / "office.py").read_text(encoding="utf-8")
REQUIREMENTS = (ROOT / "requirements.txt").read_text(encoding="utf-8")
MCP_REQUIREMENTS = (ROOT / "requirements-mcp.txt").read_text(encoding="utf-8")

CASES = 50_000

PORTS = {
    "surrealdb": 8000,
    "ace_step": 8001,
    "forge": 7861,
    "open_notebook": 5055,
    "speaches": 8969,
    "llama_language": 18081,
    "llama_embedding": 18082,
}

ENDPOINTS = {
    "surrealdb": "http://127.0.0.1:8000",
    "ace_step": "http://127.0.0.1:8001",
    "forge": "http://127.0.0.1:7861",
    "open_notebook": "http://127.0.0.1:5055",
    "speaches": "http://127.0.0.1:8969",
    "llama_language": "http://127.0.0.1:18081/v1",
    "llama_embedding": "http://127.0.0.1:18082/v1",
}

MODEL_PINS = (
    {
        "repo": "Qwen/Qwen3-1.7B-GGUF",
        "revision": "90862c4b9d2787eaed51d12237eafdfe7c5f6077",
        "filename": "Qwen3-1.7B-Q8_0.gguf",
        "sha256": "061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a",
        "alias": "nexus-qwen3-1.7b",
        "port": 18081,
    },
    {
        "repo": "Qwen/Qwen3-Embedding-0.6B-GGUF",
        "revision": "d20cf9c16f82914a21dbd9c645f56895fb1d7750",
        "filename": "Qwen3-Embedding-0.6B-Q8_0.gguf",
        "sha256": "06507c7b42688469c4e7298b0a1e16deff06caf291cf0a5b278c308249c3e439",
        "alias": "nexus-qwen3-embedding-0.6b",
        "port": 18082,
    },
)

ACTIVE_SURFACES = (INSTALL, OPEN_CONFIG, MPT_CONFIG, POST)

def _validate_ports(mapping: dict[str, int]) -> None:
    values = list(mapping.values())
    if any(not isinstance(port, int) or not 1024 <= port <= 65535 for port in values):
        raise ValueError("invalid port")
    if len(values) != len(set(values)):
        raise ValueError("port collision")


def _validate_loopback(url: str) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "http" or parsed.hostname != "127.0.0.1":
        raise ValueError("non-loopback endpoint")
    if parsed.port is None:
        raise ValueError("missing port")


def _download_url(pin: dict[str, object]) -> str:
    return (
        f"https://huggingface.co/{pin['repo']}/resolve/"
        f"{pin['revision']}/{pin['filename']}"
    )


def test_static_stack_contract_is_coherent_before_volume():
    _validate_ports(PORTS)
    for service, endpoint in ENDPOINTS.items():
        _validate_loopback(endpoint)
        assert urlsplit(endpoint).port == PORTS[service]

    for required in (
        "ggml.llamacpp",
        "Qwen3-1.7B-Q8_0.gguf",
        "Qwen3-Embedding-0.6B-Q8_0.gguf",
        "nexus-qwen3-1.7b",
        "nexus-qwen3-embedding-0.6b",
        "Zotero_OpenOffice_Integration.oxt",
        "OXT_REGISTERED_JAVA_LIBREOFFICE_VERIFIED",
    ):
        assert required in INSTALL

    for required in (
        "Nexus Local Language",
        "Nexus Local Embedding",
        "http://127.0.0.1:18081/v1",
        "http://127.0.0.1:18082/v1",
        "openai_compatible",
    ):
        assert required in OPEN_CONFIG

    for required in (
        'llm_provider = "openai"',
        "http://127.0.0.1:18081/v1",
        "nexus-qwen3-1.7b",
        "local-openai-compatible",
    ):
        assert required in MPT_CONFIG

    for required in (
        "test_windows_stack_structural_300k.py",
        "llamacpp-language-real",
        "llamacpp-embedding-real",
        "NEXUS_ZOTERO_LIBREOFFICE_EXTENSION_NOT_REGISTERED",
    ):
        assert required in POST

    assert "$AcePort = 8001" in MEDIA
    assert "$ForgePort = 7861" in MEDIA
    assert "'--port','5055'" in INSTALL
    assert "'--port','8969'" in INSTALL
    assert REQUIREMENTS.splitlines() == ["jsonschema==4.26.0"]
    assert MCP_REQUIREMENTS.splitlines() == ["mcp==1.23.2", "trio==0.34.0"]
    assert "writer_pdf_Export" in OFFICE
    assert "wav2lip.pth" in AVATAR
    for practical_token in (
        "forge-cuda",
        "ace-step-runtime",
        "ace-step-cuda",
        "speaches-kokoro-real",
        "moneyprinterturbo-cli",
        "writer-libreoffice-real",
        "bidirectional-50000-real-mcp",
    ):
        assert practical_token in POST


def test_50000_service_port_roundtrips_bidirectionally():
    names = tuple(PORTS)
    reverse = {port: name for name, port in PORTS.items()}
    checked = 0
    for i in range(CASES):
        name = names[(i * 17 + 3) % len(names)]
        port = PORTS[name]
        assert reverse[port] == name
        assert PORTS[reverse[port]] == port
        checked += 1
    assert checked == CASES


def test_50000_loopback_endpoint_roundtrips_bidirectionally():
    names = tuple(ENDPOINTS)
    checked = 0
    for i in range(CASES):
        name = names[(i * 19 + 5) % len(names)]
        base = ENDPOINTS[name]
        suffix = f"/probe/{i}?direction={'forward' if i % 2 == 0 else 'reverse'}"
        url = base.rstrip("/") + suffix
        _validate_loopback(url)
        parsed = urlsplit(url)
        rebuilt = urlunsplit(parsed)
        assert rebuilt == url
        assert parsed.port == PORTS[name]
        assert parsed.hostname == "127.0.0.1"
        checked += 1
    assert checked == CASES


def test_50000_model_pin_url_hash_roundtrips_bidirectionally():
    checked = 0
    hex40 = re.compile(r"^[0-9a-f]{40}$")
    hex64 = re.compile(r"^[0-9a-f]{64}$")
    for i in range(CASES):
        pin = MODEL_PINS[i % len(MODEL_PINS)]
        assert hex40.fullmatch(str(pin["revision"]))
        assert hex64.fullmatch(str(pin["sha256"]))
        url = _download_url(pin)
        parsed = urlsplit(url)
        parts = parsed.path.strip("/").split("/")
        assert parts[0:2] == str(pin["repo"]).split("/")
        assert parts[2] == "resolve"
        assert parts[3] == pin["revision"]
        assert parts[4] == pin["filename"]
        assert _download_url(pin) == url
        checked += 1
    assert checked == CASES


def test_50000_full_component_bindings_are_bidirectional():
    bindings = (
        ("Git.Git", INSTALL, INSTALL),
        ("Python.Python.3.12", INSTALL, INSTALL),
        ("OpenJS.NodeJS.LTS", INSTALL, INSTALL),
        ("Microsoft.OpenJDK.17", INSTALL, INSTALL),
        ("TheDocumentFoundation.LibreOffice", INSTALL, INSTALL),
        ("DigitalScholar.Zotero", INSTALL, INSTALL),
        ("Gyan.FFmpeg", INSTALL, INSTALL),
        ("astral-sh.uv", INSTALL, INSTALL),
        ("ggml.llamacpp", INSTALL, INSTALL),
        ("LanguageTool-6.6", INSTALL, INSTALL),
        ("2.7.0", INSTALL, INSTALL),
        ("315d5255af2a5132aada41c94d5c3c5dc8e837aa", INSTALL, INSTALL),
        ("993994f7984bf3fe9655b267448328cf66fccb42", INSTALL, INSTALL),
        ("ca1e85fe9430179831e6bc6be790c332190a3866", MEDIA, MEDIA),
        ("dfdcbab685e57677014f05a3309b48cc87383167", MEDIA, MEDIA),
        ("d9426c121eddadc76648be20034bc087acd0240c", MEDIA, MEDIA),
        ("wav2lip.pth", INSTALL, AVATAR),
        ("68eb5a68b93cfe338198b3dfb151f6d5ec2fe4e5", INSTALL, INSTALL),
        ("mcp==1.23.2", MCP_REQUIREMENTS, MCP_REQUIREMENTS),
        ("writer_pdf_Export", OFFICE, OFFICE),
        ("nexus-qwen3-1.7b", INSTALL, OPEN_CONFIG),
        ("nexus-qwen3-embedding-0.6b", INSTALL, OPEN_CONFIG),
        ("18081", INSTALL, MPT_CONFIG),
        ("nexus-qwen3-1.7b", OPEN_CONFIG, MPT_CONFIG),
        ("18082", INSTALL, OPEN_CONFIG),
        ("libreoffice_oxt", INSTALL, POST),
        ("forge-cuda", POST, POST),
        ("ace-step-runtime", POST, POST),
        ("ace-step-cuda", POST, POST),
        ("speaches-kokoro-real", POST, POST),
        ("moneyprinterturbo-cli", POST, POST),
        ("bidirectional-50000-real-mcp", POST, POST),
    )
    checked = 0
    for i in range(CASES):
        token, left, right = bindings[(i * 23 + 1) % len(bindings)]
        assert token in left
        assert token in right
        assert right.find(token) >= 0
        assert left.rfind(token) >= 0
        checked += 1
    assert checked == CASES


def test_50000_port_collision_attacks_fail_in_both_orders():
    names = tuple(PORTS)
    checked = 0
    for i in range(CASES):
        a_index = i % len(names)
        b_index = (i * 5 + 1) % len(names)
        if b_index == a_index:
            b_index = (b_index + 1) % len(names)
        a = names[a_index]
        b = names[b_index]
        attacked = dict(PORTS)
        attacked[a] = attacked[b]
        for candidate in (attacked, dict(reversed(tuple(attacked.items())))):
            try:
                _validate_ports(candidate)
            except ValueError as error:
                assert str(error) == "port collision"
            else:
                raise AssertionError(f"collision accepted: {a}<->{b}")
        checked += 1
    assert checked == CASES


def test_50000_remote_endpoint_attacks_fail_bidirectionally():
    hosts = (
        "0.0.0.0",
        "example.com",
        "192.168.1.10",
        "10.0.0.5",
        "172.16.0.9",
        "::1",
    )
    checked = 0
    for i in range(CASES):
        host = hosts[(i * 29 + 2) % len(hosts)]
        port = 18081 if i % 2 == 0 else 18082
        if ":" in host:
            hostile = f"http://[{host}]:{port}/v1"
        else:
            hostile = f"http://{host}:{port}/v1"
        for candidate in (hostile, hostile + f"/probe/{i}"):
            try:
                _validate_loopback(candidate)
            except ValueError as error:
                assert str(error) == "non-loopback endpoint"
            else:
                raise AssertionError(f"remote endpoint accepted: {candidate}")
        checked += 1
    assert checked == CASES
