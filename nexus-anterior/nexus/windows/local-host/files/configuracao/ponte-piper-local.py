"""Loopback-only OpenAI-compatible speech bridge for the installed Nexus Piper.

Run with the existing Windows host Python. This file starts no service on import.
Client base URL: http://127.0.0.1:8969/v1
Client API key: ARCHIVE_REDACTED_06 (a local routing marker, not a secret).
Model: nexus-piper-pt-pt; voice: pt_PT-tugao-medium; formats: mp3 or wav.
This standalone utility does not write to the Nexus Store or alter its authority.
"""

from __future__ import annotations

import hmac
import msvcrt
import json
import math
import os
import socket
import subprocess
import threading
import time
import unicodedata
import uuid
import wave
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = "127.0.0.1"
PORT = 8969
MODEL_ID = "nexus-piper-pt-pt"
VOICE_ID = "pt_PT-tugao-medium"
LOCAL_API_KEY = os.environ["NEXUS_PIPER_API_KEY"]
ROOT = Path("C:/Nexus")
VOICE_MODEL = ROOT / "modelos/piper/pt_PT-tugao-medium.onnx"
VOICE_CONFIG = VOICE_MODEL.with_suffix(".onnx.json")
FFMPEG = ROOT / "ferramentas/ffmpeg/ffmpeg.exe"
TEMP_ROOT = ROOT / "temporarios/tts"
WSL = str(Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32/wsl.exe")
PIPER = "/opt/nexus-piper/bin/piper"
MAX_REQUEST_BYTES = 65_536
MAX_INPUT_CHARS = 6_000
MAX_AUDIO_BYTES = 32 * 1024 * 1024
MAX_AUDIO_SECONDS = 600
REQUEST_SECONDS = 115
SPEECH_SLOT = threading.BoundedSemaphore(1)


class RequestError(Exception):
    def __init__(self, status: int, message: str, code: str = "invalid_request"):
        self.status = status
        self.message = message
        self.code = code
        super().__init__(message)


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def reject_constant(_value):
    raise ValueError("Non-finite JSON number")


def validate_request(data):
    if not isinstance(data, dict) or set(data) - {
        "model", "input", "voice", "response_format", "speed"
    }:
        raise RequestError(400, "Pedido de voz inválido ou com opções não suportadas.")
    if data.get("model") != MODEL_ID:
        raise RequestError(400, "Modelo de voz não disponível.")
    # Protocol aliases select the same installed Portuguese voice; alloy is required by Open Notebook connection tests.
    if data.get("voice", VOICE_ID) not in (VOICE_ID, "default", "alloy"):
        raise RequestError(400, "Voz não disponível.")
    text = data.get("input")
    if not isinstance(text, str) or not text.strip() or len(text) > MAX_INPUT_CHARS:
        raise RequestError(400, "O texto deve ter entre 1 e 6000 caracteres.")
    if any(unicodedata.category(char).startswith("C") and char not in "\t\n\r" for char in text):
        raise RequestError(400, "O texto contém caracteres de controlo não permitidos.")
    try:
        text.encode("utf-8", errors="strict")
    except UnicodeError as error:
        raise RequestError(400, "O texto não é UTF-8 válido.") from error
    audio_format = data.get("response_format", "mp3")
    if audio_format not in ("mp3", "wav"):
        raise RequestError(400, "Escolhe o formato mp3 ou wav.")
    speed = data.get("speed", 1.0)
    if isinstance(speed, bool) or not isinstance(speed, (int, float)):
        raise RequestError(400, "Velocidade de voz inválida.")
    if not 0.25 <= speed <= 4.0 or not math.isfinite(speed):
        raise RequestError(400, "A velocidade deve estar entre 0.25 e 4.0.")
    return text, audio_format, float(speed)


def linux_path(path: Path) -> str:
    # Called only with trusted constants or files created by temporary_audio().
    resolved = path.resolve()
    if resolved.drive.upper() != "C:":
        raise RequestError(503, "A pasta temporária local não está disponível.", "local_setup")
    return "/mnt/c/" + resolved.as_posix()[3:]


def plain_path(path: Path) -> None:
    if path.resolve() != path.absolute():
        raise RequestError(503, "O caminho local foi redirecionado.", "local_setup")


@contextmanager
def temporary_audio():
    # No caller-supplied directory, filename or recursive deletion is accepted.
    plain_path(TEMP_ROOT)
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    plain_path(TEMP_ROOT)
    folder = TEMP_ROOT / ("tts-" + uuid.uuid4().hex)
    folder.mkdir(exist_ok=False)
    wav_path, mp3_path = folder / "audio.wav", folder / "audio.mp3"
    try:
        yield wav_path, mp3_path
    finally:
        # Exact known paths only. Preserve anything unexpected for inspection.
        if folder.parent == TEMP_ROOT and folder.resolve().parent == TEMP_ROOT.resolve():
            for path in (wav_path, mp3_path):
                try:
                    if path.parent == folder and not path.is_dir():
                        path.unlink(missing_ok=True)
                except OSError:
                    pass
            try:
                folder.rmdir()
            except OSError:
                pass


def run_fixed(command, *, deadline: float, cap: float, input_bytes=None):
    remaining = min(cap, deadline - time.monotonic())
    if remaining <= 0:
        raise RequestError(504, "A geração de voz excedeu o tempo disponível.", "timeout")
    try:
        completed = subprocess.run(
            command,
            input=input_bytes,
            stdin=None if input_bytes is not None else subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=remaining,
            check=False,
            shell=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired as error:
        raise RequestError(504, "A geração de voz excedeu o tempo disponível.", "timeout") from error
    except OSError as error:
        raise RequestError(503, "O motor local de voz não pôde arrancar.", "local_setup") from error
    if completed.returncode == 124:
        raise RequestError(504, "A geração de voz excedeu o tempo disponível.", "timeout")
    if completed.returncode != 0:
        raise RequestError(502, "O motor local não conseguiu gerar o áudio.", "synthesis_failed")


def check_wav(path: Path):
    size = path.stat().st_size
    if not 44 < size <= MAX_AUDIO_BYTES:
        raise RequestError(502, "O áudio gerado tem um tamanho inválido.", "invalid_audio")
    with wave.open(str(path), "rb") as audio:
        frames = audio.getnframes()
        rate = audio.getframerate()
        channels = audio.getnchannels()
        width = audio.getsampwidth()
        if channels not in (1, 2) or width != 2 or not 8_000 <= rate <= 96_000:
            raise RequestError(502, "O áudio gerado tem um formato inválido.", "invalid_audio")
        duration = frames / rate
        if not 0 < duration <= MAX_AUDIO_SECONDS or frames * channels * width > size:
            raise RequestError(502, "O áudio gerado tem uma duração inválida.", "invalid_audio")


def synthesize(text: str, audio_format: str, speed: float) -> bytes:
    if not all(path.is_file() for path in (VOICE_MODEL, VOICE_CONFIG, FFMPEG)):
        raise RequestError(503, "Faltam ficheiros do motor local de voz.", "local_setup")
    deadline = time.monotonic() + REQUEST_SECONDS
    with temporary_audio() as (wav_path, mp3_path):
        # Linux enforces the output file size and stops Piper independently.
        command = [
            WSL, "-d", "Nexus", "-u", "root", "--exec",
            "/usr/bin/prlimit", f"--fsize={MAX_AUDIO_BYTES}:{MAX_AUDIO_BYTES}", "--",
            "/usr/bin/timeout", "--signal=TERM", "--kill-after=2s", "100s",
            PIPER, "--model", linux_path(VOICE_MODEL),
            "--output_file", linux_path(wav_path),
            "--length_scale", format(1.0 / speed, ".8f"),
        ]
        run_fixed(command, deadline=deadline, cap=106, input_bytes=(text + "\n").encode("utf-8"))
        try:
            check_wav(wav_path)
        except (OSError, wave.Error, EOFError) as error:
            raise RequestError(502, "O motor devolveu um WAV inválido.", "invalid_audio") from error
        output = wav_path
        if audio_format == "mp3":
            run_fixed(
                [str(FFMPEG), "-nostdin", "-v", "error", "-n", "-i", str(wav_path),
                 "-map_metadata", "-1", "-vn", "-ac", "1", "-c:a", "libmp3lame",
                 "-b:a", "96k", "-fs", str(MAX_AUDIO_BYTES), str(mp3_path)],
                deadline=deadline, cap=30,
            )
            output = mp3_path
        if not 0 < output.stat().st_size <= MAX_AUDIO_BYTES:
            raise RequestError(502, "O áudio gerado tem um tamanho inválido.", "invalid_audio")
        return output.read_bytes()


class SpeechServer(ThreadingHTTPServer):
    allow_reuse_address = False
    daemon_threads = True
    request_queue_size = 8

    def server_bind(self):
        if os.name == "nt":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "NexusPiper/1"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, *_args):
        pass

    def reply(self, status, payload, content_type="application/json"):
        body = payload if isinstance(payload, bytes) else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Connection", "close")
        self.end_headers()
        self.close_connection = True
        self.wfile.write(body)

    def error(self, error):
        self.reply(error.status, {"error": {"message": error.message, "type": "invalid_request_error" if error.status < 500 else "server_error", "code": error.code}})

    def guard(self, *, require_auth=True):
        if self.client_address[0] != HOST or self.headers.get_all("Host") not in (
            [f"127.0.0.1:{PORT}"], [f"localhost:{PORT}"]
        ):
            raise RequestError(403, "Apenas pedidos locais são permitidos.", "local_only")
        origin = self.headers.get("Origin")
        if origin and origin not in (f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}"):
            raise RequestError(403, "Origem não permitida.", "local_only")
        authorization = self.headers.get_all("Authorization") or []
        if len(authorization) > 1 or (authorization and not hmac.compare_digest(
            authorization[0].encode("utf-8"), ("Bearer " + LOCAL_API_KEY).encode("ascii")
        )) or (require_auth and not authorization):
            raise RequestError(401, "Configura a chave local desta ponte no cliente.", "local_auth")

    def do_GET(self):
        try:
            self.guard(require_auth=self.path != "/health")
            if self.path == "/health":
                available = all(path.is_file() for path in (VOICE_MODEL, VOICE_CONFIG, FFMPEG))
                self.reply(200 if available else 503, {"status": "ready" if available else "missing_files", "service": "nexus-piper-local", "model": MODEL_ID, "synthesis_checked": False})
            elif self.path == "/v1/models":
                self.reply(200, {"object": "list", "data": [{"id": MODEL_ID, "object": "model", "created": 0, "owned_by": "nexus-local"}]})
            elif self.path == "/v1/audio/voices":
                self.reply(200, {"voices": [{"id": VOICE_ID, "name": "Português de Portugal · Tugão", "language_code": "pt-PT", "gender": "MALE", "description": "Voz sintética Piper instalada localmente."}]})
            else:
                raise RequestError(404, "Endpoint não encontrado.", "not_found")
        except RequestError as error:
            self.error(error)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            self.close_connection = True

    def do_POST(self):
        acquired = False
        try:
            self.guard()
            if self.path != "/v1/audio/speech":
                raise RequestError(404, "Endpoint não encontrado.", "not_found")
            lengths = self.headers.get_all("Content-Length") or []
            if self.headers.get("Transfer-Encoding") or len(lengths) != 1 or not lengths[0].isdigit():
                raise RequestError(400, "Tamanho do pedido inválido.")
            length = int(lengths[0])
            if not 0 < length <= MAX_REQUEST_BYTES:
                raise RequestError(413, "Pedido demasiado grande.")
            if self.headers.get_content_type() != "application/json":
                raise RequestError(415, "Envia JSON em UTF-8.")
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise RequestError(400, "Pedido incompleto.")
            try:
                data = json.loads(raw.decode("utf-8"), object_pairs_hook=reject_duplicates, parse_constant=reject_constant)
            except (ValueError, UnicodeError, RecursionError) as error:
                raise RequestError(400, "JSON UTF-8 inválido.") from error
            text, audio_format, speed = validate_request(data)
            acquired = SPEECH_SLOT.acquire(blocking=False)
            if not acquired:
                raise RequestError(429, "Já existe uma geração de voz em curso.", "busy")
            audio = synthesize(text, audio_format, speed)
            self.reply(200, audio, "audio/mpeg" if audio_format == "mp3" else "audio/wav")
        except RequestError as error:
            self.error(error)
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            self.close_connection = True
        except Exception:
            # Never return or log text, credentials, subprocess output or paths.
            self.error(RequestError(500, "Falha interna da ponte local de voz.", "internal_error"))
        finally:
            if acquired:
                SPEECH_SLOT.release()


def serve():
    server = SpeechServer((HOST, PORT), Handler)
    print(f"Ponte de voz local pronta em http://{HOST}:{PORT}", flush=True)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    # Retain a Windows byte lock for this process lifetime; reopen is harmless.
    lock_path = ROOT / "registos/piper-local.lock"
    with lock_path.open("a+b") as lock:
        lock.seek(0)
        try:
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            return
        serve()


if __name__ == "__main__":
    main()
