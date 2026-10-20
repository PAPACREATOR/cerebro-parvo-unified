"""Native hash probe under Host's reduced environment and hidden console."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from nexus.contracts import ROOT
from nexus.host import process_environment

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Requires native Windows PowerShell")


def execute_hash(source, work):
    code = (
        "import json,sys;"
        "sys.path.insert(0, " + repr(str(ROOT.parent)) + ");"
        "from nexus.adapters.verify_direct import hash_windows;"
        "print(json.dumps(hash_windows(sys.argv[1])))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(source)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=ROOT,
        env=process_environment(work),
        creationflags=subprocess.CREATE_NO_WINDOW,
        timeout=20,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    return json.loads(result.stdout.decode("utf-8"))


@pytest.mark.parametrize("filename,raw", [
    ("simple.txt", b"Nexus synthetic text\n"),
    ("ação ' & $ com espaços.bin", bytes(range(256))),
    ("empty.bin", b""),
])
def test_hash_runs_without_user_environment(tmp_path, filename, raw):
    source = tmp_path / filename
    source.write_bytes(raw)
    payload = execute_hash(source, tmp_path)
    assert payload == {
        "status": "PASS",
        "sha256": hashlib.sha256(raw).hexdigest(),
        "capability": "windows.dotnet-sha256",
    }
    assert source.read_bytes() == raw


def test_missing_file_returns_json_failure(tmp_path):
    payload = execute_hash(tmp_path / "missing.bin", tmp_path)
    assert payload["status"] == "FAIL"
    assert payload["sha256"] is None
    assert payload["capability"] == "windows.dotnet-sha256"
