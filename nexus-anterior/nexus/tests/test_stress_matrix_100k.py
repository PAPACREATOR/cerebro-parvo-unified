"""100k deterministic contract cases; no external tools or AI."""
import json
import random

import pytest

from nexus.adapters.tools import compare
from nexus.approval_binding import HumanDecision, promotion_allowed
from nexus.contracts import strict_json


SEED = 20261004
COMPARE_CASES = 50_000
APPROVAL_CASES = 30_000
JSON_CASES = 20_000
TOTAL_CASES = COMPARE_CASES + APPROVAL_CASES + JSON_CASES


def _sha(rng):
    return "".join(rng.choice("0123456789abcdef") for _ in range(64))


def _comparison_oracle(a, b):
    if a["status"] == "FAIL" or b["status"] == "FAIL":
        return "failure"
    if a["status"] != "PASS" or b["status"] != "PASS" or not a.get("sha256") or not b.get("sha256"):
        return "unknown"
    return "agreement" if a["sha256"] == b["sha256"] else "conflict"


def test_50000_bidirectional_comparison_cases():
    rng = random.Random(SEED)
    statuses = ("PASS", "FAIL", "UNKNOWN")
    for case_id in range(COMPARE_CASES):
        same = rng.randrange(4) == 0
        left_hash = _sha(rng) if rng.randrange(5) else None
        right_hash = left_hash if same else (_sha(rng) if rng.randrange(5) else None)
        a = {"status": rng.choice(statuses), "sha256": left_hash, "capability": "A"}
        b = {"status": rng.choice(statuses), "sha256": right_hash, "capability": "B"}

        forward = compare(a, b)
        reverse = compare(b, a)
        expected = _comparison_oracle(a, b)

        assert forward["outcome"] == expected, ("compare-forward", SEED, case_id, a, b, forward)
        assert reverse["outcome"] == expected, ("compare-reverse", SEED, case_id, a, b, reverse)
        assert forward["a"] == a and forward["b"] == b
        assert reverse["a"] == b and reverse["b"] == a


def test_30000_human_decision_binding_cases():
    rng = random.Random(SEED + 1)
    actions = ("APPROVE", "KEEP", "DELETE")
    for case_id in range(APPROVAL_CASES):
        item = f"run-{case_id:08d}"
        version = _sha(rng)
        action = rng.choice(actions)
        decision = HumanDecision(f"decision-{case_id}", "human-test", item, version, action)

        assert promotion_allowed(decision, item, version) is (action == "APPROVE"), (
            "approval-forward", SEED + 1, case_id, action)

        wrong_item = item + "-other"
        with pytest.raises(ValueError):
            promotion_allowed(decision, wrong_item, version)

        replacement = ("0" if version[0] != "0" else "1") + version[1:]
        with pytest.raises(ValueError):
            promotion_allowed(decision, item, replacement)


def test_20000_strict_json_roundtrip_cases():
    rng = random.Random(SEED + 2)
    for case_id in range(JSON_CASES):
        value = {
            "case_id": case_id,
            "text": f"Nexus ação {case_id} 日本語",
            "flag": bool(case_id & 1),
            "count": rng.randrange(-1_000_000, 1_000_001),
            "items": [rng.randrange(1000), None, f"x-{rng.randrange(1000)}"],
        }
        raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        decoded = strict_json(raw)
        assert decoded == value, ("json-roundtrip", SEED + 2, case_id, raw, decoded)

        duplicate = '{"case_id":' + str(case_id) + ',"case_id":' + str(case_id + 1) + '}'
        with pytest.raises(ValueError):
            strict_json(duplicate)


def test_stress_case_budget_is_exactly_100000():
    assert TOTAL_CASES == 100_000
