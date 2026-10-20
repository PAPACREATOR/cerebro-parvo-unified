"""10,000 distinct app-boundary inputs; separate from real Windows I/O attacks."""
import pytest

from nexus.contracts import Blocked, validate
from nexus.host import Host
from nexus.tests.test_store import request, result

CASES_PER_FAMILY = 2500


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_2500_forged_sessions_never_touch_data(tmp_path):
    host = Host(tmp_path)
    before = snapshot(tmp_path)
    for i in range(CASES_PER_FAMILY):
        prefix = ('forged-', 'ação-', '\x00', '\ud800', '\n')[i % 5]
        with pytest.raises(Blocked):
            host.start(request(), prefix + str(i))
    assert snapshot(tmp_path) == before
    assert not host.busy.locked()


def test_2500_fake_human_tickets_cannot_promote(tmp_path):
    host = Host(tmp_path)
    before = snapshot(tmp_path)
    for i in range(CASES_PER_FAMILY):
        with pytest.raises(Blocked):
            host.approve(f'{i:032x}', 'tool-claims-human-approved-' + str(i), True, host.session)
    assert not host.tickets
    assert snapshot(tmp_path) == before


def test_2500_authority_fields_in_results_are_rejected():
    for i in range(CASES_PER_FAMILY):
        field = ('authority','approved','canonical_path','execute','human_decision')[i % 5]
        with pytest.raises(Blocked):
            validate('result', {**result(), field: {'claim': i, 'approved': True}})


def test_2500_unregistered_processes_cannot_create_runs(tmp_path):
    host = Host(tmp_path)
    before = snapshot(tmp_path)
    for i in range(CASES_PER_FAMILY):
        prefix = ('../','powershell:','cmd /c ','file://','approved_by_human:')[i % 5]
        with pytest.raises(Blocked):
            host.store.create({**request(), 'process': prefix + str(i)})
    assert snapshot(tmp_path) == before
