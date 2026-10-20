"""Read-only FTS5 Folha integration: real Host, Store and WikiBridge lab.

No live tools, synthetic Store fixtures only. Host and Store files are not modified.
"""
import uuid
from urllib.error import HTTPError

import pytest

from nexus.host import Host
from nexus.store import HumanDecision
from nexus.tests.test_reverse_flow import http
from nexus.tests.test_store import request, result, execution_trace


def stored(host, text, *, approved=False):
    store = host.store
    run = store.create(request())
    data = result()
    data["markdown"] = text
    store.accept(run, data, execution_trace(store, run, synthetic=True))
    if approved:
        decision = HumanDecision(uuid.uuid4().hex, "test-human", run,
                                 store.state(run)["candidate_sha256"], "APPROVE")
        store.promote(run, decision)
    return run


def search(call, query="nexusterm", include_creative=False, limit=8, *, session=None):
    return call("/api/search", {"query": query, "include_creative": include_creative,
                                "limit": limit}, session=session)


def test_canonical_only_and_explicit_creative_gate(tmp_path):
    host = Host(tmp_path / "memory")
    approved = stored(host, "nexusterm resposta consolidada", approved=True)
    draft = stored(host, "nexusterm hipótese ainda em Creative")
    with http(host) as call:
        canonical = search(call)
        assert canonical["scope"] == "canonical"
        assert [r["run_id"] for r in canonical["results"]] == [approved]
        assert canonical["results"][0]["authority"] == "canonical"
        assert "resposta consolidada" in canonical["results"][0]["snippet"]
        assert len(canonical["results"][0]["content_sha256"]) == 64
        assert len(canonical["results"][0]["provenance_sha256"]) == 64
        both = search(call, include_creative=True)
        assert both["scope"] == "canonical+creative"
        assert {r["run_id"] for r in both["results"]} == {approved, draft}
        assert {r["authority"] for r in both["results"]} == {"canonical", "creative"}
        assert len(search(call, limit=1, include_creative=True)["results"]) == 1
    assert not any((tmp_path / "memory" / "runs" / approved).glob("search*"))
    assert (tmp_path / "memory-fts5-index" / "wiki.sqlite").is_file()


def test_new_store_record_rebuilds_index_and_does_not_run_tool(tmp_path):
    host = Host(tmp_path / "memory")
    with http(host) as call:
        assert search(call)["results"] == []
        run = stored(host, "nexusterm origem aprovada", approved=True)
        assert [r["run_id"] for r in search(call)["results"]] == [run]
        another = stored(host, "nexusterm material novo", approved=True)
        assert {r["run_id"] for r in search(call)["results"]} == {run, another}
        assert [r["run_id"] for r in call("/api/runs")] == [another, run] or {
            r["run_id"] for r in call("/api/runs")} == {another, run}


def test_corruption_blocks_and_does_not_reuse_stale_canonical(tmp_path):
    host = Host(tmp_path / "memory")
    approved = stored(host, "nexusterm íntegro", approved=True)
    with http(host) as call:
        assert search(call)["results"][0]["run_id"] == approved
        content = host.store.path("canonical", approved) / "content.md"
        content.write_text("nexusterm adulterado", encoding="utf-8")
        rows = search(call)["results"]
        assert rows == []
        assert call("/api/runs")[0]["status"] == "BLOCKED"
    assert content.read_text(encoding="utf-8") == "nexusterm adulterado"


@pytest.mark.parametrize("data", [
    {}, {"query": "nexusterm"},
    {"query": 123, "include_creative": False, "limit": 8},
    {"query": "x" * 201, "include_creative": False, "limit": 8},
    {"query": "", "include_creative": False, "limit": 8},
    {"query": "word\x00", "include_creative": False, "limit": 8},
    {"query": "word", "include_creative": "yes", "limit": 8},
    {"query": "word", "include_creative": False, "limit": True},
    {"query": "word", "include_creative": False, "limit": 9},
    {"query": "word", "include_creative": False, "limit": 0},
    {"query": "word", "include_creative": False, "limit": 8, "approve": True},
])
def test_invalid_search_is_refused_without_execution(tmp_path, data):
    host = Host(tmp_path / "memory")
    with http(host) as call:
        with pytest.raises(HTTPError) as error:
            call("/api/search", data)
        assert error.value.code == 403
        assert call("/api/runs") == []


def test_session_is_required_and_never_approves(tmp_path):
    host = Host(tmp_path / "memory")
    draft = stored(host, "nexusterm segredo rascunho")
    with http(host) as call:
        with pytest.raises(HTTPError) as error:
            search(call, include_creative=True, session="wrong-session")
        assert error.value.code == 403
        assert [r["run_id"] for r in search(call, include_creative=True)["results"]] == [draft]
        assert search(call)["results"] == []
    assert not host.store.path("canonical", draft).exists()
    assert host.store.state(draft)["status"] == "HUMAN_REQUIRED"


@pytest.mark.parametrize("query", ['" OR nexusterm', 'nexusterm OR sensitive', '*', "'; DROP TABLE docs;--"])
def test_fts_operators_are_data_not_authority(tmp_path, query):
    host = Host(tmp_path / "memory")
    stored(host, "nexusterm origem", approved=True)
    with http(host) as call:
        assert search(call, query=query)["results"] == []
        assert len(search(call)["results"]) == 1


def test_bidirectional_human_approval_changes_search_scope_without_new_authority(tmp_path):
    """Creative -> explicit Host review -> Canonical -> FTS5 -> authentic Store."""
    host = Host(tmp_path / "memory")
    draft = stored(host, "nexusterm conteúdo precisa de assinatura humana")
    with http(host) as call:
        # Forward: Creative is searchable only when explicitly requested.
        assert search(call)["results"] == []
        before = search(call, include_creative=True)["results"]
        assert len(before) == 1 and before[0]["run_id"] == draft
        assert before[0]["authority"] == "creative"
        assert not host.store.path("canonical", draft).exists()
        # Reverse: forged or refused approval must not promote.
        with pytest.raises(HTTPError) as refused:
            call("/api/approve", {"run_id": draft, "ticket": "forged", "confirmed": True})
        assert refused.value.code == 403
        prepared = call("/api/prepare", {"run_id": draft})
        assert "nexusterm" in prepared["content"]
        with pytest.raises(HTTPError) as declined:
            call("/api/approve", {"run_id": draft, "ticket": prepared["ticket"], "confirmed": False})
        assert declined.value.code == 403
        assert not host.store.path("canonical", draft).exists()
        assert search(call)["results"] == []
        # Explicit, fresh approval bound to current candidate SHA-256.
        approved = call("/api/prepare", {"run_id": draft})
        decided = call("/api/approve", {
            "run_id": draft, "ticket": approved["ticket"], "confirmed": True
        })
        assert decided["status"] == "PASS"
        canonical = search(call)["results"]
        assert [item["run_id"] for item in canonical] == [draft]
        assert canonical[0]["authority"] == "canonical"
        assert canonical[0]["content_sha256"] == before[0]["content_sha256"]
        assert canonical[0]["provenance_sha256"] != before[0]["provenance_sha256"]
        assert search(call, include_creative=True)["results"][0]["authority"] == "canonical"
        # Reverse verification from the FTS result back to the authoritative bytes.
        approved_file = host.store.path("canonical", draft) / "content.md"
        assert approved_file.read_text(encoding="utf-8") == prepared["content"]
        assert host.store.state(draft)["status"] == "PASS"
        with pytest.raises(HTTPError) as replay:
            call("/api/approve", {"run_id": draft, "ticket": approved["ticket"], "confirmed": True})
        assert replay.value.code == 403
