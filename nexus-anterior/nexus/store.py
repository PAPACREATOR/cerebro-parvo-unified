"""Host storage and explicit human gate. No automatic promotion API."""
import base64
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from nexus.approval_binding import HumanDecision, promotion_allowed
from nexus.contracts import Blocked, ROOT, load_policy, strict_json, validate


CANDIDATE_PROCESSES = {
    "interpret", "proofread", "convert_pdf",
    "video", "podcast", "visual_podcast", "book", "music", "web",
}
AI_PROCESSES = {"interpret", "video", "podcast", "visual_podcast"}
NO_AI_PROCESSES = {"verify", "proofread", "convert_pdf", "book", "music", "web"}
PDF_PROCESSES = {"convert_pdf", "book"}


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _fsync_parent(path):
    parent = Path(path).parent
    fd = os.open(parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _replace_durable(source, target):
    source = str(source)
    target = str(target)
    if os.name == "nt":
        import ctypes
        move = ctypes.WinDLL("kernel32", use_last_error=True).MoveFileExW
        move.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
        move.restype = ctypes.c_int
        MOVEFILE_REPLACE_EXISTING = 0x1
        MOVEFILE_WRITE_THROUGH = 0x8
        if not move(source, target, MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH):
            raise ctypes.WinError(ctypes.get_last_error())
        return
    os.replace(source, target)
    _fsync_parent(target)


def atomic(path, data):
    path = Path(path)
    raw = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".pending-")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        _replace_durable(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class Store:
    def __init__(self, path):
        self.root = Path(path).resolve()
        self.policy = load_policy()
        self.lock = threading.RLock()
        for directory in ("runs", "creative", "canonical"):
            target = self.root / directory
            if target.is_symlink() or target.is_junction():
                raise Blocked("Diretório de dados redirecionado.")
            target.mkdir(parents=True, exist_ok=True)
        runs_root = self.root / "runs"
        for directory in runs_root.iterdir():
            if not directory.is_dir() or not re.fullmatch(r"[0-9a-f]{32}", directory.name):
                continue
            if directory.is_symlink() or directory.is_junction():
                raise Blocked("Pedido interrompido redirecionado.")
            state_path = directory / "state.json"
            if state_path.is_symlink() or state_path.is_junction():
                raise Blocked("Estado autoritativo redirecionado.")
            if state_path.exists():
                continue
            input_path = directory / "input.bin"
            input_sha256 = None
            if not input_path.is_symlink() and not input_path.is_junction() and input_path.is_file():
                input_sha256 = digest(input_path.read_bytes())
            created_at = datetime.fromtimestamp(directory.stat().st_mtime, timezone.utc).isoformat()
            recovered = {
                "run_id": directory.name,
                "status": "BLOCKED",
                "commit_status": "RECOVERY_REQUIRED",
                "execution_phase": "PREPARED",
                "created_at": created_at,
                "updated_at": now(),
                "title": "Pedido interrompido",
                "message": "A receção foi interrompida antes do estado autoritativo. Conteúdo conservado para reconciliação.",
            }
            if input_sha256 is not None:
                recovered["input_sha256"] = input_sha256
            atomic(state_path, recovered)
        for item in runs_root.glob("*/state.json"):
            if item.is_symlink() or item.is_junction():
                raise Blocked("Estado autoritativo redirecionado.")
            state = strict_json(item.read_bytes())
            final = self.path("canonical", state["run_id"])
            if final.exists() or state["status"] == "PASS":
                try:
                    self.check_commit(state)
                    state.update(status="PASS", commit_status="COMMITTED", message="Guardado como aprovado.")
                except (OSError, ValueError, KeyError, TypeError):
                    state.update(status="BLOCKED", commit_status="RECOVERY_REQUIRED",
                                 message="A gravação aprovada precisa de reconciliação. Conteúdo conservado.")
                state["updated_at"] = now()
                atomic(item, state)
            elif state["status"] == "RUNNING":
                execution = self.path("runs", state["run_id"]) / "execution.stdout.json"
                if execution.is_symlink() or execution.is_junction():
                    state.update(status="BLOCKED", commit_status="RECOVERY_REQUIRED",
                                 message="Resultado externo redirecionado; a reconciliação foi bloqueada.",
                                 updated_at=now())
                    atomic(item, state)
                    continue
                if execution.is_file():
                    try:
                        envelope = strict_json(execution.read_bytes())
                        if not isinstance(envelope, dict) or set(envelope) != {"result", "trace"}:
                            raise Blocked("Resposta de execução inválida.")
                        if not isinstance(envelope["trace"], dict):
                            raise Blocked("Trace de execução inválido.")
                        from nexus.adapters.runner import process_fingerprint
                        expected_process = state.get("process_sha256")
                        current_process = process_fingerprint(state["process_id"])
                        if expected_process is None or current_process != expected_process:
                            raise Blocked("O processo mudou; o resultado conservado não pode ser reconciliado automaticamente.")
                        trace = dict(envelope["trace"], process_sha256=expected_process)
                        self.accept(state["run_id"], envelope["result"], trace)
                        continue
                    except (Blocked, OSError, ValueError, KeyError, TypeError):
                        state.update(status="BLOCKED",
                                     message="Resultado externo conservado; a reconciliação precisa de revisão.",
                                     updated_at=now())
                        atomic(item, state)
                else:
                    if state.get("execution_phase") == "EXECUTING":
                        state.update(status="BLOCKED", commit_status="RECOVERY_REQUIRED",
                                     message="A execução externa foi iniciada, mas não existe resultado durável. Requer reconciliação.",
                                     updated_at=now())
                    else:
                        state.update(status="FAIL", message="Execução interrompida. Podes iniciar um novo pedido.", updated_at=now())
                    atomic(item, state)

    def verify_artifact(self, state, directory):
        expected = state.get("artifact_sha256")
        if expected is None:
            return None
        from nexus.adapters.office import pdf_bytes
        raw = pdf_bytes(directory / "resultado.pdf")
        if digest(raw) != expected:
            raise Blocked("O PDF mudou; operação bloqueada.")
        return raw

    def check_commit(self, state):
        """Verify an existing approval package; never create a new human decision."""
        try:
            self._check_commit(state)
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise Blocked("O pacote aprovado precisa de reconciliação. Conteúdo conservado.") from error

    def _check_commit(self, state):
        candidate_provenance = self.check_candidate(state)
        run_id = state["run_id"]
        final = self.path("canonical", run_id)
        for name in ("content.md", "approval.json", "provenance.json"):
            if (final / name).is_symlink():
                raise Blocked("Pacote aprovado redirecionado.")
        self.verify_artifact(state, final)
        content = (final / "content.md").read_bytes()
        approval = strict_json((final / "approval.json").read_bytes())
        provenance = strict_json((final / "provenance.json").read_bytes())
        expected_provenance = dict(candidate_provenance, human_approval=approval)
        expected_provenance["output_references"] = candidate_provenance["output_references"] + [
            {"path": "canonical/" + run_id + "/content.md", "sha256": digest(content)}]
        if state.get("artifact_sha256") is not None:
            expected_provenance["output_references"].append(
                {"path": "canonical/" + run_id + "/resultado.pdf", "sha256": state["artifact_sha256"]})
        if (digest(content) != state["candidate_sha256"]
                or approval["sha256"] != digest(content)
                or approval["run_id"] != run_id
                or approval["destination"] != "canonical"
                or approval["action"] != "APPROVE"
                or not approval["approval_id"] or not approval["actor"]
                or provenance["run_id"] != run_id
                or provenance != expected_provenance
                or provenance["human_approval"] != approval
                or {"path": "canonical/" + run_id + "/content.md", "sha256": digest(content)}
                   not in provenance["output_references"]):
            raise Blocked("Pacote aprovado incoerente.")
        decision = HumanDecision(approval["approval_id"], approval["actor"], run_id, approval["sha256"], "APPROVE")
        if not promotion_allowed(decision, run_id, digest(content)):
            raise Blocked("Aprovação inválida.")

    def checked_bytes(self, area, run_id, name):
        """Only read fixed internal names, never a path supplied by provenance."""
        path = self.path(area, run_id) / name
        if path.is_symlink() or path.is_junction():
            raise Blocked("Registo de proveniência redirecionado.")
        return path.read_bytes()

    def check_input(self, state):
        run = state["run_id"]
        original = self.checked_bytes("runs", run, "input.bin")
        raw_request = self.checked_bytes("runs", run, "request.json")
        request = validate("request", strict_json(raw_request))
        expected = base64.b64decode(request["attachment"], validate=True) if request["attachment"] else request["text"].encode("utf-8")
        if (digest(original) != state["input_sha256"] or expected != original
                or request["process"] != state["process_id"]
                or (request["filename"] or "Texto escrito") != state["title"]
                or ("request_sha256" in state and digest(raw_request) != state["request_sha256"])):
            raise Blocked("O original ou o pedido mudou; proveniência bloqueada.")

    def check_candidate(self, state):
        """Walk Creative -> result -> request/original without executing tools."""
        try:
            self.check_input(state)
            run = state["run_id"]
            content = self.checked_bytes("creative", run, "content.md")
            raw_result = self.checked_bytes("creative", run, "result.json")
            raw_provenance = self.checked_bytes("creative", run, "provenance.json")
            result = validate("result", strict_json(raw_result))
            provenance = strict_json(raw_provenance)
            references = [{"path": "creative/" + run + "/content.md", "sha256": digest(content)}]
            if state.get("artifact_sha256") is not None:
                self.verify_artifact(state, self.path("creative", run))
                references.append({"path": "creative/" + run + "/resultado.pdf", "sha256": state["artifact_sha256"]})
            if (digest(content) != state["candidate_sha256"] or result["markdown"].encode("utf-8") != content
                    or result["status"] != state["result_status"] or result["outcome"] != state["outcome"]
                    or result.get("artifact", {}).get("sha256") != state.get("artifact_sha256")
                    or provenance["run_id"] != run or provenance["process_id"] != state["process_id"]
                    or provenance["process_version"] != state["process_version"]
                    or provenance["status"] != result["status"] or provenance["human_approval"] is not None
                    or provenance["input_references"] != [{"path": "runs/" + run + "/input.bin", "sha256": state["input_sha256"]}]
                    or provenance["output_references"] != references
                    or provenance["tools"] != [item["capability"] for item in result["evidence"]]
                    or ("result_sha256" in state and digest(raw_result) != state["result_sha256"])
                    or ("provenance_sha256" in state and digest(raw_provenance) != state["provenance_sha256"])):
                raise Blocked("A ligação inversa do resultado é incoerente.")
            return provenance
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise Blocked("Não foi possível verificar a ligação ao original. Conteúdo conservado.") from error

    def path(self, area, run_id):
        if area not in ("runs", "creative", "canonical") or not isinstance(run_id, str) or not re.fullmatch(r"[0-9a-f]{32}", run_id):
            raise Blocked("Referência inválida.")
        target = self.root / area / run_id
        if target.is_symlink() or target.is_junction() or not target.resolve().is_relative_to(self.root / area):
            raise Blocked("Destino inválido.")
        return target

    def state(self, run_id):
        # Python file reads on Windows can prevent os.replace while open.
        # Share the writer lock so HTTP snapshots cannot race atomic replacement.
        with self.lock:
            return strict_json((self.path("runs", run_id) / "state.json").read_bytes())

    def update(self, run_id, **fields):
        with self.lock:
            value = self.state(run_id)
            value.update(fields, updated_at=now())
            atomic(self.path("runs", run_id) / "state.json", value)
            return value

    def create(self, request):
        validate("request", request)
        try:
            content = base64.b64decode(request["attachment"], validate=True) if request["attachment"] else request["text"].encode("utf-8")
        except (ValueError, UnicodeError) as error:
            raise Blocked("Anexo inválido.") from error
        if not content or len(content) > self.policy["max_input_bytes"]:
            raise Blocked("Escreve texto ou anexa um ficheiro até 2 MB.")
        if request["process"] not in self.policy["processes"]:
            raise Blocked("Processo não autorizado.")
        name = request["filename"] or "Texto escrito"
        if any(ord(c) < 32 for c in name) or "/" in name or "\\" in name:
            raise Blocked("Nome de anexo inválido.")
        run_id = uuid.uuid4().hex
        directory = self.path("runs", run_id)
        directory.mkdir()
        atomic(directory / "input.bin", content)
        atomic(directory / "request.json", request)
        from nexus.adapters.runner import process_fingerprint
        process_sha256 = process_fingerprint(request["process"])
        atomic(directory / "state.json", {
            "run_id": run_id, "process_id": request["process"], "process_version": "1.0.0",
            "title": name, "status": "RUNNING", "created_at": now(), "updated_at": now(),
            "message": "A executar o processo.", "execution_phase": "PREPARED",
            "input_sha256": digest(content),
            "request_sha256": digest((directory / "request.json").read_bytes()),
            "process_sha256": process_sha256,
        })
        return run_id

    def accept(self, run_id, result, trace):
        validate("result", result)
        with self.lock:
            state = self.state(run_id)
            if state["status"] != "RUNNING":
                raise Blocked("A execução já terminou.")
            self.check_input(state)
            if not isinstance(trace, dict) or trace.get("process_sha256") != state.get("process_sha256"):
                raise Blocked("O resultado não corresponde à versão do processo fixada no pedido.")
            if state["process_id"] in CANDIDATE_PROCESSES:
                if result["status"] != "UNKNOWN" or result["outcome"] != "candidate":
                    raise Blocked("Este processo só pode devolver um candidato por rever.")
            if state["process_id"] in AI_PROCESSES and result["ai_calls"] != 1:
                raise Blocked("Contagem cognitiva incompatível com o processo.")
            if state["process_id"] in NO_AI_PROCESSES and result["ai_calls"] != 0:
                raise Blocked("IA proibida neste processo.")
            artifact = result.get("artifact")
            if (state["process_id"] in PDF_PROCESSES) != (artifact is not None):
                raise Blocked("Contrato de artefacto incompatível com o processo.")
            raw_pdf = None
            if artifact:
                raw_pdf = self.verify_artifact({"artifact_sha256": artifact["sha256"]}, self.path("runs", run_id))
                result = dict(result)
                result["markdown"] += "\n\nPDF SHA-256: " + artifact["sha256"]
                validate("result", result)
            candidate = self.path("creative", run_id)
            content = result["markdown"].encode("utf-8")
            references = [{"path": "creative/" + run_id + "/content.md", "sha256": digest(content)}]
            if artifact:
                references.append({"path": "creative/" + run_id + "/resultado.pdf", "sha256": artifact["sha256"]})

            def expected_provenance(timestamp):
                return {
                    "run_id": run_id, "process_id": state["process_id"], "process_version": state["process_version"],
                    "step_id": "receive-validated-result", "timestamp": timestamp, "status": result["status"],
                    "input_references": [{"path": "runs/" + run_id + "/input.bin", "sha256": state["input_sha256"]}],
                    "output_references": references,
                    "tools": [e["capability"] for e in result["evidence"]], "execution": trace,
                    "laws_sha256": digest((ROOT / "laws/CONSTITUTION.md").read_bytes()),
                    "policy_sha256": digest((ROOT / "laws/policy.json").read_bytes()),
                    "human_approval": None,
                }

            if candidate.exists():
                try:
                    existing_content = self.checked_bytes("creative", run_id, "content.md")
                    raw_result = self.checked_bytes("creative", run_id, "result.json")
                    raw_provenance = self.checked_bytes("creative", run_id, "provenance.json")
                    existing_result = validate("result", strict_json(raw_result))
                    provenance = strict_json(raw_provenance)
                    if raw_pdf is not None:
                        self.verify_artifact({"artifact_sha256": artifact["sha256"]}, candidate)
                    if (existing_content != content or existing_result != result
                            or provenance != expected_provenance(provenance.get("timestamp"))):
                        raise Blocked("Creative existente não corresponde ao resultado conservado.")
                except (OSError, ValueError, KeyError, TypeError) as error:
                    raise Blocked("Creative existente precisa de reconciliação. Conteúdo conservado.") from error
                return self.update(
                    run_id,
                    status="HUMAN_REQUIRED" if result["status"] in ("PASS", "UNKNOWN") else result["status"],
                    **({"artifact_sha256": artifact["sha256"]} if artifact else {}),
                    result_status=result["status"], outcome=result["outcome"], candidate_sha256=digest(content),
                    result_sha256=digest(raw_result), provenance_sha256=digest(raw_provenance),
                    execution_phase="RESULT_ACCEPTED",
                    message="Resultado candidato. A decisão de guardar como aprovado é tua.",
                )

            candidate.mkdir()
            if raw_pdf is not None:
                atomic(candidate / "resultado.pdf", raw_pdf)
            atomic(candidate / "content.md", content)
            atomic(candidate / "result.json", result)
            provenance = expected_provenance(now())
            atomic(candidate / "provenance.json", provenance)
            return self.update(
                run_id,
                status="HUMAN_REQUIRED" if result["status"] in ("PASS", "UNKNOWN") else result["status"],
                **({"artifact_sha256": artifact["sha256"]} if artifact else {}),
                result_status=result["status"], outcome=result["outcome"], candidate_sha256=digest(content),
                result_sha256=digest((candidate / "result.json").read_bytes()),
                provenance_sha256=digest((candidate / "provenance.json").read_bytes()),
                execution_phase="RESULT_ACCEPTED",
                message="Resultado candidato. A decisão de guardar como aprovado é tua.",
            )

    def promote(self, run_id, decision, destination="canonical"):
        """Only called by the authenticated UI after explicit confirmation."""
        with self.lock:
            if type(decision) is not HumanDecision or destination != "canonical":
                raise Blocked("BLOCK: falta uma decisão humana válida para Canonical.")
            state = self.state(run_id)
            if state["status"] not in ("HUMAN_REQUIRED", "PASS"):
                raise Blocked("Este resultado não está disponível para aprovação.")
            provenance = self.check_candidate(state)
            candidate = self.path("creative", run_id)
            raw_pdf = self.verify_artifact(state, candidate)
            content = (candidate / "content.md").read_bytes()
            if digest(content) != state["candidate_sha256"]:
                raise Blocked("O candidato mudou depois da apresentação.")
            try:
                allowed = promotion_allowed(decision, run_id, digest(content))
            except (ValueError, TypeError) as error:
                raise Blocked("A decisão não corresponde a este conteúdo.") from error
            if not allowed:
                raise Blocked("BLOCK: aprovação humana obrigatória.")
            final = self.path("canonical", run_id)
            if final.exists():
                if (final / "content.md").read_bytes() != content:
                    raise Blocked("Conflito com conhecimento já aprovado.")
                self.check_commit(state)
                return self.update(run_id, status="PASS", commit_status="COMMITTED", message="Guardado como aprovado.")
            stage = Path(tempfile.mkdtemp(prefix=".approval-", dir=self.root / "canonical"))
            approval = {
                "approval_id": decision.decision_id, "actor": decision.actor_id,
                "run_id": run_id, "sha256": digest(content), "destination": destination,
                "action": decision.action, "timestamp": now(),
            }
            provenance["human_approval"] = approval
            provenance["output_references"].append({"path": "canonical/" + run_id + "/content.md", "sha256": digest(content)})
            try:
                if raw_pdf is not None:
                    atomic(stage / "resultado.pdf", raw_pdf)
                    provenance["output_references"].append({"path": "canonical/" + run_id + "/resultado.pdf", "sha256": digest(raw_pdf)})
                atomic(stage / "content.md", content)
                atomic(stage / "approval.json", approval)
                atomic(stage / "provenance.json", provenance)
                os.rename(stage, final)
            finally:
                if stage.exists():
                    shutil.rmtree(stage)
            return self.update(run_id, status="PASS", commit_status="COMMITTED", message="Guardado como aprovado.")

    def delete(self, *_args, **_kwargs):
        raise Blocked("BLOCK: eliminação não disponibilizada neste protótipo.")
