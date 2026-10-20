import json
import subprocess
from types import SimpleNamespace

import pytest

from nexus.adapters.languagetool import normalize, run
from nexus.contracts import Blocked, validate


def response(matches=None):
    return {"software": {"name": "LanguageTool", "version": "test"},
            "warnings": {"incompleteResults": False},
            "language": {"code": "pt-PT"}, "matches": matches or []}


def test_suggestions_never_prove_correctness():
    result = normalize(json.dumps(response()))
    validate("result", result)
    assert result["status"] == "UNKNOWN"
    assert result["ai_calls"] == 0
    assert "não garante" in result["markdown"]


def test_suggestion_is_a_candidate():
    result = normalize(json.dumps(response([{"message": "Erro", "context": {"text": "ezemplo"},
                                             "replacements": [{"value": "exemplo"}]}])))
    validate("result", result)
    assert "exemplo" in result["markdown"]
    assert result["outcome"] == "candidate"


@pytest.mark.parametrize("raw", ["", "{}", "null", '{"matches":false}',
    json.dumps({**response(), "warnings": {"incompleteResults": True}}),
    json.dumps({**response(), "language": {"code": "en-US"}})])
def test_invalid_output_blocked(raw):
    with pytest.raises(Blocked):
        normalize(raw)


def setup(tmp_path):
    source = tmp_path / "input.bin"
    source.write_text("Um ezemplo.", encoding="utf-8")
    java, jar = tmp_path / "java.exe", tmp_path / "languagetool-commandline.jar"
    java.touch(); jar.touch()
    (tmp_path / "languagetool.json").write_text(json.dumps({"java": str(java), "jar": str(jar)}))
    return source


def test_missing_tool_blocked(tmp_path):
    source = setup(tmp_path)
    (tmp_path / "java.exe").unlink()
    with pytest.raises(Blocked):
        run(source)


def test_timeout_preserves_source(tmp_path, monkeypatch):
    # Adapter normalization/process unit double; separate native security gate.
    monkeypatch.setattr("nexus.adapters.languagetool.require_native_boundary", lambda: None)
    monkeypatch.setattr(subprocess, "CREATE_NO_WINDOW", getattr(subprocess, "CREATE_NO_WINDOW", 0), raising=False)
    source = setup(tmp_path)
    original = source.read_bytes()
    def timeout(*args, **kwargs):
        assert kwargs["input"] == b""
        raise subprocess.TimeoutExpired("java", 45)
    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(Blocked):
        run(source)
    assert source.read_bytes() == original


def test_tool_failure_rejected(tmp_path, monkeypatch):
    # Adapter normalization/process unit double; separate native security gate.
    monkeypatch.setattr("nexus.adapters.languagetool.require_native_boundary", lambda: None)
    monkeypatch.setattr(subprocess, "CREATE_NO_WINDOW", getattr(subprocess, "CREATE_NO_WINDOW", 0), raising=False)
    source = setup(tmp_path)
    def failed(*args, **kwargs):
        assert kwargs["input"] == b""
        return SimpleNamespace(returncode=1)
    monkeypatch.setattr(subprocess, "run", failed)
    with pytest.raises(Blocked):
        run(source)
