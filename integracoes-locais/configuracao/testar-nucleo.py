"""Real Windows Folha verification with synthetic data and isolated memory.

This script never opens the live data directory for writing. Confirmation and
Canonical approval apply only to the one synthetic verification created here.
"""
import argparse
import base64
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def tree_hashes(root):
    """Read only a checked plain directory; never follow redirections."""
    if not root.exists():
        return {}
    require(root.is_dir() and not root.is_symlink()
            and not root.is_junction(), "A pasta de memória está redirecionada.")
    values = {}
    pending = [root]
    while pending:
        current = pending.pop()
        for path in current.iterdir():
            require(not path.is_symlink() and not path.is_junction(),
                    "A cópia de memória contém uma ligação externa.")
            if path.is_dir():
                pending.append(path)
            elif path.is_file():
                values[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return values


def run_checks(repo, test_root, memory_source):
    require(os.name == "nt", "Este teste real exige Windows e o confinamento nativo.")
    sys.path.insert(0, str(repo))
    from nexus.app import application
    import nexus.host as host_module

    runtime = test_root / "runtime"
    checks = []

    @contextmanager
    def running_server():
        with application(runtime) as (host, server):
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = "http://127.0.0.1:" + str(server.server_port)

            def call(path, payload=None):
                data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
                request = Request(base + path, data=data, headers={
                    "Content-Type": "application/json", "X-Nexus-Session": host.session,
                })
                with urlopen(request, timeout=15) as response:
                    return json.load(response)

            try:
                yield host, call
            finally:
                server.shutdown()
                thread.join(10)
                require(not thread.is_alive(), "A interface de teste não terminou.")

    def refused(call, path, value):
        try:
            call(path, value)
        except HTTPError as error:
            require(error.code == 403, "A recusa não devolveu o código esperado.")
            error.close()
            return
        raise AssertionError("Um pedido não autorizado foi aceite.")

    raw = b"Nexus Folha: verificacao real isolada; apenas dados sinteticos.\r\n"
    expected_hash = hashlib.sha256(raw).hexdigest()
    source = test_root / "fonte-sintetica.txt"
    source.write_bytes(raw)
    value = {"text": "verifica a integridade deste ficheiro", "filename": source.name,
             "attachment": base64.b64encode(raw).decode("ascii")}

    def confirmation(ticket, payload=value, confirmed=True):
        return {"ticket": ticket, "confirmed": confirmed, **payload}

    launches = []
    original_launch = host_module.launch_confined

    def recorded_launch(*args, **kwargs):
        launches.append("verify")
        return original_launch(*args, **kwargs)

    host_module.launch_confined = recorded_launch
    try:
        with running_server() as (host, call):
            interpreted = call("/api/interpret", {"text": value["text"]})
            require(interpreted["status"] == "RESOLVED" and interpreted["intent"] == "trabalhar",
                    "O pedido natural não foi reconhecido.")
            require(interpreted["execution"] == "NOT_AUTHORIZED" and call("/api/runs") == [],
                    "Interpretar executou uma ferramenta.")
            checks.append("interpretacao_sem_execucao")

            refused(call, "/api/run", {"process": "verify", **value})
            cancelled = call("/api/prepare-run", value)
            require(cancelled["process"] == "verify" and cancelled["attachment_sha256"] == expected_hash,
                    "A proposta não corresponde à fonte sintética.")
            require(call("/api/runs") == [] and launches == [], "Preparar executou uma ferramenta.")
            require(call("/api/confirm-run", confirmation(cancelled["ticket"], confirmed=False)) ==
                    {"status": "CANCELLED"}, "O cancelamento falhou.")
            refused(call, "/api/confirm-run", confirmation(cancelled["ticket"]))
            checks.append("execucao_direta_e_cancelamento_recusados")

            prepared = call("/api/prepare-run", value)
            changed = {**value, "attachment": base64.b64encode(b"alteracao posterior").decode("ascii")}
            refused(call, "/api/confirm-run", confirmation(prepared["ticket"], changed))
            refused(call, "/api/confirm-run", confirmation(prepared["ticket"]))
            require(call("/api/runs") == [] and launches == [], "Uma proposta alterada foi executada.")
            checks.append("alteracao_e_reutilizacao_recusadas")

            prepared = call("/api/prepare-run", value)
            started = call("/api/confirm-run", confirmation(prepared["ticket"]))
            run_id = started["run_id"]
            refused(call, "/api/confirm-run", confirmation(prepared["ticket"]))
            deadline = time.monotonic() + 90
            while True:
                state = call("/api/runs/" + run_id)
                if state["status"] != "RUNNING" or time.monotonic() >= deadline:
                    break
                time.sleep(.2)
            require(state["status"] == "HUMAN_REQUIRED",
                    "A execução real terminou em " + state["status"] + ": " + state.get("message", ""))
            require(state["result"]["ai_calls"] == 0 and len(launches) == 1,
                    "A verificação não foi executada exatamente uma vez sem IA.")
            require((runtime / "runs" / run_id / "input.bin").read_bytes() == raw,
                    "O original sintético mudou.")
            require((runtime / "creative" / run_id / "content.md").is_file()
                    and not (runtime / "canonical" / run_id).exists(),
                    "O resultado ultrapassou a revisão humana.")
            checks.append("verificacao_windows_real_e_revisao")

            approval = call("/api/prepare", {"run_id": run_id})
            approved = call("/api/approve", {
                "run_id": run_id, "ticket": approval["ticket"], "confirmed": True,
            })
            require(approved["status"] == "PASS", "A aprovação sintética falhou.")
            expected_content = call("/api/runs/" + run_id)["content"]
            stale_ticket = call("/api/prepare-run", value)["ticket"]
            checks.append("aprovacao_sintetica_explicitamente_confirmada")

        def ARCHIVE_REDACTED_04_launch(*args, **kwargs):
            raise AssertionError("O reinício tentou executar novamente uma ferramenta.")

        host_module.launch_confined = ARCHIVE_REDACTED_04_launch
        with running_server() as (host, call):
            restored = call("/api/runs/" + run_id)
            require(restored["status"] == "PASS" and restored["content"] == expected_content,
                    "O resultado aprovado não foi conservado no reinício.")
            refused(call, "/api/confirm-run", confirmation(stale_ticket))
            require(len(call("/api/runs")) == 1 and host.tickets == {},
                    "O reinício duplicou o pedido ou recuperou aprovações antigas.")
            require(source.read_bytes() == raw
                    and (runtime / "runs" / run_id / "input.bin").read_bytes() == raw,
                    "Um original sintético mudou no reinício.")
            checks.append("reinicio_sem_reexecucao_e_originais_intactos")

        if memory_source is not None:
            before = {name: tree_hashes(memory_source / name)
                      for name in ("runs", "creative", "canonical")}
            snapshot = test_root / "memoria-somente-copia"
            snapshot.mkdir()
            for name in before:
                directory = memory_source / name
                if directory.exists():
                    shutil.copytree(directory, snapshot / name)
            require({name: tree_hashes(snapshot / name) for name in before} == before,
                    "A cópia de memória não corresponde ao original.")
            host_module.Host(snapshot)
            require(tree_hashes(snapshot / "canonical") == before["canonical"],
                    "O arranque alterou conteúdo aprovado na cópia de memória.")
            require({name: tree_hashes(memory_source / name) for name in before} == before,
                    "A memória de origem mudou durante o teste.")
            checks.append("memoria_existente_validada_somente_em_copia")
    finally:
        host_module.launch_confined = original_launch

    return {"status": "PASS", "checks": checks, "checks_passed": len(checks),
            "real_tool_executions": len(launches), "input_sha256": expected_hash,
            "coverage": "Folha natural, proposta, cancelamento, alteracao, replay, verificacao Windows, aprovacao sintetica e reinicio.",
            "exclusions": "Nao prova geracao multimedia nem todos os adaptadores. Nenhuma aprovacao de dados pessoais."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(r"C:\Nexus\aplicacao"))
    parser.add_argument("--data-test", type=Path)
    parser.add_argument("--memory-source", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    source = args.memory_source.resolve() if args.memory_source else None
    temporary = None
    report_path = args.report
    try:
        if args.data_test is None:
            logs = Path(r"C:\Nexus\registos").resolve()
            logs.mkdir(parents=True, exist_ok=True)
            temporary = tempfile.TemporaryDirectory(prefix="folha-verificacao-", dir=logs)
            test_root = Path(temporary.name).resolve()
            if report_path is None:
                report_path = logs / "folha-teste-real.json"
        else:
            test_root = args.data_test.resolve()
            require(test_root != Path(r"C:\Nexus\dados").resolve()
                    and not test_root.is_relative_to(Path(r"C:\Nexus\dados").resolve()),
                    "A pasta de testes não pode ser a memória ativa.")
            require(not test_root.exists() or not any(test_root.iterdir()),
                    "Usa uma pasta de teste nova e vazia.")
            require(not test_root.is_symlink() and not test_root.is_junction(),
                    "A pasta de testes não pode ser uma ligação.")
            test_root.mkdir(parents=True, exist_ok=True)
            if report_path is None:
                report_path = test_root / "folha-teste-real.json"
        require(not repo.is_relative_to(test_root) and not test_root.is_relative_to(repo),
                "A pasta de testes deve ficar fora do código da aplicação.")
        if source is not None:
            require(source != test_root and not source.is_relative_to(test_root)
                    and not test_root.is_relative_to(source), "A origem e a cópia de testes sobrepõem-se.")
        result = run_checks(repo, test_root, source)
    except Exception as error:
        result = {"status": "FAIL", "error_type": type(error).__name__, "message": str(error)[:700]}
    finally:
        if temporary is not None:
            temporary.cleanup()
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if report_path is not None:
        report_path = report_path.resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(output + "\n", encoding="utf-8")
    print(output, flush=True)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
