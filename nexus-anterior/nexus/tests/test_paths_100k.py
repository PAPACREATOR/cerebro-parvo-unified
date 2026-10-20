"""100,000 deterministic path and traversal cases.

Focus: Store run paths, Windows filename rejection rules and task-root containment.
No external tools are executed.
"""
from __future__ import annotations

import re
from pathlib import Path, PureWindowsPath

import pytest

from nexus.contracts import Blocked
from nexus.store import Store


CASES = 100_000
HEX32 = re.compile(r"^[0-9a-f]{32}$")


def test_100000_store_paths_stay_inside_area(tmp_path):
    store = Store(tmp_path / "data")
    checked = 0
    for i in range(CASES):
        run_id = f"{i:032x}"[-32:]
        assert HEX32.fullmatch(run_id)
        for area in ("runs", "creative", "canonical"):
            target = store.path(area, run_id)
            assert target.parent == (store.root / area)
            assert target.name == run_id
            assert target.resolve().is_relative_to((store.root / area).resolve())
        checked += 1
    assert checked == CASES


def test_100000_traversal_and_bad_run_ids_fail_closed(tmp_path):
    store = Store(tmp_path / "data")
    attacks = (
        "../canonical",
        "..\\canonical",
        "a" * 31,
        "a" * 33,
        "A" * 32,
        "g" * 32,
        "0" * 31 + "/",
        "0" * 31 + "\\",
        "." * 32,
        "%2e%2e" * 6 + "aa",
    )
    checked = 0
    for i in range(CASES):
        attack = attacks[(i * 17 + 3) % len(attacks)]
        area = ("runs", "creative", "canonical")[i % 3]
        with pytest.raises(Blocked):
            store.path(area, attack)
        with pytest.raises(Blocked):
            store.path("../" + area, f"{i:032x}"[-32:])
        checked += 1
    assert checked == CASES


def test_windows_path_shapes_do_not_alias_runtime_roots():
    roots = (
        PureWindowsPath(r"C:\Nexus\instalacao"),
        PureWindowsPath(r"C:\Nexus-Tools"),
    )
    assert roots[0] != roots[1]
    assert roots[0].drive == roots[1].drive == "C:"
    assert "Nexus-Tools" not in roots[0].parts
    assert "instalacao" not in roots[1].parts
