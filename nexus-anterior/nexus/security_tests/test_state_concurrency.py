"""Actual HTTP snapshot readers concurrent with durable Windows state replacement."""
import threading
from concurrent.futures import ThreadPoolExecutor

from nexus.host import Host
from nexus.tests.test_store import request


def test_state_and_http_listing_readers_do_not_break_atomic_updates(tmp_path):
    host = Host(tmp_path)
    run = host.store.create(request())
    barrier = threading.Barrier(5)
    def write():
        barrier.wait()
        for i in range(500):
            host.store.update(run, synthetic_counter=i)
    def read():
        barrier.wait()
        for _ in range(1000):
            state = host.store.state(run)
            assert state["run_id"] == run and state["status"] == "RUNNING"
            listing = host.list_runs(host.session)
            assert len(listing) == 1 and listing[0]["input_sha256"] == state["input_sha256"]
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(write), *(pool.submit(read) for _ in range(4))]
        for future in futures:
            future.result(timeout=60)
    assert host.store.state(run)["synthetic_counter"] == 499
    assert not host.store.path("canonical", run).exists()
