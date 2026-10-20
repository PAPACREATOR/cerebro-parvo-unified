import base64
import uuid
import pytest
from nexus.contracts import Blocked, strict_json, validate, load_policy
from nexus.store import Store, HumanDecision


def request(**overrides):
    return dict(process="verify", text="Um ensaio Nexus.", filename="", attachment="", **overrides)


def result():
    return {"status": "PASS", "outcome": "agreement", "title": "Verificação",
            "markdown": "# Verificação\n\nDois métodos concordam.",
            "evidence": [{"capability": "test", "status": "PASS", "value": "abc"}], "ai_calls": 0}


def execution_trace(store, run, **extra):
    return {"process_sha256": store.state(run)["process_sha256"], **extra}


def candidate(store):
    run = store.create(request())
    store.accept(run, result(), execution_trace(store, run, test=True))
    return run


@pytest.mark.parametrize("raw", ['{', '{"a":1,"a":2}', '{"a":NaN}', ''])
def test_bad_json(raw):
    with pytest.raises(Blocked):
        strict_json(raw)


def test_schema_and_laws():
    assert load_policy()["canonical_gate"] == "human_required"
    for raw in ({}, {**result(), "authority": "approve"}, {**result(), "markdown": " "}):
        with pytest.raises(Blocked):
            validate("result", raw)


def test_empty_input(tmp_path):
    with pytest.raises(Blocked):
        Store(tmp_path).create(dict(process="verify", text="", filename="", attachment=""))


def test_gate_bypass_and_similarity_blocked(tmp_path):
    store = Store(tmp_path)
    run = candidate(store)
    for fake in (None, {"action": "APPROVE"}, True):
        with pytest.raises(Blocked):
            store.promote(run, fake)
    with pytest.raises(Blocked):
        store.delete(run, reason="similaridade")
    assert list((tmp_path / "canonical").iterdir()) == []


def test_explicit_bound_approval_and_restart(tmp_path):
    store = Store(tmp_path)
    run = candidate(store)
    state = store.state(run)
    decision = HumanDecision(uuid.uuid4().hex, "human-test", run, state["candidate_sha256"], "APPROVE")
    store.promote(run, decision)
    assert Store(tmp_path).state(run)["status"] == "PASS"
    store.promote(run, decision)
    assert len(list((tmp_path / "canonical").iterdir())) == 1
    assert (tmp_path / "canonical" / run / "approval.json").exists()


def test_changed_content_and_wrong_destination(tmp_path):
    store = Store(tmp_path)
    run = candidate(store)
    decision = HumanDecision("d1", "human", run, store.state(run)["candidate_sha256"], "APPROVE")
    with pytest.raises(Blocked):
        store.promote(run, decision, destination="other")
    (tmp_path / "creative" / run / "content.md").write_text("changed", encoding="utf-8")
    with pytest.raises(Blocked):
        store.promote(run, decision)


def test_unknown_is_preserved(tmp_path):
    store = Store(tmp_path)
    run = store.create(request())
    output = result()
    output.update(status="UNKNOWN", outcome="conflict")
    assert store.accept(run, output, execution_trace(store, run))["result_status"] == "UNKNOWN"


def test_interrupted_run_and_ai_capability(tmp_path):
    store = Store(tmp_path)
    run = store.create(request())
    output = result()
    output["ai_calls"] = 1
    with pytest.raises(Blocked):
        store.accept(run, output, execution_trace(store, run))
    assert Store(tmp_path).state(run)["status"] == "FAIL"


def test_unregistered_process_and_path(tmp_path):
    store = Store(tmp_path)
    with pytest.raises(Blocked):
        store.create(dict(process="shell", text="hello", filename="", attachment=""))
    with pytest.raises(Blocked):
        store.state("../canonical")


def test_accept_rejects_trace_from_different_workflow_version(tmp_path):
    """A result cannot be accepted if its execution trace is not bound to the pinned workflow."""
    store = Store(tmp_path)
    run = store.create(request())
    with pytest.raises(Blocked):
        store.accept(run, result(), {"process_sha256": "0" * 64})
    assert not store.path("creative", run).exists()
    assert store.state(run)["status"] == "RUNNING"
