from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
TEXT_SUFFIXES = {
    ".py", ".ps1", ".psm1", ".cmd", ".bat", ".md", ".txt", ".json",
    ".yml", ".yaml", ".toml", ".ini", ".cfg", ".xml", ".html", ".js", ".ts",
}
# Preserved genealogy and installed environments are not authored runtime source.
# Dependency declarations and every active source file remain checked.
EXCLUDED_TOP_LEVEL = {".git", "historico", ".venv"}
FORBIDDEN = "".join(chr(value) for value in (111, 108, 108, 97, 109, 97))
FORBIDDEN_TOKENS = (
    FORBIDDEN,
    "".join(str(value) for value in (1, 1, 4, 3, 4)),
    "".join(("qwen", "3", ":", "4", "b")),
    "".join(("nomic", "-embed", "-text")),
)


def test_active_repository_has_no_ARCHIVE_REDACTED_04_legacy_runtime_reference():
    violations = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(ROOT)
        if relative.parts and relative.parts[0] in EXCLUDED_TOP_LEVEL:
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, 1):
            folded = line.casefold()
            if any(token in folded for token in FORBIDDEN_TOKENS):
                violations.append(f"{relative}:{number}")
    assert violations == [], "ARCHIVE_REDACTED_04 legacy runtime references: " + ", ".join(violations)


@pytest.mark.parametrize("directory", ["historico", ".venv"])
def test_preserved_or_installed_files_are_not_active_source(tmp_path, monkeypatch, directory):
    historical = tmp_path / directory / "evidence.py"
    historical.parent.mkdir()
    raw = (FORBIDDEN + "\n").encode("utf-8")
    historical.write_bytes(raw)
    monkeypatch.setitem(globals(), "ROOT", tmp_path)
    test_active_repository_has_no_ARCHIVE_REDACTED_04_legacy_runtime_reference()
    assert historical.read_bytes() == raw


def test_active_runtime_reference_is_still_rejected(tmp_path, monkeypatch):
    active = tmp_path / "nexus" / "adapter.py"
    active.parent.mkdir()
    active.write_text(FORBIDDEN.upper(), encoding="utf-8")
    monkeypatch.setitem(globals(), "ROOT", tmp_path)
    with pytest.raises(AssertionError, match="ARCHIVE_REDACTED_04 legacy runtime") as failure:
        test_active_repository_has_no_ARCHIVE_REDACTED_04_legacy_runtime_reference()
    assert str(active.relative_to(tmp_path)) + ":1" in str(failure.value)
