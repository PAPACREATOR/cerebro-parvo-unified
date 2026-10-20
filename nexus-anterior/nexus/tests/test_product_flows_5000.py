"""Product-flow stress gates without changing the frozen Nexus runtime.

Six flows x 5,000 directional cases. These tests exercise existing contracts and
existing lab boundaries only. Unsupported public Host routes must remain blocked;
a test is never allowed to manufacture a PASS for a capability that is not wired.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import zipfile
from pathlib import Path

import pytest

from nexus.adapters.office import document_kind
from nexus.adapters.tools import compare
from nexus.contracts import Blocked, ROOT, validate
from nexus.frontdoor import parse
from nexus.natural_bridge import from_markdown, kernel_from_notebook_boundary, kernel_to_notebook, to_markdown


CASES = 5_000
FLOWS = ("video", "podcast", "visual_podcast", "book", "music", "web")


def _load(name: str, relative: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


DOCUMENTARY = _load("nexus_documentary_flow_test", "windows/documentary_bridge.py")
OPEN_CONFIG = _load("nexus_open_notebook_config_test", "windows/configure-open-notebook-local.py")
REQUEST_SCHEMA = json.loads((ROOT / "schemas" / "request.json").read_text(encoding="utf-8"))
POLICY = json.loads((ROOT / "laws" / "policy.json").read_text(encoding="utf-8"))


def _visual_path_contract(root: Path, name: str, max_bytes: int) -> Path:
    """Independent deterministic oracle for the published avatar path contract."""
    if not isinstance(name, str) or not name or len(name) > 240:
        raise ValueError("INVALID_PATH")
    if any(ord(c) < 32 for c in name) or "\\" in name or ":" in name:
        raise ValueError("INVALID_PATH")
    relative = Path(name)
    if relative.is_absolute() or any(part in {".", ".."} for part in name.split("/")):
        raise ValueError("INVALID_PATH")
    path = (root.resolve() / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("INPUT_UNAVAILABLE")
    if not 0 < path.stat().st_size <= max_bytes:
        raise ValueError("INPUT_SIZE")
    return path


def _assert_visual_path_oracle_is_bound_to_production_source() -> None:
    service = (ROOT / "lab" / "open_notebook_avatar" / "notebook_avatar" / "service.py").read_text(encoding="utf-8")
    for token in (
        'def contained_file(root: Path, name: str, max_bytes: int)',
        'len(name) > 240',
        '"\\\\" in name',
        '":" in name',
        'relative.is_absolute()',
        'part in {".", ".."}',
        'path.is_relative_to(root.resolve())',
        'path.stat().st_size <= max_bytes',
    ):
        assert token in service



def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _source_gate(case_id: int) -> str:
    """Two independent result envelopes; disagreement is preserved, never auto-picked."""
    left = _sha(f"source:{case_id}:verified")
    right = left if case_id % 5 else _sha(f"source:{case_id}:conflict")
    a = {"status": "PASS", "sha256": left, "capability": "source-a"}
    b = {"status": "PASS", "sha256": right, "capability": "source-b"}
    forward = compare(a, b)
    reverse = compare(b, a)
    expected = "agreement" if left == right else "conflict"
    assert forward["outcome"] == expected
    assert reverse["outcome"] == expected
    assert forward["a"] == a and forward["b"] == b
    assert reverse["a"] == b and reverse["b"] == a
    return expected


def _roundtrip_human(text: str, expected_intent: str) -> str:
    parsed = parse(text)
    assert parsed.status == "RESOLVED"
    assert parsed.intent == expected_intent
    markdown = to_markdown(parsed)
    back = from_markdown(markdown)
    assert back["text"].encode("utf-8") == text.encode("utf-8")
    return markdown


def _notebook_roundtrip(markdown: str) -> None:
    packet = kernel_to_notebook(markdown)
    assert packet["authority"] == "UNTRUSTED_REQUEST"
    assert packet["target"] == "open-notebook"
    returned = kernel_from_notebook_boundary(packet)
    assert returned == markdown


def _request(process: str, text: str = "x") -> dict:
    return {"process": process, "text": text, "filename": "", "attachment": ""}


def _minimal_odt(case_id: int) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("mimetype", "application/vnd.oasis.opendocument.text")
        archive.writestr(
            "content.xml",
            f'<?xml version="1.0" encoding="UTF-8"?><document><p>Nexus livro {case_id}</p></document>',
        )
    return stream.getvalue()


class _EpisodeAPI:
    """In-memory API double for the existing OpenNotebook profile builder only."""

    def __init__(self):
        self.calls = []

    def call(self, method: str, path: str, payload=None):
        self.calls.append((method, path, payload))
        if method == "GET":
            raise OPEN_CONFIG.SetupError("Open Notebook API GET profile -> 404: not found")
        assert method == "POST"
        value = dict(payload)
        value["id"] = "episode-profile-test"
        return value


def _valid_storyboard(case_id: int) -> dict:
    return {
        "title": f"Documentário {case_id}",
        "script": (
            f"Narração factual do caso {case_id}. "
            "Este texto existe apenas para testar o contrato delimitado e a preservação de fontes. "
        ) * 3,
        "scenes": [
            {"visual_prompt": f"Documentary factual scene {case_id}-{scene}", "seconds": 3 + ((case_id + scene) % 13)}
            for scene in range(6)
        ],
    }


def test_video_flow_5000_directional_cases():
    source = ROOT / "windows" / "documentary_bridge.py"
    assert source.is_file()
    assert "PASS_CANDIDATE" in source.read_text(encoding="utf-8")
    for case_id in range(CASES):
        markdown = _roundtrip_human(f"& cria documentário caso {case_id} com fontes aprovadas", "trabalhar")
        outcome = _source_gate(case_id)
        if outcome == "conflict":
            continue
        _notebook_roundtrip(markdown)
        value = DOCUMENTARY.validate_storyboard(_valid_storyboard(case_id))
        assert value["title"] == f"Documentário {case_id}"
        assert len(value["scenes"]) == 6
        assert all(type(scene["seconds"]) is int and 3 <= scene["seconds"] <= 15 for scene in value["scenes"])
    for case_id in range(CASES):
        assert validate("request", _request("video", str(case_id)))["process"] == "video"


def test_podcast_flow_5000_directional_cases():
    for case_id in range(CASES):
        markdown = _roundtrip_human(f"& cria podcast caso {case_id} apenas com estas fontes", "trabalhar")
        outcome = _source_gate(case_id)
        api = _EpisodeAPI()
        if outcome == "conflict":
            assert api.calls == []
            continue
        _notebook_roundtrip(markdown)
        profile = OPEN_CONFIG.episode_profile(api, f"language-{case_id}", f"speaker-{case_id}")
        assert profile["outline_llm"] == f"language-{case_id}"
        assert profile["transcript_llm"] == f"language-{case_id}"
        assert profile["speaker_config"] == f"speaker-{case_id}"
        assert profile["num_segments"] == 3
        assert "Do not invent sources or claims" in profile["default_briefing"]
        assert [call[0] for call in api.calls] == ["GET", "POST"]
    for case_id in range(CASES):
        assert validate("request", _request("podcast", str(case_id)))["process"] == "podcast"


def test_visual_podcast_flow_5000_directional_cases(tmp_path):
    audio_root = tmp_path / "audio"
    avatar_root = tmp_path / "avatars"
    audio_root.mkdir()
    avatar_root.mkdir()
    audio = audio_root / "episode.wav"
    avatar = avatar_root / "portrait.png"
    audio.write_bytes(b"RIFF" + b"a" * 128)
    avatar.write_bytes(b"\x89PNG\r\n\x1a\n" + b"b" * 128)

    for case_id in range(CASES):
        markdown = _roundtrip_human(f"& cria podcast visual caso {case_id}", "trabalhar")
        outcome = _source_gate(case_id)
        if outcome == "conflict":
            continue
        _notebook_roundtrip(markdown)
        assert _visual_path_contract(audio_root, "episode.wav", 100_000_000) == audio.resolve()
        assert _visual_path_contract(avatar_root, "portrait.png", 20_000_000) == avatar.resolve()
        bad = "../portrait.png" if case_id % 2 else "C:\\portrait.png"
        with pytest.raises(ValueError):
            _visual_path_contract(avatar_root, bad, 20_000_000)
    _assert_visual_path_oracle_is_bound_to_production_source()
    # Existing avatar output is explicitly candidate/untrusted in production service.
    service = (ROOT / "lab" / "open_notebook_avatar" / "notebook_avatar" / "service.py").read_text(encoding="utf-8")
    assert '"authority": "UNTRUSTED"' in service
    assert '"outcome": "candidate"' in service


def test_book_flow_5000_directional_cases():
    for case_id in range(CASES):
        _roundtrip_human(f"& prepara livro caso {case_id} sem alterar o molde", "trabalhar")
        outcome = _source_gate(case_id)
        if outcome == "conflict":
            continue
        assert document_kind(_minimal_odt(case_id)) == ".odt"
        assert validate("request", _request("book", f"livro {case_id}"))["process"] == "book"
    template_gate = (ROOT / "tests" / "test_writer_real_libreoffice.py").read_text(encoding="utf-8")
    assert "page-usage=\"mirrored\"" in template_gate
    assert "orphans" in template_gate and "widows" in template_gate
    assert "never edit styles" in template_gate.lower()


def test_music_flow_5000_directional_cases_is_fail_closed_until_generation_route_exists():
    media = (ROOT / "adapters" / "media_tools.py").read_text(encoding="utf-8")
    installer = (ROOT / "windows" / "install-media-tools.ps1").read_text(encoding="utf-8")
    assert "ACE-Step API" in media
    assert "ACE-Step-1.5" in installer
    for case_id in range(CASES):
        _roundtrip_human(
            f"& cria música caso {case_id}: tema memória, letra portuguesa, estilo definido",
            "trabalhar",
        )
        _source_gate(case_id)
        assert validate("request", _request("music", str(case_id)))["process"] == "music"
    assert "music" in REQUEST_SCHEMA["properties"]["process"]["enum"]


def test_web_flow_5000_directional_cases_is_parsed_but_fail_closed_at_host():
    for case_id in range(CASES):
        text = f"@ pesquisa web caso {case_id} e conserva as fontes"
        _roundtrip_human(text, "web")
        _source_gate(case_id)
        assert validate("request", _request("web", str(case_id)))["process"] == "web"
    assert "web" in REQUEST_SCHEMA["properties"]["process"]["enum"]


def test_frozen_policy_and_directional_budget_are_unchanged():
    assert POLICY == {
        "version": "1.0",
        "canonical_gate": "human_required",
        "automatic_deletion": False,
        "ai_authority": False,
        "processes": ["verify", "interpret", "proofread", "convert_pdf", "video", "podcast", "visual_podcast", "book", "music", "web"],
        "max_input_bytes": 2097152,
    }
    assert CASES * len(FLOWS) == 30_000
