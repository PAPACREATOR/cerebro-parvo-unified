import json
import os
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "windows" / "inventory-external-tools.ps1"
PLAN = ROOT / "windows" / "plan-external-provisioning.ps1"

pytestmark = pytest.mark.skipif(os.name != "nt", reason="PowerShell Windows functional gate")


def run_ps(script: Path, tools_root: Path):
    result = subprocess.run(
        [
            "powershell.exe", "-NoProfile", "-NonInteractive",
            "-ExecutionPolicy", "Bypass", "-File", str(script),
            "-ToolsRoot", str(tools_root),
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result


def test_inventory_executes_read_only_and_writes_one_report(tmp_path):
    tools = tmp_path / "tools"
    result = run_ps(INVENTORY, tools)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "NEXUS EXTERNAL INVENTORY = PASS" in result.stdout
    report = tools / "external-tools-inventory.json"
    assert report.is_file()
    value = json.loads(report.read_text(encoding="utf-8-sig"))
    assert value["schema"] == "nexus.external-inventory.v1"
    assert set(value["items"]) >= {
        "git", "python", "java", "libreoffice", "zotero", "ffmpeg",
        "open_notebook", "languagetool", "ace_step", "forge",
    }
    assert set(value["guarded_provisioning"]) == {
        "ace_step", "forge", "avatar_models", "isolation_account",
    }
    assert all(v == "BLOCKED_BY_POLICY" for v in value["guarded_provisioning"].values())
    assert sorted(p.name for p in tools.iterdir()) == ["external-tools-inventory.json"]


def test_plan_executes_after_inventory_without_download_or_install(tmp_path):
    tools = tmp_path / "tools"
    inventory = run_ps(INVENTORY, tools)
    assert inventory.returncode == 0, inventory.stdout + inventory.stderr
    before = (tools / "external-tools-inventory.json").read_bytes()

    result = run_ps(PLAN, tools)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "NEXUS EXTERNAL PROVISION PLAN = PASS" in result.stdout
    assert "MODE: PLAN_ONLY" in result.stdout
    assert (tools / "external-tools-inventory.json").read_bytes() == before
    plan = tools / "external-provision-plan.json"
    assert plan.is_file()
    value = json.loads(plan.read_text(encoding="utf-8-sig"))
    assert value["schema"] == "nexus.external-provision-plan.v1"
    assert value["mode"] == "PLAN_ONLY"
    assert value["execution_authorized"] is False
    by_name = {item["name"]: item for item in value["items"]}
    assert by_name["ace_step"]["pin"] == "ca1e85fe9430179831e6bc6be790c332190a3866"
    assert by_name["forge"]["pin"] == "dfdcbab685e57677014f05a3309b48cc87383167"
    assert by_name["open_notebook"]["pin"] == "315d5255af2a5132aada41c94d5c3c5dc8e837aa"
    assert sorted(p.name for p in tools.iterdir()) == [
        "external-provision-plan.json", "external-tools-inventory.json"
    ]
