"""Real process death around Canonical publication; no power-loss claim."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from nexus.store import Store, digest


CHILD = r'''
import os, sys
from pathlib import Path
import nexus.store as storage
from nexus.tests.test_store import candidate

root, window = Path(sys.argv[1]), sys.argv[2]
store = storage.Store(root)
run = candidate(store)
real_atomic, real_rename, real_update = storage.atomic, storage.os.rename, store.update

def atomic(path, data):
    real_atomic(path, data)
    if window == "staged-content" and Path(path).parent.name.startswith(".approval-"):
        os._exit(91)

def rename(source, target):
    if window == "before-publication":
        os._exit(92)
    real_rename(source, target)
    if window == "after-publication":
        os._exit(93)

def update(*args, **kwargs):
    value = real_update(*args, **kwargs)
    if window == "after-state":
        os._exit(94)
    return value

storage.atomic, storage.os.rename, store.update = atomic, rename, update
state = store.state(run)
decision = storage.HumanDecision("synthetic-human-decision", "test-human", run,
                                 state["candidate_sha256"], "APPROVE")
store.promote(run, decision)
raise AssertionError("crash boundary was not reached")
'''


@pytest.mark.parametrize("window,code,published", [
    ("staged-content", 91, False),
    ("before-publication", 92, False),
    ("after-publication", 93, True),
    ("after-state", 94, True),
])
def test_real_canonical_crash_preserves_complete_package_and_recovery(tmp_path, monkeypatch, window, code, published):
    root = tmp_path / "data"
    crashed = subprocess.run([sys.executable, "-c", CHILD, str(root), window],
                             cwd=Path(__file__).resolve().parents[2],
                             capture_output=True, timeout=30,
                             env=dict(os.environ, PYTHONUTF8="1"))
    assert crashed.returncode == code, (crashed.stdout, crashed.stderr)
    runs = list((root / "runs").iterdir())
    assert len(runs) == 1
    run = runs[0].name
    original = (runs[0] / "input.bin").read_bytes()
    creative = {p.name: p.read_bytes() for p in (root / "creative" / run).iterdir()}
    final = root / "canonical" / run
    assert final.exists() is published
    canonical = {p.name: p.read_bytes() for p in final.iterdir()} if published else {}
    if published:
        assert set(canonical) == {"content.md", "approval.json", "provenance.json"}
        assert canonical["content.md"] == creative["content.md"]
        assert json.loads(canonical["approval.json"])["sha256"] == digest(canonical["content.md"])

    def no_tool(*args, **kwargs):
        pytest.fail("Recovery attempted a new external execution")

    monkeypatch.setattr("nexus.adapters.runner.execute", no_tool)
    monkeypatch.setattr("nexus.host.launch_confined", no_tool)
    monkeypatch.setattr("nexus.adapters.notebook.fetch_output", no_tool)
    for _ in range(3):
        recovered = Store(root)
        state = recovered.state(run)
        assert state["status"] == ("PASS" if published else "HUMAN_REQUIRED")
        if published:
            assert state["commit_status"] == "COMMITTED"
            recovered.check_commit(state)
            assert {p.name: p.read_bytes() for p in final.iterdir()} == canonical
        else:
            assert not final.exists()
        assert (runs[0] / "input.bin").read_bytes() == original
        assert {p.name: p.read_bytes() for p in (root / "creative" / run).iterdir()} == creative
        assert not (runs[0] / "execution.stdout.json").exists()

