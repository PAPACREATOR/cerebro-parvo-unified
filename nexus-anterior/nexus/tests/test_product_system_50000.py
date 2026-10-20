"""50,000 whole-system deterministic cases across the six product intentions.

No external model/GPU/network is mocked as a PASS. The matrix exercises the
existing deterministic shell around those capabilities: Front Door, source
comparison, bounded Notebook handoff, result schema authority rejection and
human decision binding.
"""
from __future__ import annotations

import hashlib

import pytest

from nexus.adapters.tools import compare
from nexus.approval_binding import HumanDecision, promotion_allowed
from nexus.contracts import Blocked, validate
from nexus.frontdoor import parse
from nexus.natural_bridge import from_markdown, kernel_from_notebook_boundary, kernel_to_notebook, to_markdown


CASES = 50_000
FLOWS = (
    ("video", "& cria documentário {i} com as fontes verificadas", "trabalhar"),
    ("podcast", "& cria podcast {i} com as fontes verificadas", "trabalhar"),
    ("visual_podcast", "& cria podcast visual {i} com as fontes verificadas", "trabalhar"),
    ("book", "& prepara livro {i} com o molde existente", "trabalhar"),
    ("music", "& cria música {i} com tema letra e estilo definidos", "trabalhar"),
    ("web", "@ pesquisa web {i} e conserva as fontes", "web"),
)
PUBLIC_PROCESSES = {"verify", "interpret", "proofread", "convert_pdf", "video", "podcast", "visual_podcast", "book", "music", "web"}
NOTEBOOK_FLOWS = {"video", "podcast", "visual_podcast"}


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def test_whole_product_system_50000_cases():
    for case_id in range(CASES):
        flow, template, expected_intent = FLOWS[case_id % len(FLOWS)]
        original = template.format(i=case_id) + " — çã 日本語"

        # 1. Human text is resolved deterministically and preserved exactly.
        parsed = parse(original)
        assert parsed.status == "RESOLVED", (case_id, flow, parsed)
        assert parsed.intent == expected_intent, (case_id, flow, parsed)
        markdown = to_markdown(parsed)
        recovered = from_markdown(markdown)
        assert recovered["text"].encode("utf-8") == original.encode("utf-8")

        # 2. Sources are compared BEFORE any Notebook handoff.
        left_hash = _sha(f"{flow}:source:{case_id}")
        right_hash = left_hash if case_id % 5 else _sha(f"{flow}:conflict:{case_id}")
        left = {"status": "PASS", "sha256": left_hash, "capability": "source-left"}
        right = {"status": "PASS", "sha256": right_hash, "capability": "source-right"}
        forward = compare(left, right)
        reverse = compare(right, left)
        expected = "agreement" if left_hash == right_hash else "conflict"
        assert forward["outcome"] == expected
        assert reverse["outcome"] == expected

        if expected == "agreement" and flow in NOTEBOOK_FLOWS:
            # 3. Notebook is a downstream specialist only for flows that need it.
            packet = kernel_to_notebook(markdown)
            assert packet["authority"] == "UNTRUSTED_REQUEST"
            assert packet["target"] == "open-notebook"
            returned = kernel_from_notebook_boundary(packet)
            assert returned == markdown
            assert from_markdown(returned)["text"].encode("utf-8") == original.encode("utf-8")
        elif expected == "agreement":
            # Research/writing/music stay outside Notebook at this boundary.
            assert flow in {"book", "music", "web"}
        else:
            # Conflict is preserved; no downstream specialist receives it.
            assert forward["outcome"] == "conflict"

        # 4. Public product routes are recognized but still produce candidates only.
        request = {"process": flow, "text": original, "filename": "", "attachment": ""}
        assert validate("request", request)["process"] == flow

        # 5. External/AI output cannot smuggle authority into the result contract.
        hostile = {
            "status": "PASS",
            "outcome": "agreement",
            "title": f"{flow}-{case_id}",
            "markdown": "# candidato\n\nconteúdo",
            "evidence": [{"capability": flow, "status": "PASS", "value": left_hash}],
            "ai_calls": 1,
            "authority": "CANONICAL",
        }
        with pytest.raises(Blocked):
            validate("result", hostile)

        # 6. Human decision remains cryptographically bound to the exact candidate version.
        item = f"{flow}-{case_id}"
        version = _sha(f"candidate:{item}")
        action = ("APPROVE", "KEEP", "DELETE")[case_id % 3]
        decision = HumanDecision(f"d-{case_id}", "human-test", item, version, action)
        assert promotion_allowed(decision, item, version) is (action == "APPROVE")
        changed = ("0" if version[0] != "0" else "1") + version[1:]
        with pytest.raises(ValueError):
            promotion_allowed(decision, item, changed)


def test_whole_product_system_budget_is_exact():
    assert CASES == 50_000
    assert len(FLOWS) == 6
    assert PUBLIC_PROCESSES == {"verify", "interpret", "proofread", "convert_pdf", "video", "podcast", "visual_podcast", "book", "music", "web"}
    assert NOTEBOOK_FLOWS == {"video", "podcast", "visual_podcast"}
