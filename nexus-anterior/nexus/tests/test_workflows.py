import hashlib

import pytest

from nexus.tests._mcp_baseline import execute
from nexus.adapters.verify_direct import POLICY
from nexus.adapters.tools import compare, report
from nexus.contracts import Blocked, validate


@pytest.mark.parametrize("left,right,outcome,status", [
    (("PASS", "abc"), ("PASS", "abc"), "agreement", "PASS"),
    (("PASS", "abc"), ("PASS", "def"), "conflict", "UNKNOWN"),
    (("UNKNOWN", None), ("PASS", "abc"), "unknown", "UNKNOWN"),
    (("FAIL", None), ("PASS", "abc"), "failure", "FAIL"),
])
def test_comparison_preserves_both_sides(left, right, outcome, status):
    a = dict(status=left[0], sha256=left[1], capability="A")
    b = dict(status=right[0], sha256=right[1], capability="B")
    compared = compare(a, b)
    assert compared == dict(outcome=outcome, a=a, b=b)
    value = report(dict(comparison=compared, status=status))
    validate("result", value)
    assert [v["value"] for v in value["evidence"]] == [left[1], right[1]]


def test_real_redundant_workflow(tmp_path):
    run = tmp_path / "runs" / ("a" * 32)
    run.mkdir(parents=True)
    source = run / "input.bin"
    source.write_text("Olá Nexus", encoding="utf-8")
    response = execute("verify", source)
    value = validate("result", response["result"])
    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    assert value["outcome"] == "agreement"
    assert value["ai_calls"] == 0
    assert response["trace"]["engine"] == "nexus/python-mcp"
    assert response["trace"]["summary"]["usage"]["total_tokens"] == 0
    assert [item["value"] for item in value["evidence"]] == [expected, expected]


def test_unknown_process_is_blocked(tmp_path):
    with pytest.raises(Blocked):
        execute("unknown", tmp_path / "input.txt")


def test_verify_policy_matches_contract():
    sample = {
        "status": "PASS", "outcome": "agreement", "title": "x",
        "markdown": "x", "evidence": [
            {"capability": "x", "status": "PASS", "value": "x"}
        ], "ai_calls": 0,
    }
    for outcome, status in POLICY.items():
        validate("result", {**sample, "outcome": outcome, "status": status})
