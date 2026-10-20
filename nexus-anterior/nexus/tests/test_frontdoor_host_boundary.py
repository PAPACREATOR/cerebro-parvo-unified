"""Unmapped parser proposals cannot authorize execution on the existing Host.

PASS here proves refusal, not an integrated natural-language Folha.
"""
from urllib.error import HTTPError

import pytest

from nexus.host import Host
from nexus.tests.test_reverse_flow import http


@pytest.mark.parametrize("proposal", [
    {"text": "Guarda esta nota.", "filename": "", "attachment": ""},
    {"text": "Guarda esta nota.", "filename": "", "attachment": "",
     "intent": "arquivo", "status": "RESOLVED"},
    {"process": "verify", "text": "Guarda esta nota.", "filename": "",
     "attachment": "", "intent": "arquivo"},
    {"version": "folha-intent-v1", "status": "RESOLVED", "intent": "arquivo",
     "original": "Guarda esta nota.", "content": "Guarda esta nota.",
     "parser": "eliza-rules-v1", "explicit": False,
     "shadow": None, "execution": "SIMULATED_ONLY"},
])
def test_unmapped_interpretation_cannot_start_a_tool_or_write_knowledge(tmp_path, proposal):
    host = Host(tmp_path)
    with http(host) as call:
        with pytest.raises(HTTPError) as error:
            call("/api/run", proposal)
        assert error.value.code == 403
        assert call("/api/runs") == []
    for name in ("runs", "creative", "canonical"):
        assert not list((tmp_path / name).iterdir())
    assert not host.busy.locked()
