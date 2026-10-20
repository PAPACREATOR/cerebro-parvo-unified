"""Real process probes for startup ownership; disposable data only."""
import json
import os
import subprocess
import sys
import time
import threading
from pathlib import Path
from contextlib import contextmanager
from types import SimpleNamespace
from urllib.request import urlopen

import pytest

from nexus.app import application
from nexus.contracts import Blocked
from nexus.instance import data_directory_lock
from nexus.store import Store
from nexus.tests.test_store import request

REPO = Path(__file__).resolve().parents[2]


def test_launch_reference_never_exposes_truncated_url(tmp_path, monkeypatch):
    import nexus.app as app
    import nexus.store as storage
    target = tmp_path / "launch-url.txt"
    previous = "http://127.0.0.1:1234/#session=previous"
    expected = "http://127.0.0.1:4321/#session=synthetic"
    target.write_text(previous, encoding="utf-8")
    observed = []
    real_open, real_replace = Path.open, storage._replace_durable

    def observe_open(path, mode="r", *args, **kwargs):
        stream = real_open(path, mode, *args, **kwargs)
        if path == target and "w" in mode:
            observed.append(target.read_text("utf-8"))
        return stream

    def observe_replace(source, destination):
        if Path(destination) == target:
            observed.append(target.read_text("utf-8"))
            assert Path(source).read_text("utf-8") == expected
        result = real_replace(source, destination)
        if Path(destination) == target:
            observed.append(target.read_text("utf-8"))
        return result

    @contextmanager
    def fake_application(*_):
        yield SimpleNamespace(store=SimpleNamespace(root=tmp_path), session="synthetic"), SimpleNamespace(
            server_port=4321, serve_forever=lambda: None)

    monkeypatch.setattr(Path, "open", observe_open)
    monkeypatch.setattr(storage, "_replace_durable", observe_replace)
    monkeypatch.setattr(app, "application", fake_application)
    monkeypatch.setattr(sys, "argv", ["nexus", "--no-browser"])
    assert app.main() == 0
    assert observed and all(value in (previous, expected) for value in observed)
    assert observed == [previous, expected]
    assert target.read_text("utf-8") == expected
    assert not list(tmp_path.glob(".pending-*"))


def test_launch_publication_failure_preserves_previous_reference(tmp_path, monkeypatch):
    import nexus.app as app
    import nexus.store as storage
    target = tmp_path / "launch-url.txt"
    target.write_bytes(b"previous-complete-reference")
    served = []

    @contextmanager
    def fake_application(*_):
        yield SimpleNamespace(store=SimpleNamespace(root=tmp_path), session="synthetic"), SimpleNamespace(
            server_port=4321, serve_forever=lambda: served.append(True))

    def fail_replace(source, destination):
        assert Path(destination) == target
        assert target.read_bytes() == b"previous-complete-reference"
        assert Path(source).read_bytes() == b"http://127.0.0.1:4321/#session=synthetic"
        raise PermissionError("synthetic publication failure")

    monkeypatch.setattr(app, "application", fake_application)
    monkeypatch.setattr(storage, "_replace_durable", fail_replace)
    monkeypatch.setattr(sys, "argv", ["nexus", "--no-browser"])
    with pytest.raises(PermissionError, match="synthetic publication"):
        app.main()
    assert target.read_bytes() == b"previous-complete-reference"
    assert not served
    assert not list(tmp_path.glob(".pending-*"))


def start_app(data):
    environment = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    return subprocess.Popen(
        [sys.executable, "-m", "nexus.app", "--data", str(data), "--no-browser"],
        cwd=REPO, env=environment, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def stop_app(process):
    if process.poll() is None:
        process.kill()
    process.communicate(timeout=10)


def wait_for_app(process, data):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise AssertionError((process.returncode, stdout, stderr))
        launch = data / "launch-url.txt"
        if launch.is_file():
            url = launch.read_text("utf-8")
            try:
                with urlopen(url.split("#")[0], timeout=.3) as response:
                    if response.status == 200:
                        return url
            except OSError:
                pass
        time.sleep(.05)
    raise AssertionError("Application did not start within 15 seconds")


def test_second_cli_does_not_recover_live_first_instance(tmp_path):
    data = tmp_path / "memoria ação com espaços"
    first = start_app(data)
    try:
        url = wait_for_app(first, data)
        # Synthetic RUNNING sentinel: observe startup recovery without a tool.
        store = Store(data)
        run = store.create(request())
        state_path = data / "runs" / run / "state.json"
        original = state_path.read_bytes()
        second = start_app(data)
        try:
            stdout, stderr = second.communicate(timeout=5)
            assert second.returncode != 0, stdout
            assert "Já existe uma Folha Nexus" in stderr.decode("utf-8")
        finally:
            stop_app(second)
        assert first.poll() is None
        assert state_path.read_bytes() == original
        assert (data / "launch-url.txt").read_text("utf-8") == url
        assert not list((data / "canonical").iterdir())
    finally:
        stop_app(first)


def test_independent_memories_can_open_together(tmp_path):
    roots = (tmp_path / "first", tmp_path / "second")
    processes = [start_app(data) for data in roots]
    try:
        urls = [wait_for_app(process, data) for process, data in zip(processes, roots)]
        assert urls[0] != urls[1]
        assert all(process.poll() is None for process in processes)
    finally:
        for process in processes:
            stop_app(process)


def test_killed_owner_releases_lock_and_restart_recovers_orphan(tmp_path):
    data = tmp_path / "data"
    first = start_app(data)
    try:
        old_url = wait_for_app(first, data)
        store = Store(data)
        run = store.create(request())
        original = (data / "runs" / run / "input.bin").read_bytes()
        lock = data / ".nexus.lock"
        assert lock.is_file()
    finally:
        stop_app(first)
    second = start_app(data)
    try:
        assert wait_for_app(second, data) != old_url
        state = json.loads((data / "runs" / run / "state.json").read_bytes())
        assert state["status"] == "FAIL"
        assert "interrompida" in state["message"]
        assert (data / "runs" / run / "input.bin").read_bytes() == original
        assert not list((data / "canonical").iterdir())
        assert lock.is_file()
    finally:
        stop_app(second)


@pytest.mark.parametrize("interrupt", [False, True])
def test_context_releases_ownership_on_normal_exit_and_error(tmp_path, interrupt):
    try:
        with application(tmp_path):
            if interrupt:
                raise RuntimeError("synthetic failure after startup")
    except RuntimeError:
        assert interrupt
    with application(tmp_path) as (host, server):
        assert host.store.root == tmp_path.resolve()
        assert server.server_port > 0


def test_host_startup_failure_releases_ownership(tmp_path, monkeypatch):
    import nexus.app as app
    original = app.Host
    def fail(_):
        raise Blocked("synthetic integrity failure")
    monkeypatch.setattr(app, "Host", fail)
    with pytest.raises(Blocked, match="synthetic integrity"):
        with application(tmp_path):
            pytest.fail("Host should not start")
    monkeypatch.setattr(app, "Host", original)
    with application(tmp_path):
        pass


def test_port_failure_releases_data_lock(tmp_path):
    with application(tmp_path / "first") as (_, first):
        with pytest.raises(OSError):
            with application(tmp_path / "second", first.server_port):
                pytest.fail("Port already belongs to another listener")
        with application(tmp_path / "second"):
            pass


def test_path_alias_does_not_bypass_ownership(tmp_path):
    alias = tmp_path / "unused" / ".."
    with data_directory_lock(tmp_path):
        with pytest.raises(Blocked, match="Já existe"):
            with data_directory_lock(alias):
                pytest.fail("Same resolved directory was opened twice")
    # The persistent coordination file is not treated as a stale active owner.
    assert (tmp_path / ".nexus.lock").is_file()
    with data_directory_lock(tmp_path):
        pass


def test_unusable_lock_path_blocks_startup(tmp_path):
    (tmp_path / ".nexus.lock").mkdir()
    with pytest.raises(Blocked, match="Não foi possível abrir"):
        with application(tmp_path):
            pytest.fail("Invalid lock path must stop startup")
    assert not (tmp_path / "runs").exists()


def test_shutdown_keeps_ownership_until_active_task_finishes(tmp_path):
    stopping, finished, released = threading.Event(), threading.Event(), threading.Event()
    errors = []
    def owner():
        try:
            with application(tmp_path) as (host, _):
                host.busy.acquire()
                def task():
                    try:
                        finished.wait(10)
                    finally:
                        host.busy.release()
                task_thread = threading.Thread(target=task)
                task_thread.start()
                stopping.set()
            released.set()
            task_thread.join(timeout=5)
        except BaseException as error:
            errors.append(error)
    worker = threading.Thread(target=owner)
    worker.start()
    try:
        assert stopping.wait(5)
        with pytest.raises(Blocked, match="Já existe"):
            with data_directory_lock(tmp_path):
                pytest.fail("Shutdown released ownership before the task finished")
        assert not released.is_set()
    finally:
        finished.set()
        worker.join(timeout=10)
    assert not worker.is_alive()
    assert not errors
    assert released.is_set()
    with data_directory_lock(tmp_path):
        pass
