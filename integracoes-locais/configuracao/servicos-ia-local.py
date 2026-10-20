"""Keep the two existing Nexus llama.cpp services local and CPU only.

Run with the bundled host Python. A second invocation is harmless. ``--stop``
requests a bounded shutdown of this supervisor's own children; a reused server
is never stopped. This file neither installs tools nor performs inference.
"""
from __future__ import annotations

import argparse
import contextlib
from datetime import datetime, timezone
import json
import logging
import msvcrt
import os
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request


ROOT = Path(r"C:\Nexus")
LOG = ROOT / "registos"
SERVER = ROOT / "ferramentas/llama/llama-server.exe"
MODELS = ROOT / "ferramentas/nexus-tools/models/llamacpp"
STATUS = LOG / "ia-local-servicos.json"
LOCK = LOG / "ia-local-servicos.lock"
STOP = LOG / "ia-local-parar.sinal"
STARTUP_TIMEOUT = 180
HTTP_TIMEOUT = 2
MAX_JSON_BYTES = 1_000_000
SHUTDOWN_TIMEOUT = 8
SERVICES = (
    {
        "name": "linguagem", "port": 18081, "alias": "nexus-qwen3-1.7b",
        "model": "Qwen3-1.7B-Q8_0.gguf", "extra": [],
    },
    {
        "name": "embedding", "port": 18082, "alias": "nexus-qwen3-embedding-0.6b",
        "model": "Qwen3-Embedding-0.6B-Q8_0.gguf",
        "extra": ["--embedding", "--pooling", "last", "--no-cont-batching"],
    },
)


class ServiceError(RuntimeError):
    """Controlled local failure, without returning arbitrary service output."""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ServiceError("Redirecionamento do servico local recusado.")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_status(state, services, *, error=None):
    value = {
        "status": state, "updated_at": utc_now(),
        "mode": "llama.cpp local; CPU por defeito", "supervisor_pid": os.getpid(),
        "services": services,
    }
    if error is not None:
        value["error"] = error
    raw = json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")
    descriptor, temporary = tempfile.mkstemp(prefix=".ia-local-", suffix=".tmp", dir=LOG)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, STATUS)
    finally:
        with contextlib.suppress(FileNotFoundError):
            Path(temporary).unlink()


def json_get(service, path):
    # No configurable hosts, proxies, credentials, redirects or remote URLs.
    request = urllib.request.Request(
        "http://127.0.0.1:" + str(service["port"]) + path,
        headers={"Accept": "application/json"}, method="GET",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=HTTP_TIMEOUT) as response:
        if response.status != 200:
            raise ServiceError("O servico local nao respondeu com sucesso.")
        raw = response.read(MAX_JSON_BYTES + 1)
    if len(raw) > MAX_JSON_BYTES:
        raise ServiceError("Resposta do servico local demasiado grande.")
    try:
        return json.loads(raw)
    except (ValueError, UnicodeError):
        raise ServiceError("Resposta do servico local invalida.") from None


def is_ready(service):
    try:
        health = json_get(service, "/health")
        models = json_get(service, "/v1/models")
    except (urllib.error.URLError, TimeoutError, OSError):
        return False
    if not isinstance(health, dict) or health.get("status") != "ok":
        return False
    if not isinstance(models, dict) or not isinstance(models.get("data"), list):
        raise ServiceError("Catalogo do servico local invalido.")
    if not any(isinstance(item, dict) and item.get("id") == service["alias"]
               for item in models["data"]):
        raise ServiceError("Porta " + str(service["port"]) + " ocupada por um modelo diferente; nada foi terminado.")
    return True


def port_free(port):
    # Windows exclusive binding detects listeners on loopback or all addresses.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def wait_ready(service, stopping, process=None):
    deadline = time.monotonic() + STARTUP_TIMEOUT
    while not stopping.is_set() and not STOP.exists():
        if process is not None and process.poll() is not None:
            raise ServiceError("O servidor de " + service["name"] + " terminou; consulta o respetivo registo.")
        if is_ready(service):
            if process is not None and process.poll() is not None:
                raise ServiceError("O servidor proprio terminou durante o arranque.")
            return
        if time.monotonic() >= deadline:
            raise ServiceError("Tempo de arranque excedido na porta " + str(service["port"]) + "; nada foi reiniciado.")
        stopping.wait(0.5)
    raise InterruptedError


def command(service):
    return [
        str(SERVER), "-m", str(MODELS / service["model"]),
        "--host", "127.0.0.1", "--port", str(service["port"]),
        "--alias", service["alias"], "-c", "8192", "-ngl", "0", "-np", "1",
        "-t", str(max(1, min(8, os.cpu_count() or 1))),
        *service["extra"],
    ]


def shutdown(children):
    # Only retained Popen handles are eligible. Never stop by PID, name or port.
    for process in reversed(children):
        if process.poll() is None:
            with contextlib.suppress(OSError):
                process.terminate()
    for process in reversed(children):
        try:
            process.wait(timeout=SHUTDOWN_TIMEOUT)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(OSError):
                process.kill()
            with contextlib.suppress(subprocess.TimeoutExpired, OSError):
                process.wait(timeout=2)


def monitor(children, stopping, logger):
    failed_checks = 0
    while not stopping.wait(5) and not STOP.exists():
        if any(process.poll() is not None for process in children):
            raise ServiceError("Um servidor proprio terminou; nao houve reinicio automatico.")
        # A single slow HTTP response is not evidence that either service died.
        # Malformed/redirected responses still raise immediately in is_ready().
        if all(is_ready(service) for service in SERVICES):
            failed_checks = 0
            continue
        failed_checks += 1
        if failed_checks >= 3:
            raise ServiceError("Um servico local falhou tres verificacoes consecutivas; nao houve reinicio automatico.")
        logger.warning("Verificacao local sem resposta (%s/3); conservar servidores.", failed_checks)


def supervise():
    LOG.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a+b") as lock:
        lock.seek(0, os.SEEK_END)
        if lock.tell() == 0:
            lock.write(b"\0")
            lock.flush()
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            return 0
        with contextlib.suppress(FileNotFoundError):
            STOP.unlink()
        logger = logging.getLogger("nexus-ia-local")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(LOG / "ia-local-supervisor.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
        stopping = threading.Event()
        previous_signals = {}
        children, streams, records = [], [], []
        failed = False
        try:
            for sig in (signal.SIGINT, signal.SIGTERM):
                previous_signals[sig] = signal.signal(sig, lambda *_args: stopping.set())
            write_status("STARTING", records)
            if not SERVER.is_file() or any(not (MODELS / item["model"]).is_file() for item in SERVICES):
                raise ServiceError("Falta o executavel llama.cpp ou um dos modelos locais existentes.")
            # Check both occupied ports before starting anything new.
            reused = {}
            for service in SERVICES:
                reused[service["name"]] = not port_free(service["port"])
                if reused[service["name"]]:
                    wait_ready(service, stopping)
            env = dict(os.environ)
            env["CUDA_VISIBLE_DEVICES"] = ""
            for service in SERVICES:
                if stopping.is_set() or STOP.exists():
                    raise InterruptedError
                owned = not reused[service["name"]]
                process = None
                if owned:
                    # Recheck immediately before spawn; a new listener is reused
                    # only after validating its configured alias, never replaced.
                    if not port_free(service["port"]):
                        wait_ready(service, stopping)
                        owned = False
                    else:
                        stream = (LOG / ("ia-local-" + service["name"] + ".log")).open("ab")
                        streams.append(stream)
                        try:
                            process = subprocess.Popen(
                                command(service), cwd=SERVER.parent, env=env,
                                stdin=subprocess.DEVNULL, stdout=stream, stderr=stream,
                                creationflags=subprocess.CREATE_NO_WINDOW,
                            )
                        except OSError:
                            raise ServiceError("Nao foi possivel iniciar o servidor de " + service["name"] + ".") from None
                        children.append(process)
                        wait_ready(service, stopping, process)
                records.append({
                    "name": service["name"], "alias": service["alias"],
                    "url": "http://127.0.0.1:" + str(service["port"]) + "/v1",
                    "ownership": "OWNED" if owned else "REUSED",
                    "pid": process.pid if process is not None else None,
                    "gpu_layers": 0 if owned else None,
                })
            write_status("READY", records)
            logger.info("Servicos de linguagem e embedding prontos; servidores reutilizados nao serao terminados.")
            monitor(children, stopping, logger)
        except InterruptedError:
            logger.info("Paragem local solicitada.")
        except Exception as error:
            failed = True
            message = str(error) if isinstance(error, ServiceError) else "Falha do supervisor local; consultar os registos."
            logger.error("%s", message)
            write_status("FAIL", records, error=message)
        finally:
            shutdown(children)
            for stream in streams:
                stream.close()
            if not failed:
                write_status("STOPPED", records)
            with contextlib.suppress(FileNotFoundError):
                STOP.unlink()
            for sig, previous in previous_signals.items():
                signal.signal(sig, previous)
            logger.removeHandler(handler)
            handler.close()
        return 1 if failed else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stop", action="store_true", help="Pedir paragem dos filhos deste supervisor.")
    args = parser.parse_args()
    if args.stop:
        LOG.mkdir(parents=True, exist_ok=True)
        STOP.write_text("stop\n", encoding="ascii")
        return 0
    return supervise()


if __name__ == "__main__":
    raise SystemExit(main())
