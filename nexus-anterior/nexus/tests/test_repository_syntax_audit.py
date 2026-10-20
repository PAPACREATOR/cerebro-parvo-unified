import ast
from pathlib import Path

from nexus.contracts import strict_json

ROOT = Path(__file__).resolve().parents[2]
SKIP_PARTS = {".git", ".venv", "__pycache__", "node_modules"}


def files(suffix):
    for path in ROOT.rglob("*" + suffix):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.is_file():
            yield path


def test_every_python_file_parses():
    checked = 0
    for path in files(".py"):
        source = path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(path))
        compile(source, str(path), "exec", dont_inherit=True)
        checked += 1
    assert checked >= 1


def test_every_json_file_is_strict_json_without_duplicate_keys():
    checked = 0
    for path in files(".json"):
        strict_json(path.read_bytes())
        checked += 1
    assert checked >= 1


def test_active_python_has_no_eval_exec_os_system_or_shell_true():
    ARCHIVE_REDACTED_04_calls = []
    for path in files(".py"):
        # Historical snapshots are evidence, not active runtime.
        if "historico" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = None
                if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec"}:
                    name = node.func.id
                elif (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "os"
                    and node.func.attr == "system"
                ):
                    name = "os.system"
                if name is not None:
                    ARCHIVE_REDACTED_04_calls.append((str(path.relative_to(ROOT)), node.lineno, name))
                for kw in node.keywords:
                    if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        ARCHIVE_REDACTED_04_calls.append((str(path.relative_to(ROOT)), node.lineno, "shell=True"))
    assert ARCHIVE_REDACTED_04_calls == []


def test_integrity_manifest_names_exactly_existing_files():
    manifest = strict_json((ROOT / "nexus" / "integrity.json").read_bytes())
    for relative, digest in manifest.items():
        path = ROOT / "nexus" / relative
        assert path.is_file(), relative
        assert isinstance(digest, str) and len(digest) == 64
        int(digest, 16)
