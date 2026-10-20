"""Minimal local Host: contracts, deterministic Python delegation, gate and presentation."""
import getpass
import hmac
import json
import os
import secrets
import subprocess
import sys
import threading
import tempfile
import time
import uuid
from pathlib import Path

from nexus.contracts import ROOT, Blocked, strict_json, validate
from nexus.store import Store, HumanDecision, atomic, digest
from nexus.windows_sandbox import launch_confined, task_environment


def verify_integrity():
    manifest = strict_json((ROOT / "integrity.json").read_bytes())
    required = {
        "__init__.py", "app.py", "host.py", "store.py", "contracts.py", "approval_binding.py", "capability_router.py", "instance.py",
        "windows_sandbox.py", "native_mcp.py", "frontdoor.py", "frontdoor_rules.json", "schemas/frontdoor_rules.json", "adapters/runner.py", "mcp_client.py", "mcp_tools_server.py", "adapters/verify_direct.py", "adapters/tools.py", "adapters/notebook.py",
        "adapters/languagetool.py", "adapters/office.py", "adapters/writer_sandy.py",
        "adapters/vendor/sandy/libreoffice-demo.py", "adapters/vendor/sandy/libreoffice.toml",
        "adapters/vendor/sandy/LICENSE", "adapters/media_tools.py", "adapters/product_routes.py",
        "laws/CONSTITUTION.md", "laws/policy.json",
        "schemas/request.json", "schemas/result.json", "schemas/cognitive.json", "schemas/languagetool.json",
        "ui/index.html", "ui/app.js", "ui/style.css",
        "adapters/constitutional.py", "schemas/multimedia.json",
        "families/multimedia/som.md", "families/multimedia/imagem.md",
    }
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise Blocked("Manifesto de integridade ausente ou incompleto.")
    for relative, expected in manifest.items():
        target = ROOT / relative
        if target.is_symlink() or digest(target.read_bytes()) != expected:
            raise Blocked("Um contrato ou processo mudou. É necessária revisão antes de executar.")
    return manifest


def process_environment(run_directory):
    return task_environment(run_directory)


class Host:
    def __init__(self, data_root):
        verify_integrity()
        self.store = Store(data_root)
        self.session = secrets.token_urlsafe(32)
        self.tickets = {}
        self.busy = threading.Lock()
        self.actor = getpass.getuser()

    def authorize(self, session):
        if type(session) is not str or not session.isascii() or not hmac.compare_digest(session, self.session):
            raise Blocked("Abre a Folha através do lançador local.")

    def start(self, request, session):
        self.authorize(session)
        verify_integrity()
        if not self.busy.acquire(blocking=False):
            raise Blocked("Já há um pedido a executar. Aguarda o resultado.")
        try:
            run_id = self.store.create(request)
        except Exception:
            self.busy.release()
            raise
        threading.Thread(target=self._run, args=(run_id,), daemon=True).start()
        return {"run_id": run_id}

    def _run(self, run_id):
        directory = self.store.path("runs", run_id)
        try:
            if os.name != "nt":
                raise Blocked("A execução protegida requer Windows nesta versão.")
            state = self.store.state(run_id)
            self.store.check_input(state)
            process = state["process_id"]
            # Persist BEFORE the sole external capability call. Recovery never
            # repeats notebook/model/tool execution to reconstruct a missing result.
            self.store.update(run_id, execution_phase="EXECUTING")
            from nexus.adapters.runner import prepare_task, collect_artifact
            with tempfile.TemporaryDirectory(prefix=".nexus-task-", dir=self.store.root.parent) as temporary:
                work = Path(temporary) / "runs" / run_id
                work.mkdir(parents=True)
                roots = prepare_task(process, directory / "input.bin", work, config_root=self.store.root)
                if process in ("book", "convert_pdf"):
                    # Necessary exception: Office's named pipe cannot be created
                    # in the original LPAC runner. A pinned Sandy launcher owns
                    # the Writer-only LPAC/Job; the Host remains the sole authority.
                    from nexus.adapters.writer_sandy import convert as writer_convert
                    envelope = writer_convert(process, work)
                    stdout = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
                    stderr = b""
                else:
                    command = [sys.executable, "-I", str(ROOT / "adapters/runner.py"), process, str(work / "input.bin")]
                    with launch_confined(command, cwd=work, env=process_environment(work),
                                         read_roots=roots, deny_roots=(self.store.root,)) as proc:
                        try:
                            stdout, stderr = proc.communicate(
                                timeout=150 if process in ("interpret", "video", "podcast", "visual_podcast") else 75
                            )
                        except subprocess.TimeoutExpired:
                            raise Blocked("A ferramenta excedeu o tempo permitido.") from None
                        code = proc.returncode
                    if code:
                        raise Blocked("A execução da ferramenta falhou. O pedido foi conservado.")
                    if not stdout.strip():
                        raise Blocked("A ferramenta não devolveu um resultado.")
                    envelope = strict_json(stdout)
                # All tool descendants must be dead before Host reads artefacts.
                atomic(directory / "execution.stderr.txt", stderr)
                atomic(directory / "execution.stdout.json", stdout)
                if (not isinstance(envelope, dict) or set(envelope) != {"result", "trace"}
                        or not isinstance(envelope["trace"], dict)):
                    raise Blocked("Resposta de execução inválida.")
                collect_artifact(envelope, work, directory)
            from nexus.adapters.runner import process_fingerprint
            envelope["trace"]["process_sha256"] = process_fingerprint(process)
            self.store.accept(run_id, envelope["result"], envelope["trace"])
        except Exception as error:
            self.store.update(run_id, status="BLOCKED" if isinstance(error, Blocked) else "FAIL",
                              message=str(error) if isinstance(error, Blocked) else "Não foi possível concluir. O pedido foi conservado.")
            atomic(directory / "failure.json", {"type": type(error).__name__, "message": str(error)})
        finally:
            self.busy.release()

    def list_runs(self, session):
        self.authorize(session)
        with self.store.lock:
            values = [strict_json(p.read_bytes()) for p in (self.store.root / "runs").glob("*/state.json")]
        for state in values:
            try:
                self.check_visible_result(state)
            except (Blocked, OSError, KeyError, TypeError):
                # Read-only presentation: preserve persisted records for reconciliation.
                state.update(status="BLOCKED", message="A ligação ao original precisa de reconciliação. Conteúdo conservado.")
        return sorted(values, key=lambda item: item["created_at"], reverse=True)

    def check_visible_result(self, state):
        if state["status"] == "PASS":
            self.store.check_commit(state)
        elif state["status"] == "HUMAN_REQUIRED":
            self.store.check_candidate(state)

    def detail(self, run_id, session):
        self.authorize(session)
        state = self.store.state(run_id)
        candidate = self.store.path("creative", run_id)
        self.check_visible_result(state)
        if (candidate / "result.json").exists():
            result = strict_json((candidate / "result.json").read_bytes())
            state["result"] = result
            state["content"] = (candidate / "content.md").read_text("utf-8")
        return state

    def artifact(self, run_id, session):
        self.authorize(session)
        state = self.store.state(run_id)
        data = self.store.verify_artifact(state, self.store.path("creative", run_id))
        if data is None:
            raise Blocked("Este resultado não tem PDF.")
        return data

    def prepare_approval(self, run_id, session):
        self.authorize(session)
        with self.store.lock:
            state = self.store.state(run_id)
            if state["status"] != "HUMAN_REQUIRED":
                raise Blocked("Não há candidato pendente de decisão.")
            self.store.check_candidate(state)
            self.store.verify_artifact(state, self.store.path("creative", run_id))
            content = (self.store.path("creative", run_id) / "content.md").read_bytes()
            if digest(content) != state["candidate_sha256"]:
                raise Blocked("O conteúdo mudou. A aprovação foi bloqueada.")
            # Keep only live tickets for other candidates; refreshing revokes the old review.
            current_time = time.monotonic()
            self.tickets = {key: value for key, value in self.tickets.items()
                            if value[2] > current_time and value[0] != run_id}
            ticket = secrets.token_urlsafe(32)
            self.tickets[ticket] = (run_id, digest(content), time.monotonic() + 300)
            return {"ticket": ticket, "content": content.decode("utf-8")}

    def approve(self, run_id, ticket, confirmed, session):
        self.authorize(session)
        with self.store.lock:
            binding = self.tickets.pop(ticket, None) if isinstance(ticket, str) else None
            if confirmed is not True or not binding or binding[0] != run_id or binding[2] < time.monotonic():
                raise Blocked("BLOCK: é necessária confirmação humana explícita.")
            decision = HumanDecision(uuid.uuid4().hex, self.actor, run_id, binding[1], "APPROVE")
            return self.store.promote(run_id, decision)
