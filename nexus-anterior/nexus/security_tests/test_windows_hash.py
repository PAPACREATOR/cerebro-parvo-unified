"""Real native Windows CNG vectors; no mocked provider, Python or token."""
import hashlib
import json
from pathlib import Path
import sys

from nexus.contracts import ROOT
from nexus.windows_sandbox import launch_confined, task_environment


def test_cng_known_vectors_inside_native_boundary(tmp_path):
    work = tmp_path / "task"
    work.mkdir()
    vectors = {
        "empty": b"",
        "abc": b"abc",
        "all-bytes": bytes(range(256)),
        "nul-bytes": b"one\x00two\xffthree",
        "ação-日本語": "Ação e memória 日本語".encode("utf-8"),
        "chunk-boundary": b"x" * 65537,
        "maximum-input": bytes(range(256)) * 8192,
    }
    for name, data in vectors.items():
        (work / name).write_bytes(data)
    (work / "vectors.json").write_text(json.dumps(list(vectors)), encoding="utf-8")
    script = (
        "import importlib.util,json,sys;from pathlib import Path;"
        f"r=Path({str(ROOT)!r});"
        "s=importlib.util.spec_from_file_location('nexus',r/'__init__.py',submodule_search_locations=[str(r)]);"
        "p=importlib.util.module_from_spec(s);sys.modules['nexus']=p;s.loader.exec_module(p);"
        "from nexus.adapters.verify_direct import hash_cng;"
        "print(json.dumps({name:hash_cng(name) for name in json.loads(Path('vectors.json').read_text())}))"
    )
    with launch_confined([sys.executable, "-I", "-c", script], cwd=work,
            env=task_environment(work), read_roots=(ROOT, sys.prefix, sys.base_prefix)) as proc:
        stdout, stderr = proc.communicate(timeout=30)
        code = proc.returncode
    assert code == 0, stderr.decode("utf-8", errors="replace")
    results = json.loads(stdout)
    assert set(results) == set(vectors)
    for name, data in vectors.items():
        assert results[name] == {"status": "PASS", "sha256": hashlib.sha256(data).hexdigest(),
                                  "capability": "windows.cng-sha256"}
        assert (work / name).read_bytes() == data
