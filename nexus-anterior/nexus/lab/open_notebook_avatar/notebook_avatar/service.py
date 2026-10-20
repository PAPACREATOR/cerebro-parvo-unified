"""Bounded local audio + portrait -> talking MP4, with reusable provenance.

Inputs are operator-controlled files. No network, shell commands, deletion of
sources, Canonical access, or automatic promotion. Windows child processes and image decoding use the verified Nexus boundary.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from filelock import FileLock, Timeout
from PIL import Image


class AvatarError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


# Bind trusted runtime modules and DLL prototypes when the service starts.
# This creates no task, profile, process or ACL; each invocation still verifies
# the seal and creates a fresh task identity before running the selected tool.
_NATIVE_RUNTIME = None
if os.name == "nt":
    try:
        from nexus.contracts import ROOT as _ROOT, Blocked as _Blocked
        from nexus.host import verify_integrity as _verify_integrity
        from nexus.windows_sandbox import _API, launch_confined as _launch, task_environment as _environment
    except ImportError:
        pass
    else:
        _verify_integrity()
        _API()
        _NATIVE_RUNTIME = (_ROOT, _Blocked, _verify_integrity, _launch, _environment)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def contained_file(root: Path, name: str, max_bytes: int) -> Path:
    # Reject both Windows and POSIX escape forms even when tested on Linux.
    if not isinstance(name, str) or not name or len(name) > 240:
        raise AvatarError("INVALID_PATH")
    if any(ord(c) < 32 for c in name) or "\\" in name or ":" in name:
        raise AvatarError("INVALID_PATH")
    relative = Path(name)
    if relative.is_absolute() or any(part in {".", ".."} for part in name.split("/")):
        raise AvatarError("INVALID_PATH")
    path = (root.resolve() / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise AvatarError("INPUT_UNAVAILABLE")
    if not 0 < path.stat().st_size <= max_bytes:
        raise AvatarError("INPUT_SIZE")
    return path


def _tool(value: str) -> str:
    found = shutil.which(value)
    if not found:
        raise AvatarError("TOOL_UNAVAILABLE")
    return str(Path(found).resolve())


_PYTHON_ENVIRONMENT_CACHE = {}


def _python_environment(executable):
    """Select Python files without granting its complete package installation."""
    executable = Path(executable).resolve()
    cache_key = str(executable)
    cached = _PYTHON_ENVIRONMENT_CACHE.get(cache_key)
    if cached is not None:
        roots, directories, sites = cached
        return list(roots), list(directories), tuple(sites)

    prefix = executable.parent.parent if executable.parent.name.lower() == "scripts" else executable.parent
    prefix = prefix.resolve()
    base = Path(sys.base_prefix).resolve() if prefix == Path(sys.prefix).resolve() else prefix
    config = prefix / "pyvenv.cfg"
    roots = [executable]
    if config.is_file():
        if config.is_symlink() or config.stat().st_size > 4096:
            raise AvatarError("TOOL_UNAVAILABLE")
        roots.append(config)
        for line in config.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip().lower() == "home":
                home = Path(value.strip())
                if not home.is_absolute():
                    raise AvatarError("TOOL_UNAVAILABLE")
                base = home.resolve(strict=True)
    library = base / "Lib"
    if not library.is_dir():
        raise AvatarError("TOOL_UNAVAILABLE")
    directories = [prefix, base, library]
    for folder in dict.fromkeys((prefix, base)):
        roots.extend(folder.glob("*.dll"))
        roots.extend(folder.glob("python*.zip"))
        if (folder / "DLLs").is_dir():
            roots.append(folder / "DLLs")
    # FileFinder needs enumeration of Lib; granting every descendant would
    # also propagate task ACLs over unrelated upstream packages.
    roots.extend(p for p in library.iterdir() if p.name.lower() != "site-packages")
    sites = tuple(dict.fromkeys(p for p in (prefix / "Lib" / "site-packages",
                                           base / "Lib" / "site-packages") if p.is_dir()))
    directories.extend(sites)
    frozen = (tuple(roots), tuple(directories), tuple(sites))
    _PYTHON_ENVIRONMENT_CACHE[cache_key] = frozen
    return list(frozen[0]), list(frozen[1]), frozen[2]


# Pure discovery only: no process, profile, ACL or capability is created here.
# Moving this stable filesystem enumeration outside the first timed tool call
# avoids charging Python installation discovery to the tool timeout contract.
if os.name == "nt" and _NATIVE_RUNTIME is not None:
    try:
        _python_environment(Path(sys.executable))
    except AvatarError:
        pass


def _windows_command(args, timeout, cwd, read_roots):
    if _NATIVE_RUNTIME is None:
        raise AvatarError("TOOL_UNAVAILABLE")
    ROOT, Blocked, verify_integrity, launch_confined, task_environment = _NATIVE_RUNTIME
    executable = Path(_tool(args[0]))
    try:
        directories = []
        if executable.stem.lower() in {"python", "pythonw"}:
            roots, directories, _ = _python_environment(executable)
            roots.extend(ROOT / name for name in ("__init__.py", "contracts.py", "windows_sandbox.py"))
            roots.append(Path(__file__).with_name("worker.py"))
            directories.append(ROOT)
        else:
            roots = [executable.parent]
        roots.extend(read_roots)
        verify_integrity()
        with launch_confined([str(executable), *args[1:]], cwd=Path(cwd).resolve(),
                env=task_environment(Path(cwd).resolve()), read_roots=tuple(dict.fromkeys(roots)),
                read_dirs=tuple(dict.fromkeys(directories))) as process:
            try:
                data, error = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                raise AvatarError("TOOL_TIMEOUT") from None
            if process.returncode:
                raise AvatarError("TOOL_FAILED") from RuntimeError(error[:4000].decode("utf-8", errors="replace"))
    except (Blocked, OSError):
        raise AvatarError("TOOL_UNAVAILABLE") from None
    if len(data) > 1_000_000:
        raise AvatarError("TOOL_OUTPUT_SIZE")
    try:
        return data.decode("utf-8")
    except UnicodeError:
        raise AvatarError("TOOL_OUTPUT_INVALID") from None


def command(args: list[str], timeout: float, cwd: Path | None = None, *, read_roots=()) -> str:
    if os.name == "nt":
        if cwd is None:
            with tempfile.TemporaryDirectory(prefix="nexus-avatar-tool-") as temporary:
                return _windows_command(args, timeout, Path(temporary), read_roots)
        return _windows_command(args, timeout, cwd, read_roots)
    env = {k: v for k, v in os.environ.items() if k in {
        "PATH", "SystemRoot", "WINDIR", "TEMP", "TMP", "TMPDIR", "HOME", "USERPROFILE",
        "CUDA_VISIBLE_DEVICES", "LD_LIBRARY_PATH"}}
    try:
        with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
            process = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                       cwd=cwd, env=env, start_new_session=True)
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise AvatarError("TOOL_TIMEOUT") from None
            if process.returncode:
                raise AvatarError("TOOL_FAILED")
            stdout.seek(0)
            data = stdout.read(1_000_001)
    except OSError:
        raise AvatarError("TOOL_UNAVAILABLE") from None
    if len(data) > 1_000_000:
        raise AvatarError("TOOL_OUTPUT_SIZE")
    try:
        return data.decode("utf-8")
    except UnicodeError:
        raise AvatarError("TOOL_OUTPUT_INVALID") from None


def probe(path: Path, ffprobe: str) -> dict:
    raw = command([ffprobe, "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)], 20, path.parent)
    try:
        value = json.loads(raw)
        duration = float(value["format"]["duration"])
        if not math.isfinite(duration) or not 0 < duration <= 3600:
            raise ValueError
        if not isinstance(value["streams"], list):
            raise ValueError
        return {"duration": duration, "streams": value["streams"]}
    except (ValueError, TypeError, KeyError):
        raise AvatarError("MEDIA_INVALID") from None


@dataclass(frozen=True)
class Settings:
    audio_root: Path
    avatar_root: Path
    output_root: Path
    checkpoint: Path
    worker_python: str
    ffmpeg: str = "ffmpeg"
    ffprobe: str = "ffprobe"
    timeout: float = 900
    detector_checkpoint: Path | None = None


class AvatarService:
    def __init__(self, settings: Settings):
        self.settings = settings

    def inspect(self, key: str) -> dict:
        if not isinstance(key, str) or not re.fullmatch(r"[a-f0-9]{64}", key):
            raise AvatarError("INVALID_JOB")
        directory = self.settings.output_root.resolve() / key
        if directory.is_symlink():
            raise AvatarError("OUTPUT_TAMPERED")
        manifest_path = directory / "provenance.json"
        if manifest_path.is_symlink():
            raise AvatarError("OUTPUT_TAMPERED")
        if not manifest_path.is_file():
            raise AvatarError("JOB_NOT_FOUND")
        try:
            if manifest_path.stat().st_size > 100_000:
                raise ValueError
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            video = directory / "video.mp4"
            if manifest["job_id"] != key or video.is_symlink() or not video.is_file():
                raise ValueError
            if digest(video) != manifest["output"]["sha256"]:
                raise ValueError
            # Manifest identity is bound to the input contract, not its filename alone.
            encoded = json.dumps(manifest["input"], sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
            if hashlib.sha256(encoded).hexdigest() != key:
                raise ValueError
            if manifest["authority"] != "UNTRUSTED" or manifest["outcome"] != "candidate":
                raise ValueError
            return manifest
        except (ValueError, TypeError, KeyError, OSError):
            raise AvatarError("OUTPUT_TAMPERED") from None

    def render(self, episode_id: str, audio_name: str, avatar_name: str,
               device: str = "cpu", batch_size: int = 8) -> dict:
        if not isinstance(episode_id, str) or not 1 <= len(episode_id) <= 200 or any(ord(c) < 32 for c in episode_id):
            raise AvatarError("INVALID_EPISODE")
        if device not in {"cpu", "cuda"} or type(batch_size) is not int or not 1 <= batch_size <= 32:
            raise AvatarError("INVALID_OPTIONS")
        s = self.settings
        if not math.isfinite(s.timeout) or not 0 < s.timeout <= 3600:
            raise AvatarError("INVALID_TIMEOUT")
        audio = contained_file(s.audio_root, audio_name, 100_000_000)
        avatar = contained_file(s.avatar_root, avatar_name, 20_000_000)
        if not s.checkpoint.is_file() or s.checkpoint.is_symlink():
            raise AvatarError("CHECKPOINT_UNAVAILABLE")
        detector_checkpoint = s.detector_checkpoint or s.checkpoint.with_name("s3fd.pth")
        if not detector_checkpoint.is_file() or detector_checkpoint.is_symlink():
            raise AvatarError("CHECKPOINT_UNAVAILABLE")
        worker = Path(__file__).with_name("worker.py")
        s.output_root.mkdir(parents=True, exist_ok=True)
        # Snapshot first. The inference worker never receives original input paths.
        with tempfile.TemporaryDirectory(prefix=".avatar-", dir=s.output_root) as temporary:
            stage = Path(temporary)
            audio_copy = stage / "input-audio"
            shutil.copyfile(audio, audio_copy)
            avatar_copy = stage / "original-avatar"
            shutil.copyfile(avatar, avatar_copy)
            if not 0 < avatar_copy.stat().st_size <= 20_000_000:
                raise AvatarError("INPUT_SIZE")
            image_copy = stage / "avatar.png"
            try:
                if os.name == "nt":
                    # Only copied bytes reach PIL; the Host never decodes an image.
                    decode = (
                        "from PIL import Image;"
                        "im=Image.open('original-avatar');"
                        "assert im.format in {'JPEG','PNG'};"
                        "assert 96 <= min(im.size) and max(im.size) <= 2048;"
                        "im.load();im.convert('RGB').save('avatar.png')"
                    )
                    dependencies = [Path(Image.__file__).resolve().parent]
                    xml = getattr(Image, "ElementTree", None)
                    if xml is not None and xml.__name__.startswith("defusedxml"):
                        dependencies.append(Path(xml.__file__).resolve().parent)
                    command([sys.executable, "-I", "-c", decode], 30, stage,
                            read_roots=tuple(dependencies))
                else:
                    with Image.open(avatar_copy) as image:
                        if image.format not in {"JPEG", "PNG"} or not 96 <= min(image.size) or max(image.size) > 2048:
                            raise ValueError
                        image.load()
                        image.convert("RGB").save(image_copy)
            except Exception as error:
                raise AvatarError("AVATAR_INVALID") from error
            if not 0 < audio_copy.stat().st_size <= 100_000_000:
                raise AvatarError("INPUT_SIZE")
            # Record original image bytes too; protect against changes during decoding.
            original_hash = digest(avatar_copy)
            audio_info = probe(audio_copy, s.ffprobe)
            if not any(x.get("codec_type") == "audio" for x in audio_info["streams"]):
                raise AvatarError("AUDIO_REQUIRED")
            contract = {"episode_id": episode_id, "audio_name": audio_name,
                        "audio_sha256": digest(audio_copy), "avatar_name": avatar_name,
                        "avatar_original_sha256": original_hash, "avatar_sha256": digest(image_copy),
                        "checkpoint_sha256": digest(s.checkpoint), "worker_sha256": digest(worker),
                        "detector_sha256": digest(detector_checkpoint),
                        "device": device, "batch_size": batch_size, "extension_version": "0.1.0"}
            key = hashlib.sha256(json.dumps(contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
            lock = FileLock(str(s.output_root / (key + ".lock")))
            try:
                with lock.acquire(timeout=0):
                    if (s.output_root / key).exists():
                        return self.inspect(key)
                    wav = stage / "audio.wav"
                    command([s.ffmpeg, "-nostdin", "-v", "error", "-i", str(audio_copy),
                             "-vn", "-ac", "1", "-ar", "16000", str(wav)], 60, stage)
                    video = stage / "video.mp4"
                    command([s.worker_python, "-I", str(worker), "--audio", str(wav), "--avatar", str(image_copy),
                             "--output", str(video), "--checkpoint", str(s.checkpoint.resolve()),
                             "--detector", str(detector_checkpoint.resolve()),
                             "--device", device, "--batch-size", str(batch_size), "--ffmpeg", _tool(s.ffmpeg)],
                            s.timeout, stage, read_roots=(s.checkpoint.resolve(), detector_checkpoint.resolve(),
                                                         Path(_tool(s.ffmpeg)).parent,
                                                         *(_python_environment(Path(_tool(s.worker_python)))[2]
                                                           if os.name == "nt" else ())))
                    if (digest(s.checkpoint) != contract["checkpoint_sha256"] or
                        digest(detector_checkpoint) != contract["detector_sha256"] or
                        digest(worker) != contract["worker_sha256"]):
                        raise AvatarError("DEPENDENCY_CHANGED")
                    info = probe(video, s.ffprobe)
                    kinds = {x.get("codec_type") for x in info["streams"]}
                    if not {"audio", "video"} <= kinds or abs(info["duration"] - audio_info["duration"]) > 0.5:
                        raise AvatarError("OUTPUT_INVALID")
                    command([s.ffmpeg, "-nostdin", "-v", "error", "-i", str(video), "-f", "null", "-"], 120, stage)
                    manifest = {"job_id": key, "status": "PASS", "outcome": "candidate", "authority": "UNTRUSTED",
                                "input": contract, "output": {"file": "video.mp4", "sha256": digest(video),
                                "duration": info["duration"], "bytes": video.stat().st_size},
                                "scope": "technical media validation; lip-sync quality requires human review"}
                    publish = stage / "publish"
                    publish.mkdir()
                    shutil.move(video, publish / "video.mp4")
                    (publish / "provenance.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
                    # One directory commit: crashes cannot expose a half-published job.
                    os.rename(publish, s.output_root / key)
                    return self.inspect(key)
            except Timeout:
                raise AvatarError("JOB_BUSY") from None
