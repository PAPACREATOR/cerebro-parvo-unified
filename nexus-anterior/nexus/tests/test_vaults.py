import pytest
from nexus.store import Store, HumanDecision
from nexus.contracts import Blocked
from nexus.tests.test_store import request, result, candidate, execution_trace


def test_original_and_candidate_survive_promotion_and_restart(tmp_path):
    store = Store(tmp_path)
    run = candidate(store)
    original = (tmp_path / "runs" / run / "input.bin").read_bytes()
    content = (tmp_path / "creative" / run / "content.md").read_bytes()
    store.promote(run, HumanDecision("synthetic-approval", "test-human", run, store.state(run)["candidate_sha256"], "APPROVE"))
    store = Store(tmp_path)
    assert (tmp_path / "runs" / run / "input.bin").read_bytes() == original
    assert (tmp_path / "creative" / run / "content.md").read_bytes() == content
    assert (tmp_path / "canonical" / run / "content.md").read_bytes() == content


@pytest.mark.parametrize("outcome", ["conflict", "unknown"])
def test_approval_does_not_turn_uncertainty_into_truth(tmp_path, outcome):
    store = Store(tmp_path)
    run = store.create(request())
    output = {**result(), "status": "UNKNOWN", "outcome": outcome}
    store.accept(run, output, execution_trace(store, run))
    store.promote(run, HumanDecision("synthetic-approval", "test-human", run, store.state(run)["candidate_sha256"], "APPROVE"))
    assert Store(tmp_path).state(run)["result_status"] == "UNKNOWN"
    assert store.state(run)["outcome"] == outcome


def test_identical_candidates_are_not_silently_deleted(tmp_path):
    store = Store(tmp_path)
    first, second = candidate(store), candidate(store)
    assert first != second
    assert len(list((tmp_path / "creative").iterdir())) == 2
    assert not list((tmp_path / "canonical").iterdir())


def test_incomplete_promotion_never_exposes_partial_canonical(tmp_path, monkeypatch):
    store = Store(tmp_path)
    run = candidate(store)
    def fail_rename(*args):
        raise OSError("synthetic interrupted commit")
    monkeypatch.setattr("nexus.store.os.rename", fail_rename)
    with pytest.raises(OSError):
        store.promote(run, HumanDecision("synthetic-approval", "test-human", run, store.state(run)["candidate_sha256"], "APPROVE"))
    assert not list((tmp_path / "canonical").iterdir())
    assert Store(tmp_path).state(run)["status"] == "HUMAN_REQUIRED"
    assert (tmp_path / "creative" / run / "content.md").exists()


def test_restart_reconciles_commit_after_state_write_failure(tmp_path, monkeypatch):
    store = Store(tmp_path)
    run = candidate(store)
    def fail(*args, **kwargs):
        raise OSError("synthetic crash after canonical publication")
    monkeypatch.setattr(store, "update", fail)
    with pytest.raises(OSError):
        store.promote(run, HumanDecision("test-decision", "test-human", run, store.state(run)["candidate_sha256"], "APPROVE"))
    state = Store(tmp_path).state(run)
    assert state["status"] == "PASS"
    assert state["commit_status"] == "COMMITTED"


@pytest.mark.parametrize("damage", ["content.md", "approval.json", "provenance.json"])
def test_corrupt_commit_blocks_recovery(tmp_path, damage):
    store = Store(tmp_path)
    run = candidate(store)
    store.promote(run, HumanDecision("test-decision", "test-human", run, store.state(run)["candidate_sha256"], "APPROVE"))
    (tmp_path / "canonical" / run / damage).write_bytes(b"corrupt")
    restarted = Store(tmp_path)
    assert restarted.state(run)["commit_status"] == "RECOVERY_REQUIRED"
    assert restarted.state(run)["status"] == "BLOCKED"
    assert (tmp_path / "canonical" / run / damage).read_bytes() == b"corrupt"
