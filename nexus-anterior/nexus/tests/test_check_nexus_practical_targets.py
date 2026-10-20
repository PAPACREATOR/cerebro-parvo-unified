from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "windows" / "check-nexus.ps1").read_text(encoding="utf-8")


EXPECTED = [
    "nexus/tests/test_workflows.py::test_real_redundant_workflow",
    "nexus/tests/test_windows_hash_environment.py",
    "nexus/tests/test_reverse_flow.py::test_real_windows_result_back_to_original_and_folha_after_restart",
    "nexus/tests/test_multimedia.py::test_python_reader_reads_family",
    "nexus/tests/test_lab_practical_boundaries.py",
    "nexus/tests/test_open_notebook_kernel_e2e.py",
    "nexus/tests/test_media_tools.py",
    "nexus/tests/test_media_tools_mcp.py",
    "nexus/tests/test_media_tools_checker.py",
    "nexus/tests/test_pc_sync.py",
    "nexus/tests/test_code_sync.py",
    "nexus/tests/test_code_sync_functional.py",
    "nexus/tests/test_prepare_nexus_core.py",
    "nexus/tests/test_bootstrap_nexus_local.py",
    "nexus/tests/test_external_inventory.py",
    "nexus/tests/test_external_provision_plan.py",
    "nexus/tests/test_external_inventory_functional.py",
    "nexus/tests/test_repository_syntax_audit.py",
]


def practical_block():
    start = SCRIPT.index("'practical' { @(")
    end = SCRIPT.index(") }", start)
    return SCRIPT[start:end]


def test_practical_targets_are_unique_and_complete():
    block = practical_block()
    found = re.findall(r"'(nexus/tests/[^']+)'", block)
    assert found == EXPECTED
    assert len(found) == len(set(found))


def test_practical_targets_are_comma_separated_except_last():
    block = practical_block()
    lines = [line.strip() for line in block.splitlines() if line.strip().startswith("'nexus/tests/")]
    assert len(lines) == len(EXPECTED)
    for line in lines[:-1]:
        assert line.endswith(","), line
    assert not lines[-1].endswith(",")
