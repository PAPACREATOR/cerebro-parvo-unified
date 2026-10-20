import hashlib
import inspect
import os
import subprocess
import sys
from pathlib import Path

import nexus.store as store_module
from nexus.store import Store


EXPECTED_TEXT = "bytes preservados após crash"
EXPECTED = EXPECTED_TEXT.encode("utf-8")


def _run(script, tmp_path):
    return subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)],
        cwd=str(Path(__file__).parents[2]),
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_restart_surfaces_create_crash_after_input_is_durable(tmp_path):
    script = r"""
import os
import sys
from pathlib import Path
import nexus.store as store_module

root = Path(sys.argv[1])
real_atomic = store_module.atomic
calls = {"count": 0}

def crash_after_first_durable_write(path, data):
    real_atomic(path, data)
    calls["count"] += 1
    if calls["count"] == 1:
        os._exit(91)

store_module.atomic = crash_after_first_durable_write
request = {
    "process": "verify",
    "text": "bytes preservados após crash",
    "filename": "",
    "attachment": "",
}
store_module.Store(root).create(request)
"""
    crashed = _run(script, tmp_path)
    assert crashed.returncode == 91, crashed.stdout + crashed.stderr

    runs = [path for path in (tmp_path / "runs").iterdir() if path.is_dir()]
    assert len(runs) == 1
    run = runs[0]
    original = run / "input.bin"
    assert original.read_bytes() == EXPECTED
    assert not (run / "state.json").exists()

    restarted = Store(tmp_path)
    recovered = restarted.state(run.name)

    assert recovered["status"] == "BLOCKED"
    assert recovered["commit_status"] == "RECOVERY_REQUIRED"
    assert recovered["run_id"] == run.name
    assert recovered["input_sha256"] == hashlib.sha256(EXPECTED).hexdigest()
    assert original.read_bytes() == EXPECTED
    assert not (tmp_path / "canonical" / run.name).exists()


def test_restart_preserves_temp_if_process_dies_before_atomic_replace(tmp_path):
    script = r"""
import os
import sys
from pathlib import Path
import nexus.store as store_module

root = Path(sys.argv[1])

def die_before_replace(source, target):
    os._exit(92)

store_module._replace_durable = die_before_replace
request = {
    "process": "verify",
    "text": "bytes preservados após crash",
    "filename": "",
    "attachment": "",
}
store_module.Store(root).create(request)
"""
    crashed = _run(script, tmp_path)
    assert crashed.returncode == 92, crashed.stdout + crashed.stderr

    runs = [path for path in (tmp_path / "runs").iterdir() if path.is_dir()]
    assert len(runs) == 1
    run = runs[0]
    partials = list(run.glob(".pending-*"))
    assert len(partials) == 1
    assert partials[0].read_bytes() == EXPECTED
    assert not (run / "input.bin").exists()
    assert not (run / "state.json").exists()

    restarted = Store(tmp_path)
    recovered = restarted.state(run.name)
    assert recovered["status"] == "BLOCKED"
    assert recovered["commit_status"] == "RECOVERY_REQUIRED"
    assert "input_sha256" not in recovered
    assert partials[0].read_bytes() == EXPECTED
    assert not (tmp_path / "canonical" / run.name).exists()


def test_restart_recovers_if_process_dies_immediately_after_atomic_replace(tmp_path):
    script = r"""
import os
import sys
from pathlib import Path
import nexus.store as store_module

root = Path(sys.argv[1])
real_replace = store_module._replace_durable

def die_after_replace(source, target):
    real_replace(source, target)
    os._exit(93)

store_module._replace_durable = die_after_replace
request = {
    "process": "verify",
    "text": "bytes preservados após crash",
    "filename": "",
    "attachment": "",
}
store_module.Store(root).create(request)
"""
    crashed = _run(script, tmp_path)
    assert crashed.returncode == 93, crashed.stdout + crashed.stderr

    runs = [path for path in (tmp_path / "runs").iterdir() if path.is_dir()]
    assert len(runs) == 1
    run = runs[0]
    original = run / "input.bin"
    assert original.read_bytes() == EXPECTED
    assert not (run / "state.json").exists()

    restarted = Store(tmp_path)
    recovered = restarted.state(run.name)
    assert recovered["status"] == "BLOCKED"
    assert recovered["commit_status"] == "RECOVERY_REQUIRED"
    assert recovered["input_sha256"] == hashlib.sha256(EXPECTED).hexdigest()
    assert original.read_bytes() == EXPECTED
    assert not (tmp_path / "canonical" / run.name).exists()


def test_atomic_declares_platform_durable_rename_contract():
    source = inspect.getsource(store_module)
    atomic_source = inspect.getsource(store_module.atomic)
    assert "_replace_durable" in atomic_source
    if os.name == "nt":
        assert "MoveFileExW" in source
        assert "MOVEFILE_WRITE_THROUGH" in source
    else:
        assert "_fsync_parent" in source
        assert "os.fsync" in source
