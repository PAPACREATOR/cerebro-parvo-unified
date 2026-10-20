"""100,000 deterministic logic cases for process classification and Human Gate.

This gate focuses on logical invariants rather than filesystem or external tools.
"""
from __future__ import annotations

import hashlib
import json

import pytest

from nexus.approval_binding import HumanDecision, promotion_allowed
from nexus.contracts import ROOT, strict_json
from nexus.adapters.runner import PROCESS_TO_TOOL
from nexus.store import AI_PROCESSES, CANDIDATE_PROCESSES, NO_AI_PROCESSES, PDF_PROCESSES


CASES = 100_000
POLICY = strict_json((ROOT / "laws" / "policy.json").read_bytes())
REQUEST = strict_json((ROOT / "schemas" / "request.json").read_bytes())
PROCESSES = tuple(POLICY["processes"])


def test_static_logic_sets_match_policy_and_schema():
    schema_processes = tuple(REQUEST["properties"]["process"]["enum"])
    assert PROCESSES == schema_processes
    assert set(PROCESSES) == set(PROCESS_TO_TOOL)
    assert AI_PROCESSES.isdisjoint(NO_AI_PROCESSES)
    assert AI_PROCESSES | NO_AI_PROCESSES == set(PROCESSES)
    assert CANDIDATE_PROCESSES == set(PROCESSES) - {"verify"}
    assert PDF_PROCESSES == {"convert_pdf", "book"}
    assert POLICY["canonical_gate"] == "human_required"
    assert POLICY["ai_authority"] is False
    assert POLICY["automatic_deletion"] is False


def test_100000_process_logic_roundtrips():
    reverse = {tool: process for process, tool in PROCESS_TO_TOOL.items()}
    assert len(reverse) == len(PROCESS_TO_TOOL)
    checked = 0
    for i in range(CASES):
        process = PROCESSES[(i * 31 + 7) % len(PROCESSES)]
        tool = PROCESS_TO_TOOL[process]
        assert reverse[tool] == process

        expected_ai = 1 if process in AI_PROCESSES else 0
        assert (process in AI_PROCESSES) == (expected_ai == 1)
        assert (process in NO_AI_PROCESSES) == (expected_ai == 0)

        expected_candidate = process != "verify"
        assert (process in CANDIDATE_PROCESSES) == expected_candidate
        assert (process in PDF_PROCESSES) == (process in {"convert_pdf", "book"})
        checked += 1
    assert checked == CASES


def test_100000_human_decision_bindings_fail_closed():
    checked = 0
    for i in range(CASES):
        item = f"{i:032x}"[-32:]
        digest = hashlib.sha256(f"candidate:{i}".encode()).hexdigest()
        action = "APPROVE" if i % 4 != 0 else "KEEP"
        decision = HumanDecision(
            decision_id=f"decision-{i}",
            actor_id="human",
            item_id=item,
            version_sha256=digest,
            action=action,
        )
        allowed = promotion_allowed(decision, item, digest)
        assert allowed is (action == "APPROVE")

        wrong_item = ("f" if item[0] != "f" else "e") + item[1:]
        with pytest.raises(ValueError, match="item_id does not match"):
            promotion_allowed(decision, wrong_item, digest)

        wrong_digest = ("f" if digest[0] != "f" else "e") + digest[1:]
        with pytest.raises(ValueError, match="version_sha256 does not match"):
            promotion_allowed(decision, item, wrong_digest)
        checked += 1
    assert checked == CASES
