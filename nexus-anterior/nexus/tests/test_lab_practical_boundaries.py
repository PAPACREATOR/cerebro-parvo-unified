"""Practical boundary tests for the Windows Lab.

These tests exercise public Host/Store contracts and, on Windows, the real
deterministic verify workflow. No AI and no external cloud service.
"""
import base64
import hashlib
import os
import time

import pytest

from nexus.contracts import Blocked
from nexus.host import Host
from nexus.store import Store
from nexus.tests.test_reverse_flow import http
from nexus.tests.test_store import request


MIB2 = 2 * 1024 * 1024


def test_attachment_one_byte_over_2mib_is_blocked_without_run(tmp_path):
    raw = b"x" * (MIB2 + 1)
    encoded = base64.b64encode(raw).decode("ascii")
    # 2 MiB and 2 MiB + 1 share this Base64 length, so the Store byte policy
    # must enforce the real decoded-size boundary.
    assert len(encoded) == 2_796_204
    store = Store(tmp_path)
    with pytest.raises(Blocked):
        store.create({
            **request(),
            "text": "boundary",
            "filename": "too-large.bin",
            "attachment": encoded,
        })
    assert not list((tmp_path / "runs").iterdir())
    assert not list((tmp_path / "creative").iterdir())
    assert not list((tmp_path / "canonical").iterdir())


def test_unicode_text_schema_boundary_is_exact(tmp_path):
    store = Store(tmp_path)
    allowed = "á" * 100_000
    run_id = store.create({**request(), "text": allowed})
    assert (store.path("runs", run_id) / "input.bin").read_bytes() == allowed.encode("utf-8")

    before = {p.name for p in (tmp_path / "runs").iterdir()}
    with pytest.raises(Blocked):
        store.create({**request(), "text": allowed + "á"})
    assert {p.name for p in (tmp_path / "runs").iterdir()} == before
    assert not list((tmp_path / "canonical").iterdir())


@pytest.mark.skipif(os.name != "nt", reason="Requires real Windows PowerShell")
def test_real_windows_exact_2mib_attachment_roundtrip_and_restart(tmp_path, monkeypatch):
    raw = bytes(range(256)) * 8192
    assert len(raw) == MIB2
    expected = hashlib.sha256(raw).hexdigest()
    payload = {
        **request(),
        "text": "Verificar anexo no limite exato de 2 MiB",
        "filename": "limite-2MiB ação.bin",
        "attachment": base64.b64encode(raw).decode("ascii"),
    }

    host = Host(tmp_path)
    # Technical boundary test: direct execution is explicitly diagnostic-only.
    with http(host, allow_direct_run=True) as call:
        run_id = call("/api/run", payload)["run_id"]
        deadline = time.monotonic() + 90
        state = call("/api/runs/" + run_id)
        while state["status"] == "RUNNING" and time.monotonic() < deadline:
            time.sleep(.1)
            state = call("/api/runs/" + run_id)

        assert state["status"] == "HUMAN_REQUIRED", state
        assert state["input_sha256"] == expected
        assert state["result"]["ai_calls"] == 0
        assert [item["value"] for item in state["result"]["evidence"]] == [expected, expected]

        ticket = call("/api/prepare", {"run_id": run_id})["ticket"]
        approved = call("/api/approve", {
            "run_id": run_id,
            "ticket": ticket,
            "confirmed": True,
        })
        assert approved["status"] == "PASS"

    def ARCHIVE_REDACTED_04(*args, **kwargs):
        pytest.fail("Restart must use durable evidence, never rerun the external workflow")

    monkeypatch.setattr("nexus.host.launch_confined", ARCHIVE_REDACTED_04)
    restored = Host(tmp_path)
    with http(restored) as call:
        state = call("/api/runs/" + run_id)
        assert state["status"] == "PASS"
        assert state["input_sha256"] == expected
        assert state["result"]["ai_calls"] == 0

    assert (tmp_path / "runs" / run_id / "input.bin").read_bytes() == raw
    assert (tmp_path / "canonical" / run_id / "approval.json").is_file()
