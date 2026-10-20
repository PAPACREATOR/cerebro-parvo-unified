"""Independent review of Kernel-owned crash/restart reconciliation.

Synthetic data only. This file does not implement recovery; it verifies the
already-implemented T01 contract from the Work branch.
"""
import json

import pytest

from nexus.contracts import Blocked
from nexus.store import Store
from nexus.tests.test_store import request, result


def test_restart_reconciles_durable_executor_result_without_generic_fail(tmp_path):
    """Executor output is durable; Kernel crashed before Store.accept.

    Restart must reconcile the saved result without creating Canonical or
    degrading the operation to a generic FAIL.
    """
    store = Store(tmp_path)
    run_id = store.create(request())
    run = store.path("runs", run_id)

    envelope = {
        "result": result(),
        "trace": {
            "engine": "synthetic-disposable-executor",
            "version": "synthetic",
            "summary": {"status": "completed"},
            "events": [],
        },
    }
    raw = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
    (run / "execution.stdout.json").write_bytes(raw)
    (run / "execution.stderr.txt").write_bytes(b"")

    restarted = Store(tmp_path)
    state = restarted.state(run_id)

    assert state["status"] == "HUMAN_REQUIRED"
    assert state["status"] != "FAIL"
    assert (run / "execution.stdout.json").read_bytes() == raw
    assert restarted.check_candidate(state)["execution"]["engine"] == "synthetic-disposable-executor"
    assert not restarted.path("canonical", run_id).exists()


def test_restart_after_kernel_dies_during_executor_is_recovery_required(tmp_path, monkeypatch):
    """FAIL-first: distinguish PREPARED from an external execution already entered.

    If the Kernel dies after declaring entry into an external capability but before
    a durable result exists, restart must preserve uncertainty. It must not claim a
    generic FAIL and must not retry automatically.
    """
    from nexus.host import Host

    host = Host(tmp_path)
    run_id = host.store.create(request())
    seen_phase = []

    def crash_after_external_entry(*args, **kwargs):
        seen_phase.append(host.store.state(run_id).get("execution_phase"))
        raise SystemExit("synthetic hard crash during executor")

    # This is a phase/recovery unit double, not a native execution proof.
    # Select the Windows branch without changing the global platform module.
    from types import SimpleNamespace
    from nexus import host as host_module
    monkeypatch.setattr(host_module, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr("nexus.host.launch_confined", crash_after_external_entry)

    host.busy.acquire()
    with pytest.raises(SystemExit, match="synthetic hard crash"):
        host._run(run_id)

    assert seen_phase == ["EXECUTING"]

    restarted = Store(tmp_path)
    state = restarted.state(run_id)

    assert state["status"] == "BLOCKED"
    assert state["commit_status"] == "RECOVERY_REQUIRED"
    assert state["execution_phase"] == "EXECUTING"
    assert (restarted.path("runs", run_id) / "input.bin").is_file()
    assert not (restarted.path("runs", run_id) / "execution.stdout.json").exists()
    assert not restarted.path("canonical", run_id).exists()


def test_accepted_result_closes_external_execution_phase(tmp_path):
    """FAIL-first: a durable accepted result must not remain marked EXECUTING."""
    store = Store(tmp_path)
    run_id = store.create(request())
    prepared = store.state(run_id)
    assert prepared["execution_phase"] == "PREPARED"

    trace = {
        "engine": "synthetic-disposable-executor",
        "events": [],
        "process_sha256": prepared["process_sha256"],
    }
    state = store.accept(run_id, result(), trace)

    assert state["status"] == "HUMAN_REQUIRED"
    assert state["execution_phase"] == "RESULT_ACCEPTED"
    assert store.check_candidate(state)["execution"]["process_sha256"] == prepared["process_sha256"]
    assert not store.path("canonical", run_id).exists()


def test_restart_never_reconciles_redirected_executor_output(tmp_path):
    """FAIL-first security: recovery must not follow executor-output symlinks."""
    store = Store(tmp_path / "data")
    run_id = store.create(request())
    state = store.state(run_id)
    store.update(run_id, execution_phase="EXECUTING")

    outside = tmp_path / "outside-result.json"
    envelope = {
        "result": result(),
        "trace": {
            "engine": "synthetic-outside",
            "events": [],
            "process_sha256": state["process_sha256"],
        },
    }
    outside.write_text(json.dumps(envelope, ensure_ascii=False), encoding="utf-8")

    execution = store.path("runs", run_id) / "execution.stdout.json"
    try:
        execution.symlink_to(outside)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"symlink unavailable on this platform: {error}")

    restarted = Store(tmp_path / "data")
    recovered = restarted.state(run_id)

    assert recovered["status"] == "BLOCKED"
    assert recovered["commit_status"] == "RECOVERY_REQUIRED"
    assert execution.is_symlink()
    assert outside.read_text("utf-8") == json.dumps(envelope, ensure_ascii=False)
    assert not restarted.path("creative", run_id).exists()
    assert not restarted.path("canonical", run_id).exists()


def test_restart_refuses_redirected_authoritative_state(tmp_path):
    """FAIL-first security: authoritative state.json must never be followed outside."""
    root = tmp_path / "data"
    store = Store(root)
    run_id = store.create(request())
    state_path = store.path("runs", run_id) / "state.json"
    original = state_path.read_bytes()

    outside = tmp_path / "outside-state.json"
    outside.write_bytes(original)
    state_path.unlink()
    try:
        state_path.symlink_to(outside)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"symlink unavailable on this platform: {error}")

    with pytest.raises(Blocked):
        Store(root)

    assert state_path.is_symlink()
    assert outside.read_bytes() == original
    assert not store.path("canonical", run_id).exists()
