"""Transport equivalence: adapters and native boundaries remain real.

OpenNotebook responses and Java/Writer CLI peers are deterministic fixtures,
not claims of a model, LanguageTool installation, or physical PC validation.
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

import pytest

from nexus.adapters.runner import PROCESS_TO_TOOL, process_fingerprint
from nexus.contracts import Blocked, ROOT, validate
from nexus.adapters import runner as direct

SOURCE = "Lisboa recebeu 12 caixas."
PDF = b"%PDF-1.4\n% deterministic CLI fixture\n%%EOF\n"


@pytest.fixture(scope="module")
def cli_peers(tmp_path_factory):
    root = tmp_path_factory.mktemp("transport-cli-peers")
    # A real PE process exercises inherited token/Job and stdio. Only the
    # external tool's semantic output is substituted in this transport proof.
    definition = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc, char **argv) {
  const char *base = strrchr(argv[0], '\\');
  if (getenv("OPENAI_API_KEY")) return 90;
  if (getchar() != EOF) return 94;
  if (strcmp(base ? base + 1 : argv[0], "java.exe") == 0) {
    printf("{\"software\":{\"name\":\"LanguageTool\",\"version\":\"fixture\"},\"language\":{\"name\":\"Portuguese\",\"code\":\"pt-PT\"},\"matches\":[],\"warnings\":{\"incompleteResults\":false}}");
  } else {
    int i; char path[32768]; FILE *pdf = NULL;
    for (i=1; i+1<argc; i++) if (!strcmp(argv[i], "--outdir")) {
      if (snprintf(path, sizeof(path), "%s/resultado.pdf", argv[i+1]) >= sizeof(path)) return 91;
      pdf = fopen(path, "wb"); break;
    }
    if (!pdf) return 92;
    fputs("%PDF-1.4\n% deterministic CLI fixture\n%%EOF\n", pdf);
    if (fclose(pdf)) return 93;
  }
  return 0;
}
'''
    (root / "peer.c").write_text(definition, encoding="utf-8")
    vswhere = Path(os.environ["ProgramFiles(x86)"]) / "Microsoft Visual Studio/Installer/vswhere.exe"
    found = subprocess.run([str(vswhere), "-latest", "-products", "*", "-requires",
                            "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath"],
                           capture_output=True, text=True, timeout=15)
    assert found.returncode == 0 and found.stdout.strip(), "Native CLI fixture compiler NOT RUN"
    vcvars = Path(found.stdout.strip()) / "VC/Auxiliary/Build/vcvars64.bat"
    (root / "build.cmd").write_text('@echo off\ncall "' + str(vcvars) + '"\nif errorlevel 1 exit /b 1\ncl /nologo /MT peer.c /Fe:java.exe\n', encoding="utf-8")
    built = subprocess.run(["cmd.exe", "/d", "/c", str(root / "build.cmd")],
                           cwd=root, capture_output=True, timeout=60)
    assert built.returncode == 0, built.stderr.decode(errors="replace")
    office = root / "LibreOffice/program"
    office.mkdir(parents=True)
    (office / "soffice.com").write_bytes((root / "java.exe").read_bytes())
    (root / "languagetool-commandline.jar").write_bytes(b"fixture, never loaded by a JVM")
    return root


def prepare(work, process, tools):
    source = work / "input.bin"
    text = "Consulta: imprensa portuguesa" if process == "web" else SOURCE
    if process == "music":
        text = "Tema: memória\nLetra: Volto à rua onde cresci.\nEstilo: folk português"
    raw = text.encode("utf-8")
    if process in {"convert_pdf", "book"}:
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            for name, value in [("mimetype", "application/vnd.oasis.opendocument.text"),
                                ("content.xml", '<document xmlns="http://example.org">Ensaio</document>')]:
                archive.writestr(zipfile.ZipInfo(name, (2026, 10, 8, 0, 0, 0)), value)
        raw = stream.getvalue()
    source.write_bytes(raw)
    if process == "interpret":
        (work / "open-notebook-response.json").write_text(json.dumps({
            "output": json.dumps({"title": "Entrega", "summary": SOURCE, "quotes": [SOURCE]}),
            "model_id": "model:fixture", "transformation_id": "transformation:fixture"}), encoding="utf-8")
    elif process in {"video", "podcast", "visual_podcast"}:
        (work / "product-plan-response.json").write_text(json.dumps({
            "output": json.dumps({"title": "Entrega", "body": SOURCE, "steps": ["Rever fonte", "Rever plano"], "quotes": [SOURCE]}),
            "model_id": "model:fixture", "transformation_id": "transformation:fixture"}), encoding="utf-8")
    elif process == "proofread":
        (work / "languagetool.json").write_text(json.dumps({
            "java": str(tools / "java.exe"), "jar": str(tools / "languagetool-commandline.jar")}), encoding="utf-8")
    elif process in {"convert_pdf", "book"}:
        (work / "libreoffice.json").write_text(json.dumps({"executable": str(tools / "LibreOffice/program/soffice.com")}), encoding="utf-8")
    return source


def job_process_count(worker):
    import ctypes as C
    class Accounting(C.Structure):
        _fields_ = [("user", C.c_int64), ("kernel", C.c_int64),
                    ("period_user", C.c_int64), ("period_kernel", C.c_int64),
                    ("faults", C.c_ulong), ("total", C.c_ulong),
                    ("active", C.c_ulong), ("terminated", C.c_ulong)]
    query = C.WinDLL("kernel32", use_last_error=True).QueryInformationJobObject
    query.argtypes = [C.c_void_p, C.c_int, C.c_void_p, C.c_ulong, C.c_void_p]
    query.restype = C.c_int
    info = Accounting()
    assert query(worker.job, 1, C.byref(info), C.sizeof(info), None), C.get_last_error()
    return info.total


@pytest.mark.skipif(os.name != "nt", reason="A/B native Windows execution NOT RUN on this OS")
@pytest.mark.parametrize("process", sorted(PROCESS_TO_TOOL))
def test_all_internal_capabilities_across_real_native_mcp_and_direct(tmp_path, monkeypatch, cli_peers, process):
    from nexus.windows_sandbox import launch_confined, task_environment
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-host-only-secret")
    denied = tmp_path / "store"
    denied.mkdir()
    marker = denied / "canonical"
    marker.write_bytes(b"human-owned")
    results, inputs, counts = [], [], []
    pinned = process_fingerprint(process)
    for name, script in [("A", ROOT / "tests/_mcp_baseline.py"),
                         ("B", ROOT / "adapters/runner.py")]:
        work = tmp_path / (".nexus-task-" + name) / "runs" / ("a" * 32)
        work.mkdir(parents=True)
        source = prepare(work, process, cli_peers)
        raw = source.read_bytes()
        inputs.append(raw)
        with launch_confined([sys.executable, "-I", str(script), process, str(source)],
                             cwd=work, env=task_environment(work),
                             read_roots=(ROOT, sys.prefix, sys.base_prefix, work.parent.parent, cli_peers),
                             deny_roots=(denied,)) as worker:
            stdout, stderr = worker.communicate(timeout=150 if process in {"interpret", "video", "podcast", "visual_podcast"} else 75)
            assert worker.returncode == 0, name + "/" + process + ":\n" + stderr.decode(errors="replace")
            counts.append(job_process_count(worker))
        result = validate("result", json.loads(stdout)["result"])
        assert source.read_bytes() == raw
        assert marker.read_bytes() == b"human-owned"
        assert result["ai_calls"] == int(process in {"interpret", "video", "podcast", "visual_podcast"})
        if process in {"book", "convert_pdf"}:
            assert (work / "resultado.pdf").read_bytes() == PDF
            assert result["artifact"]["sha256"] == hashlib.sha256(PDF).hexdigest()
        else:
            assert "artifact" not in result
        results.append(result)
    assert results[0] == results[1]
    assert inputs[0] == inputs[1]
    assert counts[0] > counts[1] >= 1, counts
    print(process + " native Job processes A/B: " + repr(counts))
    assert process_fingerprint(process) == pinned


@pytest.mark.parametrize("process", sorted(PROCESS_TO_TOOL))
def test_direct_dispatch_has_same_fixed_policy_and_controlled_exceptions(tmp_path, monkeypatch, process):
    work = tmp_path / "runs" / ("a" * 32)
    work.mkdir(parents=True)
    source = work / "input.bin"
    source.write_bytes(b"original")
    monkeypatch.setattr(direct, "os", type("Platform", (), {"name": "posix"}))
    called = []
    def failing(selected, path):
        called.append((selected, path.read_bytes()))
        raise RuntimeError("synthetic adapter exception")
    monkeypatch.setattr(direct, "_dispatch", failing)
    with pytest.raises(Blocked, match="controlada"):
        direct.execute(process, source)
    assert called == [(process, b"original")]


@pytest.mark.parametrize("value", [None, [], {"ai_calls": 0}, float("nan"), "{invalid-json"])
def test_direct_rejects_malformed_results(tmp_path, monkeypatch, value):
    source = tmp_path / "runs" / ("a" * 32) / "input.bin"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"original")
    monkeypatch.setattr(direct, "os", type("Platform", (), {"name": "posix"}))
    monkeypatch.setattr(direct, "_dispatch", lambda *_: value)
    with pytest.raises(Blocked):
        direct.execute("web", source)


def test_schema_valid_output_still_respects_independent_mcp_byte_limit(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from nexus.mcp_client import _payload_from_result
    source = tmp_path / "runs" / ("a" * 32) / "input.bin"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"original")
    payload = {"status": "UNKNOWN", "outcome": "candidate", "title": "x", "markdown": "x",
               "ai_calls": 0, "evidence": [{"capability": "x", "status": "UNKNOWN", "value": "á" * 100000}] * 6}
    validate("result", payload)
    with pytest.raises(Blocked, match="limite"):
        _payload_from_result(SimpleNamespace(structuredContent=payload))
    monkeypatch.setattr(direct, "os", type("Platform", (), {"name": "posix"}))
    monkeypatch.setattr(direct, "_dispatch", lambda *_: payload)
    with pytest.raises(Blocked, match="limite"):
        direct.execute("web", source)


@pytest.mark.parametrize("process", ["shell", "approve", "canonical", "unknown"])
def test_direct_cannot_choose_a_tool_outside_policy(tmp_path, process):
    with pytest.raises(Blocked, match="indisponível"):
        direct.execute(process, tmp_path / "input.bin")


def test_direct_rejects_traversal_and_redirected_input(tmp_path, monkeypatch):
    monkeypatch.setattr(direct, "os", type("Platform", (), {"name": "posix"}))
    called = []
    monkeypatch.setattr(direct, "_dispatch", lambda *_: called.append(True))
    target = tmp_path / "outside"
    target.write_bytes(b"protected")
    source = tmp_path / "runs" / ("a" * 32) / "input.bin"
    source.parent.mkdir(parents=True)
    try:
        source.symlink_to(target)
    except OSError:
        # Windows directory junctions are separately covered by the native gate.
        pass
    for path in [Path("../input.bin"), target, source]:
        with pytest.raises(Blocked):
            direct.execute("verify", path)
    assert not called


@pytest.mark.skipif(os.name != "nt", reason="Full native Host capability path NOT RUN on this OS")
@pytest.mark.parametrize("process", sorted(PROCESS_TO_TOOL))
def test_direct_product_capability_is_pinned_then_human_approved_without_restart_replay(tmp_path, monkeypatch, cli_peers, process):
    import base64
    import time
    from nexus.host import Host
    from nexus.tests.test_reverse_flow import http
    from nexus import host as host_module
    data = tmp_path / "data"
    data.mkdir()
    raw = prepare(data, process, cli_peers).read_bytes()
    config = {"base_url": "http://127.0.0.1:5055", "password": "ARCHIVE_REDACTED_03",
              "model_id": "model:fixture", "transformation_id": "transformation:fixture"}
    brokers = []
    if process in {"interpret", "video", "podcast", "visual_podcast"}:
        name = "open-notebook.json" if process == "interpret" else "open-notebook-product.json"
        (data / name).write_text(json.dumps(config), encoding="utf-8")
        snapshot = data / ("open-notebook-response.json" if process == "interpret" else "product-plan-response.json")
        def broker(*args):
            assert args[-1] == config
            brokers.append(process)
            return json.loads(snapshot.read_text("utf-8"))
        target = "nexus.adapters.notebook.fetch_output" if process == "interpret" else "nexus.adapters.product_routes.fetch_plan"
        monkeypatch.setattr(target, broker)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-parent-only-secret")
    launches = []
    original_launch = host_module.launch_confined
    def launch(command, **kwargs):
        launches.append((command, kwargs))
        assert data.resolve() in kwargs["deny_roots"]
        assert "OPENAI_API_KEY" not in kwargs["env"]
        assert config["password"] not in kwargs["env"].values()
        return original_launch(command, **kwargs)
    monkeypatch.setattr(host_module, "launch_confined", launch)
    host = Host(data)
    if process in {"book", "convert_pdf"}:
        # Intentional missing-Sandy negative gate: these old CLI peers prove
        # transport equivalence only, NOT a trusted Writer LPAC installation.
        # The separate real-Windows test_native_writer_route_real.py proves
        # positive end-to-end Writer, PDF, human approval and restart safety.
        # Never allow a fake soffice.com to bypass the new pinned Sandy gate.
        with http(host, allow_direct_run=True) as call:
            run = call("/api/run", {"process": process, "text": "",
                                   "filename": "source.bin",
                                   "attachment": base64.b64encode(raw).decode("ascii")})["run_id"]
            deadline = time.monotonic() + 20
            state = call("/api/runs/" + run)
            while state["status"] == "RUNNING" and time.monotonic() < deadline:
                time.sleep(0.05)
                state = call("/api/runs/" + run)
            assert state["status"] == "BLOCKED", state
            assert "Configuração da ferramenta inválida." in state["message"]
            assert (data / "runs" / run / "input.bin").read_bytes() == raw
            assert not (data / "canonical" / run).exists()
            assert not (data / "creative" / run).exists()
            from urllib.error import HTTPError
            with pytest.raises(HTTPError) as refused:
                call("/api/prepare", {"run_id": run})
            assert refused.value.code == 403
        assert launches == []
        assert brokers == []
        restored = Host(data)
        assert restored.store.state(run)["status"] == "BLOCKED"
        assert not (data / "canonical" / run).exists()
        return
    # Diagnostic A/B only; product default remains fail-closed.
    with http(host, allow_direct_run=True) as call:
        run = call("/api/run", {"process": process, "text": "", "filename": "source.bin",
                               "attachment": base64.b64encode(raw).decode("ascii")})["run_id"]
        pinned = host.store.state(run)["process_sha256"]
        deadline = time.monotonic() + 60
        state = call("/api/runs/" + run)
        while state["status"] == "RUNNING" and time.monotonic() < deadline:
            time.sleep(0.05)
            state = call("/api/runs/" + run)
        if state["status"] != "HUMAN_REQUIRED":
            folder = data / "runs" / run
            diagnostics = {p.name: p.read_text("utf-8", errors="replace")[-12000:]
                           for p in folder.iterdir() if p.name in {
                               "execution.stderr.txt", "execution.stdout.json", "failure.json"}}
            pytest.fail(json.dumps({"state": state, "diagnostics": diagnostics}, ensure_ascii=False))
        assert pinned == process_fingerprint(process)
        assert (data / "runs" / run / "input.bin").read_bytes() == raw
        assert not (data / "canonical" / run).exists()
        provenance = json.loads((data / "creative" / run / "provenance.json").read_text("utf-8"))
        assert provenance["execution"]["engine"] == "nexus/python-direct"
        assert provenance["execution"]["process_sha256"] == pinned
        assert state["result"]["ai_calls"] == int(process in {"interpret", "video", "podcast", "visual_podcast"})
        ticket = call("/api/prepare", {"run_id": run})["ticket"]
        assert call("/api/approve", {"run_id": run, "ticket": ticket, "confirmed": True})["status"] == "PASS"
    assert len(launches) == 1
    assert len(brokers) == int(process in {"interpret", "video", "podcast", "visual_podcast"})
    package = {p.name: p.read_bytes() for p in (data / "canonical" / run).iterdir()}
    def no_replay(*args, **kwargs):
        pytest.fail("Committed recovery replayed a tool or broker")
    monkeypatch.setattr(host_module, "launch_confined", no_replay)
    monkeypatch.setattr("nexus.adapters.notebook.fetch_output", no_replay)
    monkeypatch.setattr("nexus.adapters.product_routes.fetch_plan", no_replay)
    restored = Host(data)
    restored.store.check_commit(restored.store.state(run))
    assert restored.store.state(run)["status"] == "PASS"
    assert {p.name: p.read_bytes() for p in (data / "canonical" / run).iterdir()} == package
