"""Independent consistency checks across the existing authority boundaries."""
import json
from html.parser import HTMLParser

import pytest

from nexus.adapters.runner import PROCESS_FILES, PROCESS_TO_TOOL, process_fingerprint
from nexus.contracts import ROOT, Blocked, load_policy, strict_json, validate
from nexus.store import AI_PROCESSES, CANDIDATE_PROCESSES, NO_AI_PROCESSES, PDF_PROCESSES, Store
from nexus.tests.test_store import candidate, execution_trace, request, result


class ProcessChoices(HTMLParser):
    def __init__(self):
        super().__init__()
        self.values = []

    def handle_starttag(self, tag, attrs):
        fields = dict(attrs)
        if tag == "input" and fields.get("name") == "process":
            self.values.append(fields["value"])


def test_internal_process_contracts_match_while_normal_ui_hides_technical_selector():
    policy = load_policy()["processes"]
    schema = strict_json((ROOT / "schemas/request.json").read_bytes())
    frontdoor_rules = strict_json((ROOT / "frontdoor_rules.json").read_bytes())
    choices = ProcessChoices()
    choices.feed((ROOT / "ui/index.html").read_text("utf-8"))

    # The normal Folha no longer asks the person to choose an internal process.
    # Internal diagnostic/API process contracts still have to agree exactly.
    assert choices.values == []
    assert set(policy) == set(schema["properties"]["process"]["enum"])
    assert set(policy) == set(PROCESS_TO_TOOL) == set(PROCESS_FILES)
    mapped = {rule["process"] for rule in frontdoor_rules["operation_rules"]}
    # The Folha now proposes exactly one verification and two explicit Writer
    # PDF exports. No technical process selector or arbitrary tool dispatch.
    assert mapped == {"verify", "convert_pdf", "book"}
    assert mapped <= set(policy)
    by_process = {rule["process"]: rule for rule in frontdoor_rules["operation_rules"]}
    assert len(by_process) == len(frontdoor_rules["operation_rules"])
    assert by_process["convert_pdf"] == {
        "process": "convert_pdf", "intent": "trabalhar",
        "requires_attachment": True, "patterns": [r"^converter para pdf$"],
    }
    assert by_process["book"] == {
        "process": "book", "intent": "trabalhar",
        "requires_attachment": True, "patterns": [r"^exportar manuscrito para pdf$"],
    }
    assert by_process["verify"]["requires_attachment"] is True
    assert len(set(PROCESS_TO_TOOL.values())) == len(policy)
    assert AI_PROCESSES.isdisjoint(NO_AI_PROCESSES)
    assert AI_PROCESSES | NO_AI_PROCESSES == set(policy)
    assert CANDIDATE_PROCESSES == set(policy) - {"verify"}
    assert PDF_PROCESSES == {"book", "convert_pdf"}
    for process in policy:
        assert len(process_fingerprint(process)) == 64
        for relative in PROCESS_FILES[process]:
            assert (ROOT / relative).is_file()


@pytest.mark.parametrize("process", ["shell", "approve", "canonical", "unknown"])
def test_schema_cannot_authorize_a_process_outside_policy(process):
    assert process not in load_policy()["processes"]
    with pytest.raises(Blocked):
        validate("request", dict(request(), process=process))


@pytest.mark.parametrize("process", load_policy()["processes"])
def test_store_rejects_wrong_ai_or_artifact_contract_before_creative(tmp_path, process):
    store = Store(tmp_path)
    run = store.create(dict(request(), process=process))
    output = result()
    if process in CANDIDATE_PROCESSES:
        output.update(status="UNKNOWN", outcome="candidate")
    output["ai_calls"] = 0 if process in AI_PROCESSES else 1
    with pytest.raises(Blocked):
        store.accept(run, output, execution_trace(store, run))
    assert not store.path("creative", run).exists()
    output["ai_calls"] = 1 if process in AI_PROCESSES else 0
    if process not in PDF_PROCESSES:
        output["artifact"] = {"name": "resultado.pdf", "sha256": "0" * 64}
    with pytest.raises(Blocked):
        store.accept(run, output, execution_trace(store, run))
    assert store.state(run)["status"] == "RUNNING"
    assert not store.path("creative", run).exists()
    assert not store.path("canonical", run).exists()


def test_committed_canonical_survives_new_fingerprint_but_running_recovery_is_blocked(tmp_path, monkeypatch):
    from nexus.store import HumanDecision
    store = Store(tmp_path)
    approved = candidate(store)
    state = store.state(approved)
    store.promote(approved, HumanDecision("test-human-decision", "human", approved,
                                        state["candidate_sha256"], "APPROVE"))
    original_package = {p.name: p.read_bytes() for p in store.path("canonical", approved).iterdir()}
    pending = store.create(request())
    envelope = {"result": result(), "trace": execution_trace(store, pending)}
    (store.path("runs", pending) / "execution.stdout.json").write_text(json.dumps(envelope), encoding="utf-8")
    monkeypatch.setattr("nexus.adapters.runner.process_fingerprint", lambda _: "0" * 64)
    restored = Store(tmp_path)
    restored.check_commit(restored.state(approved))
    assert restored.state(approved)["status"] == "PASS"
    assert {p.name: p.read_bytes() for p in restored.path("canonical", approved).iterdir()} == original_package
    assert restored.state(pending)["status"] == "BLOCKED"
    assert not restored.path("creative", pending).exists()
    assert not restored.path("canonical", pending).exists()

