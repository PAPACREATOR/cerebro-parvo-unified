import asyncio
import concurrent.futures
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import wave

import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from filelock import FileLock
from PIL import Image
from pydantic import ValidationError

from notebook_avatar import service as mod
from notebook_avatar.router import RenderRequest, create_router
from notebook_avatar.service import AvatarError, AvatarService, Settings, command, contained_file, digest, probe


@pytest.fixture
def setup(tmp_path):
    audio = tmp_path / "audio"
    avatars = tmp_path / "avatars"
    output = tmp_path / "output"
    for p in (audio, avatars, output):
        p.mkdir()
    with wave.open(str(audio / "episode.wav"), "wb") as wav:
        wav.setparams((1, 2, 16000, 0, "NONE", "none"))
        wav.writeframes(b"\x00\x00" * 16000)
    Image.new("RGB", (128, 128), (30, 40, 50)).save(avatars / "face.png")
    checkpoint = tmp_path / "weights.pth"
    checkpoint.write_bytes(b"TEST_ONLY_NOT_A_MODEL")
    (tmp_path / "s3fd.pth").write_bytes(b"TEST_ONLY_NOT_A_DETECTOR")
    s = Settings(audio, avatars, output, checkpoint, sys.executable, timeout=10)
    return AvatarService(s)


@pytest.fixture
def rendering(setup, monkeypatch):
    # Exercise REAL audio conversion, REAL FFmpeg MP4 creation/probe/decode,
    # and atomic publication. Substitute only the unavailable learned model.
    # This is an integration-boundary test, never lip-sync quality evidence.
    original = mod.command
    calls = []
    def fake_model(args, timeout, cwd=None, **kwargs):
        calls.append(args)
        if len(args) > 2 and args[2].endswith("worker.py"):
            value = lambda flag: args[args.index(flag) + 1]
            return original(["ffmpeg", "-nostdin", "-v", "error", "-loop", "1", "-i", value("--avatar"),
                             "-i", value("--audio"), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                             "-c:a", "aac", "-shortest", value("--output")], timeout, cwd)
        return original(args, timeout, cwd, **kwargs)
    monkeypatch.setattr(mod, "command", fake_model)
    return setup, calls


def expect(code, call):
    with pytest.raises(AvatarError) as error:
        call()
    assert error.value.code == code


BAD_PATHS = ["", ".", "..", "../outside", "/etc/passwd", "C:/data", "C:\\data", "\\server\\share",
             "file://x", "https://x", "a\x00b", "a\nb", "a\rb", "a\tb", "x/../y", "./x",
             "x/./y", "x" * 241, None, 1, True, {}, [], "D:weights", "x\\..\\file"]
@pytest.mark.parametrize("name", BAD_PATHS)
def test_escape_forms_rejected(setup, name):
    with pytest.raises(AvatarError):
        contained_file(setup.settings.audio_root, name, 100)
    assert list(setup.settings.output_root.iterdir()) == []


@pytest.mark.parametrize("name", ["ação.png", "漢字.png", "face space.png", "face;.png", "$(echo).png"])
def test_literal_filenames_no_shell(rendering, name):
    service, calls = rendering
    shutil.copyfile(service.settings.avatar_root / "face.png", service.settings.avatar_root / name)
    result = service.render("episode:ação", "episode.wav", name)
    assert result["authority"] == "UNTRUSTED"
    assert result["input"]["avatar_name"] == name
    assert service.inspect(result["job_id"]) == result


@pytest.mark.parametrize("batch", [0, 33, -1, True, False, 1.0, "8", None, 1000000])
def test_bad_batch(setup, batch):
    expect("INVALID_OPTIONS", lambda: setup.render("e", "episode.wav", "face.png", batch_size=batch))


@pytest.mark.parametrize("device", ["auto", "GPU", "CUDA", "", None, "cpu; echo bad"])
def test_bad_device(setup, device):
    expect("INVALID_OPTIONS", lambda: setup.render("e", "episode.wav", "face.png", device=device))


@pytest.mark.parametrize("episode", ["", "x" * 201, "a\x00b", "a\nb", None, {}, 1])
def test_bad_episode(setup, episode):
    expect("INVALID_EPISODE", lambda: setup.render(episode, "episode.wav", "face.png"))


@pytest.mark.parametrize("size,limit,ok", [(0, 1, False), (1, 1, True), (2, 1, False), (7, 8, True), (8, 8, True), (9, 8, False)])
def test_byte_limits(tmp_path, size, limit, ok):
    (tmp_path / "item").write_bytes(b"x" * size)
    if ok:
        assert contained_file(tmp_path, "item", limit).stat().st_size == size
    else:
        expect("INPUT_SIZE", lambda: contained_file(tmp_path, "item", limit))


@pytest.mark.parametrize("dimensions,ok", [((95, 96), False), ((96, 96), True), ((96, 2048), True),
                                           ((96, 2049), False), ((2049, 96), False), ((1, 1), False)])
def test_image_dimensions(setup, monkeypatch, dimensions, ok):
    Image.new("RGB", dimensions).save(setup.settings.avatar_root / "face.png")
    def stop_probe(*a):
        raise AvatarError("PROBE_REACHED")
    monkeypatch.setattr(mod, "probe", stop_probe)
    expect("PROBE_REACHED" if ok else "AVATAR_INVALID", lambda: setup.render("e", "episode.wav", "face.png"))


@pytest.mark.parametrize("data", [b"<html>photo</html>", b"\xff", b"not png", b"\x89PNG\r\n\x1a\n"])
def test_corrupt_avatar(setup, data):
    (setup.settings.avatar_root / "face.png").write_bytes(data)
    expect("AVATAR_INVALID", lambda: setup.render("e", "episode.wav", "face.png"))


@pytest.mark.parametrize("format", ["GIF", "BMP", "TIFF"])
def test_wrong_image_format(setup, format):
    Image.new("RGB", (128, 128)).save(setup.settings.avatar_root / "face.png", format=format)
    expect("AVATAR_INVALID", lambda: setup.render("e", "episode.wav", "face.png"))


def test_missing_checkpoint(setup):
    setup.settings.checkpoint.unlink()
    expect("CHECKPOINT_UNAVAILABLE", lambda: setup.render("e", "episode.wav", "face.png"))


def test_symlink_input_escape(setup, tmp_path):
    outside = tmp_path / "outside"
    outside.write_bytes(b"secret")
    try:
        (setup.settings.audio_root / "link").symlink_to(outside)
    except OSError:
        pytest.skip("Host cannot create symlinks")
    expect("INPUT_UNAVAILABLE", lambda: contained_file(setup.settings.audio_root, "link", 100))


@pytest.mark.parametrize("raw", ["not json", "{}", '{"format":{"duration":"NaN"},"streams":[]}',
                                 '{"format":{"duration":"Infinity"},"streams":[]}',
                                 '{"format":{"duration":"0"},"streams":[]}',
                                 '{"format":{"duration":"3600.01"},"streams":[]}',
                                 '{"format":{"duration":"1"},"streams":{}}'])
def test_invalid_probe_payload(monkeypatch, tmp_path, raw):
    monkeypatch.setattr(mod, "command", lambda *a: raw)
    expect("MEDIA_INVALID", lambda: probe(tmp_path, "ffprobe"))


def test_missing_tool():
    expect("TOOL_UNAVAILABLE", lambda: command(["nexus-tool-does-not-exist"], 1))


def test_failed_tool():
    expect("TOOL_FAILED", lambda: command([sys.executable, "-c", "raise SystemExit(3)"], 2))


def test_timeout():
    started = time.monotonic()
    expect("TOOL_TIMEOUT", lambda: command([sys.executable, "-c", "import time;time.sleep(30)"], .1))
    assert time.monotonic() - started < 3


def test_output_limit():
    expect("TOOL_OUTPUT_SIZE", lambda: command([sys.executable, "-c", "import sys;sys.stdout.write('x'*1000001)"], 3))


def test_output_invalid_utf8():
    expect("TOOL_OUTPUT_INVALID", lambda: command([sys.executable, "-c", "import sys;sys.stdout.buffer.write(b'\\xff')"], 3))


def test_cloud_secrets_not_inherited(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "secret-test")
    result = command([sys.executable, "-c", "import os;print('OPENAI_API_KEY' in os.environ)"], 3)
    assert result.strip() == "False"


def test_corrupt_audio_rejected(setup):
    (setup.settings.audio_root / "episode.wav").write_bytes(b"not audio")
    expect("TOOL_FAILED", lambda: setup.render("e", "episode.wav", "face.png"))
    assert not list(setup.settings.output_root.glob("*/provenance.json"))
    assert not list(setup.settings.output_root.glob(".avatar-*"))


def test_pipeline_reverse_idempotence_restart(rendering):
    service, calls = rendering
    audio_hash = digest(service.settings.audio_root / "episode.wav")
    avatar_hash = digest(service.settings.avatar_root / "face.png")
    result = service.render("podcast_episode:one", "episode.wav", "face.png")
    n = sum(len(c) > 2 and c[2].endswith("worker.py") for c in calls)
    assert n == 1
    assert result["input"]["audio_sha256"] == audio_hash
    assert result["input"]["avatar_original_sha256"] == avatar_hash
    assert service.render("podcast_episode:one", "episode.wav", "face.png") == result
    assert sum(len(c) > 2 and c[2].endswith("worker.py") for c in calls) == 1
    fresh = AvatarService(service.settings)
    assert fresh.inspect(result["job_id"]) == result
    assert digest(service.settings.audio_root / "episode.wav") == audio_hash
    assert digest(service.settings.avatar_root / "face.png") == avatar_hash
    assert not list(service.settings.output_root.glob(".avatar-*"))


@pytest.mark.parametrize("tamper", ["video", "job", "input", "authority", "outcome", "manifest", "missing"])
def test_tamper_rejected(rendering, tamper):
    service, calls = rendering
    result = service.render("e", "episode.wav", "face.png")
    root = service.settings.output_root / result["job_id"]
    if tamper == "video":
        (root / "video.mp4").write_bytes(b"tampered")
    elif tamper == "missing":
        (root / "video.mp4").unlink()
    elif tamper == "manifest":
        (root / "provenance.json").write_text("{}")
    else:
        if tamper == "job": result["job_id"] = "0" * 64
        if tamper == "input": result["input"]["episode_id"] = "other"
        if tamper == "authority": result["authority"] = "CANONICAL"
        if tamper == "outcome": result["outcome"] = "approved"
        (root / "provenance.json").write_text(json.dumps(result))
    key = root.name
    expect("OUTPUT_TAMPERED", lambda: service.inspect(key))
    expect("OUTPUT_TAMPERED", lambda: service.render("e", "episode.wav", "face.png"))
    assert sum(len(c) > 2 and c[2].endswith("worker.py") for c in calls) == 1


def test_changed_inputs_create_new_job(rendering):
    service, calls = rendering
    first = service.render("e", "episode.wav", "face.png")
    Image.new("RGB", (128, 128), (80, 90, 100)).save(service.settings.avatar_root / "face.png")
    second = service.render("e", "episode.wav", "face.png")
    assert first["job_id"] != second["job_id"]
    assert service.inspect(first["job_id"]) == first


def test_concurrent_same_job(rendering, monkeypatch):
    service, calls = rendering
    import threading
    started, release = threading.Event(), threading.Event()
    original = mod.command
    def delayed(args, timeout, cwd=None, **kwargs):
        if len(args) > 2 and args[2].endswith("worker.py"):
            started.set()
            assert release.wait(5)
        return original(args, timeout, cwd, **kwargs)
    monkeypatch.setattr(mod, "command", delayed)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(service.render, "e", "episode.wav", "face.png")
        assert started.wait(5)
        expect("JOB_BUSY", lambda: service.render("e", "episode.wav", "face.png"))
        release.set()
        result = first.result(10)
    assert service.inspect(result["job_id"]) == result
    assert sum(len(c) > 2 and c[2].endswith("worker.py") for c in calls) == 1


def test_worker_failure_and_retry(rendering, monkeypatch):
    service, calls = rendering
    original = mod.command
    def fail(args, timeout, cwd=None, **kwargs):
        if len(args) > 2 and args[2].endswith("worker.py"):
            raise AvatarError("TOOL_TIMEOUT")
        return original(args, timeout, cwd, **kwargs)
    monkeypatch.setattr(mod, "command", fail)
    expect("TOOL_TIMEOUT", lambda: service.render("e", "episode.wav", "face.png"))
    assert not list(service.settings.output_root.glob("*/video.mp4"))
    assert not list(service.settings.output_root.glob(".avatar-*"))
    monkeypatch.setattr(mod, "command", original)
    result = service.render("e", "episode.wav", "face.png")
    assert service.inspect(result["job_id"]) == result


def test_failure_at_atomic_publish_and_retry(rendering, monkeypatch):
    service, calls = rendering
    original = mod.os.rename
    def crash(*args):
        raise OSError("simulated failure before directory commit")
    monkeypatch.setattr(mod.os, "rename", crash)
    with pytest.raises(OSError):
        service.render("e", "episode.wav", "face.png")
    assert not list(service.settings.output_root.glob("*/provenance.json"))
    assert not list(service.settings.output_root.glob(".avatar-*"))
    monkeypatch.setattr(mod.os, "rename", original)
    result = service.render("e", "episode.wav", "face.png")
    assert AvatarService(service.settings).inspect(result["job_id"]) == result


def test_model_changed_during_execution_never_publishes(rendering, monkeypatch):
    service, calls = rendering
    original = mod.command
    def changed(args, timeout, cwd=None, **kwargs):
        result = original(args, timeout, cwd, **kwargs)
        if len(args) > 2 and args[2].endswith("worker.py"):
            service.settings.checkpoint.write_bytes(b"CHANGED_MODEL")
        return result
    monkeypatch.setattr(mod, "command", changed)
    expect("DEPENDENCY_CHANGED", lambda: service.render("e", "episode.wav", "face.png"))
    assert not list(service.settings.output_root.glob("*/provenance.json"))


def test_manifest_symlink_rejected(rendering, tmp_path):
    service, calls = rendering
    result = service.render("e", "episode.wav", "face.png")
    manifest = service.settings.output_root / result["job_id"] / "provenance.json"
    external = tmp_path / "external.json"
    external.write_bytes(manifest.read_bytes())
    manifest.unlink()
    try:
        manifest.symlink_to(external)
    except OSError:
        pytest.skip("Host cannot create symlinks")
    expect("OUTPUT_TAMPERED", lambda: service.inspect(result["job_id"]))


def test_detector_missing_prevents_worker(setup):
    setup.settings.checkpoint.with_name("s3fd.pth").unlink()
    expect("CHECKPOINT_UNAVAILABLE", lambda: setup.render("e", "episode.wav", "face.png"))


@pytest.mark.parametrize("batch", [1, 32])
def test_valid_batch_limits(rendering, batch):
    service, calls = rendering
    result = service.render("e", "episode.wav", "face.png", batch_size=batch)
    assert result["input"]["batch_size"] == batch


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf"), 3601])
def test_invalid_timeout(setup, timeout):
    from dataclasses import replace
    service = AvatarService(replace(setup.settings, timeout=timeout))
    expect("INVALID_TIMEOUT", lambda: service.render("e", "episode.wav", "face.png"))


def test_short_audio_and_no_video_response_blocked(rendering, monkeypatch):
    service, calls = rendering
    original = mod.probe
    def invalid(path, tool):
        value = original(path, tool)
        if path.name == "video.mp4":value["streams"] = [{"codec_type": "audio"}]
        return value
    monkeypatch.setattr(mod, "probe", invalid)
    expect("OUTPUT_INVALID", lambda: service.render("e", "episode.wav", "face.png"))
    assert not list(service.settings.output_root.glob("*/provenance.json"))


def test_incorrect_output_duration_blocked(rendering, monkeypatch):
    service, calls = rendering
    original = mod.probe
    def invalid(path, tool):
        value = original(path, tool)
        if path.name == "video.mp4":value["duration"] += 1
        return value
    monkeypatch.setattr(mod, "probe", invalid)
    expect("OUTPUT_INVALID", lambda: service.render("e", "episode.wav", "face.png"))
    assert not list(service.settings.output_root.glob("*/provenance.json"))


@pytest.mark.parametrize("payload", [
    {}, {"avatar": "../face.png"}, {"avatar": "https://x.png"}, {"avatar": "face.png", "batch_size": True},
    {"avatar": "face.png", "device": "auto"}, {"avatar": "face.png", "approval_id": "invented"},
    {"avatar": "face.png", "command": "whoami"}, {"avatar": "face.png", "canonical": True},
    {"avatar": "face.png", "batch_size": 0}, {"avatar": "face.png", "batch_size": 33},
    {"avatar": "face.png", "batch_size": "8"}, {"avatar": None}, {"avatar": "x" * 121},
])
def test_request_schema(payload):
    with pytest.raises(ValidationError):
        RenderRequest.model_validate(payload)


def test_native_router_roundtrip(rendering):
    service, calls = rendering
    app = FastAPI()
    async def lookup(episode):
        assert episode == "podcast_episode:one"
        return "episode.wav"
    app.include_router(create_router(lambda: service, lookup), prefix="/api")
    client = TestClient(app)
    result = client.post("/api/podcasts/episodes/podcast_episode:one/avatar", json={"avatar": "face.png"})
    assert result.status_code == 200
    key = result.json()["job_id"]
    assert client.get("/api/podcasts/avatars/" + key).json() == result.json()
    video = client.get("/api/podcasts/avatars/" + key + "/video")
    assert video.status_code == 200 and video.headers["content-type"] == "video/mp4"
    assert video.content == (service.settings.output_root / key / "video.mp4").read_bytes()


def test_installer_idempotence(tmp_path):
    script = Path(__file__).parents[1] / "install_router.py"
    spec = importlib.util.spec_from_file_location("installer", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (tmp_path / "api").mkdir()
    (tmp_path / "pyproject.toml").write_text('[project]\nversion="1.15.0"\n')
    text = 'app.include_router(podcasts.router, prefix="/api", tags=["podcasts"])\n'
    (tmp_path / "api/main.py").write_text(text)
    assert module.install(tmp_path) == "INSTALLED"
    first = (tmp_path / "api/main.py").read_bytes()
    assert module.install(tmp_path) == "ALREADY_INSTALLED"
    assert (tmp_path / "api/main.py").read_bytes() == first
    assert (tmp_path / "api/main.py.pre-avatar").read_text() == text


@pytest.mark.parametrize("version", ["1.13.0", "1.14.0", "1.14.1", "2.0.0"])
def test_installer_rejects_unverified_version(tmp_path, version):
    script = Path(__file__).parents[1] / "install_router.py"
    spec = importlib.util.spec_from_file_location("installer", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (tmp_path / "pyproject.toml").write_text(f'[project]\nversion="{version}"\n')
    with pytest.raises(ValueError):
        module.install(tmp_path)


@pytest.mark.skipif(os.name != "nt", reason="Real Windows boundary only")
def test_avatar_command_cannot_write_outside_assigned_work(tmp_path):
    protected = tmp_path / "protected"
    protected.mkdir()
    target = protected / "original"
    target.write_bytes(b"original")
    work = tmp_path / "work"
    work.mkdir()
    code = (
        "from pathlib import Path;"
        "Path('allowed').write_bytes(b'work');"
        f"target=Path({str(target)!r});\n"
        "try: target.write_bytes(b'changed');print('ALLOWED')\n"
        "except PermissionError: print('DENIED')"
    )
    assert command([sys.executable, "-I", "-c", code], 10, work).strip() == "DENIED"
    assert target.read_bytes() == b"original"
    assert (work / "allowed").read_bytes() == b"work"

@pytest.mark.skipif(os.name != "nt", reason="Real Windows boundary only")
def test_avatar_worker_requires_real_native_boundary(tmp_path):
    worker = Path(mod.__file__).with_name("worker.py")
    direct = subprocess.run([sys.executable, "-I", str(worker), "--help"],
                            capture_output=True, timeout=10)
    assert direct.returncode != 0
    assert b"Blocked" in direct.stderr
    work = tmp_path / "assigned"
    work.mkdir()
    protected = command([sys.executable, "-I", str(worker), "--help"], 10, work)
    assert "--checkpoint" in protected and "--detector" in protected

@pytest.mark.skipif(os.name != "nt", reason="Real Windows boundary only")
def test_ffmpeg_cannot_read_unneeded_host_runtime(tmp_path):
    work = tmp_path / "assigned"
    work.mkdir()
    source = work / "sample"
    source.write_bytes(b"assigned-input")
    protected = Path(sys.base_prefix) / "Lib" / "this.py"
    before = protected.read_bytes()
    def read_data(path):
        return command(["ffmpeg", "-nostdin", "-v", "error", "-f", "data", "-i",
                        str(path), "-map", "0:0", "-c", "copy", "-f", "data", "-"], 15, work)
    assert read_data(source) == "assigned-input"
    expect("TOOL_FAILED", lambda: read_data(protected))
    assert protected.read_bytes() == before


@pytest.mark.skipif(os.name != "nt", reason="Real Windows Python runtime discovery only")
def test_python_runtime_discovery_cache_returns_independent_lists():
    executable = Path(sys.executable).resolve()
    first_roots, first_dirs, first_sites = mod._python_environment(executable)
    second_roots, second_dirs, second_sites = mod._python_environment(executable)
    assert first_roots == second_roots
    assert first_dirs == second_dirs
    assert first_sites == second_sites
    assert first_roots is not second_roots
    assert first_dirs is not second_dirs
    first_roots.append(Path("synthetic-do-not-leak"))
    first_dirs.append(Path("synthetic-do-not-leak"))
    third_roots, third_dirs, third_sites = mod._python_environment(executable)
    assert Path("synthetic-do-not-leak") not in third_roots
    assert Path("synthetic-do-not-leak") not in third_dirs
    assert third_sites == first_sites
