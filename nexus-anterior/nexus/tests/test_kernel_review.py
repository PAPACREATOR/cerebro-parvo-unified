"""Review findings reproduced before fixes; synthetic data only."""
import json
import pytest
from nexus.contracts import Blocked, strict_json
from nexus.host import Host, verify_integrity
from nexus.store import Store
from nexus.tests.test_store import request, result


@pytest.mark.parametrize("raw", ['{"n":1e309}', '{"n":-1e309}'])
def test_overflow_number_rejected(raw):
    with pytest.raises(Blocked): strict_json(raw)


def test_empty_manifest_rejected(tmp_path, monkeypatch):
    import nexus.host as module
    (tmp_path / "integrity.json").write_text("{}")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    with pytest.raises(Blocked): verify_integrity()


def test_changed_original_rejected(tmp_path):
    store = Store(tmp_path); run = store.create(request())
    (store.path("runs", run) / "input.bin").write_bytes(b"changed")
    with pytest.raises(Blocked): store.accept(run, result(), {})


def test_cognitive_pass_cannot_enter_as_verified(tmp_path):
    store = Store(tmp_path); run = store.create({**request(), "process": "interpret"})
    output = result(); output["ai_calls"] = 1
    with pytest.raises(Blocked): store.accept(run, output, {})


def test_cleanup_error_does_not_keep_host_busy(tmp_path, monkeypatch):
    from pathlib import Path
    host = Host(tmp_path)
    run = host.store.create({**request(), "process": "interpret"})
    original = Path.unlink
    def fail(path, *args, **kwargs):
        if path.name == "open-notebook.json": raise PermissionError("synthetic locked file")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, "unlink", fail)
    host.busy.acquire()
    try: host._run(run)
    except PermissionError: pass
    assert not host.busy.locked()
