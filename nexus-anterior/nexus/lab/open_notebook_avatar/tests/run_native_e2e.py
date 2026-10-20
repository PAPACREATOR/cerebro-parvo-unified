"""Opt-in real Open Notebook + SurrealDB + Wav2Lip + MCP acceptance test.

Uses a private source checkout, a synthetic episode row and supplied local
speech/portrait fixtures. It never generates a podcast with an LLM/TTS provider.
All subprocesses share the same network namespace and are stopped at exit.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import uuid

import httpx


def wait_ready(url, process, timeout=120):
    deadline = time.monotonic() + timeout
    with httpx.Client(trust_env=False, timeout=2) as client:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Lab server exited during startup")
            try:
                if client.get(url).status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            time.sleep(.2)
    raise TimeoutError("Lab server did not become ready")


def main():
    parser = argparse.ArgumentParser()
    for name in ("source-root", "python-api", "python-worker", "surreal", "checkpoint", "audio", "portrait", "report"):
        parser.add_argument("--" + name, type=Path, required=True)
    a = parser.parse_args()
    a.report.mkdir(parents=True, exist_ok=False)
    report = {"status": "RUNNING", "scope": "real native Open Notebook API, synthetic episode with supplied speech; no TTS generation", "checks": []}
    def record(name):
        report["checks"].append(name)
        print(name, flush=True)
        (a.report / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    processes = []
    logs = []
    env = dict(os.environ)
    env.update(SURREAL_URL="ws://127.0.0.1:8000/rpc", SURREAL_USER="root", SURREAL_PASSWORD="ARCHIVE_REDACTED_02",
               OPEN_NOTEBOOK_PASSWORD="ARCHIVE_REDACTED_02", OPEN_NOTEBOOK_ENCRYPTION_KEY="ARCHIVE_REDACTED_02",
               PYTHONPATH=str(a.source_root.resolve()),
               OPEN_NOTEBOOK_AVATAR_ROOT=str(a.portrait.resolve().parent),
               OPEN_NOTEBOOK_AVATAR_OUTPUT=str((a.report / "videos").resolve()),
               OPEN_NOTEBOOK_AVATAR_CHECKPOINT=str(a.checkpoint.resolve()),
               OPEN_NOTEBOOK_AVATAR_PYTHON=str(a.python_worker.absolute()))
    episode_audio = a.source_root / ("data/podcasts/avatar-lab-" + uuid.uuid4().hex + ".wav")
    episode_audio.parent.mkdir(parents=True, exist_ok=True)
    if episode_audio.exists():
        raise RuntimeError("Refusing to overwrite a previous lab source")
    shutil.copyfile(a.audio, episode_audio)
    try:
        for name, cmd, cwd in [
            ("database", [str(a.surreal.resolve()), "start", "--no-banner", "--bind", "127.0.0.1:8000", "--user", "root", "--pass", "ARCHIVE_REDACTED_02", "memory"], a.source_root),
            ("api", [str(a.python_api.absolute()), "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "5055"], a.source_root)]:
            log = (a.report / (name + ".log")).open("w")
            logs.append(log)
            process = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=log, stderr=log)
            processes.append(process)
            wait_ready("http://127.0.0.1:" + ("8000/health" if name == "database" else "5055/health"), process)
            record(name + " real startup PASS")
        seed = """
import asyncio
from open_notebook.database.repository import repo_query
async def main():
 await repo_query('CREATE episode:avatar_lab CONTENT {name: "Avatar lab", briefing: "Synthetic fixture", content: "Upstream speech sample", episode_profile: {}, speaker_profile: {}, audio_file: "avatar-lab-test.wav", transcript: {}, outline: {}};')
asyncio.run(main())
"""
        seed = seed.replace("avatar-lab-test.wav", episode_audio.name)
        subprocess.run([str(a.python_api.absolute()), "-c", seed], cwd=a.source_root, env=env, check=True, timeout=20)
        record("native episode persisted in real SurrealDB PASS")
        with httpx.Client(base_url="http://127.0.0.1:5055", trust_env=False, timeout=960) as client:
            route = "/api/podcasts/episodes/episode:avatar_lab/avatar"
            assert client.post(route, json={"avatar": a.portrait.name}).status_code == 401
            client.headers["Authorization"] = "Bearer wrong"
            assert client.post(route, json={"avatar": a.portrait.name}).status_code == 401
            client.headers["Authorization"] = "Bearer ARCHIVE_REDACTED_02"
            record("native auth missing and wrong credentials rejected PASS")
            for payload in [{"avatar": "../escape.png"}, {"avatar": a.portrait.name, "approval_id": "fake"},
                            {"avatar": a.portrait.name, "batch_size": True}, {"avatar": a.portrait.name, "device": "auto"}]:
                assert client.post(route, json=payload).status_code == 422
            record("native malformed/path/authority requests rejected PASS")
            started = time.monotonic()
            response = client.post(route, json={"avatar": a.portrait.name})
            if response.status_code != 200:
                raise RuntimeError(f"Render failed: {response.status_code} {response.text}")
            manifest = response.json()
            report["render_seconds"] = time.monotonic() - started
            report["manifest"] = manifest
            key = manifest["job_id"]
            assert manifest["input"]["episode_id"] == "episode:avatar_lab"
            assert manifest["input"]["audio_sha256"] == hashlib.sha256(a.audio.read_bytes()).hexdigest()
            record("native API -> real SFD/Wav2Lip -> FFmpeg -> MP4/provenance PASS")
            assert client.get("/api/podcasts/avatars/" + key).json() == manifest
            video = client.get("/api/podcasts/avatars/" + key + "/video")
            assert video.status_code == 200
            assert hashlib.sha256(video.content).hexdigest() == manifest["output"]["sha256"]
            record("native video download -> source hash reverse PASS")
            assert client.post(route, json={"avatar": a.portrait.name}).json() == manifest
            record("native repeat same job/hash PASS")
        # Real stdio MCP discovery and calls against the same authenticated API.
        mcp_code = """
import asyncio, json, os, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
async def main():
 p=StdioServerParameters(command=sys.executable,args=['-m','notebook_avatar.mcp_server'],env=dict(os.environ))
 async with stdio_client(p) as (r,w):
  async with ClientSession(r,w) as s:
   await s.initialize()
   names={t.name for t in (await s.list_tools()).tools}
   assert names == {'render_podcast_avatar','get_podcast_avatar'}
   for name,args in [('get_podcast_avatar',{'job_id':sys.argv[1]}), ('render_podcast_avatar',{'episode_id':'episode:avatar_lab','avatar':sys.argv[2]})]:
    result=await s.call_tool(name,args)
    assert not result.isError
    value=result.structuredContent
    if value is None:value=json.loads(result.content[0].text)
    assert value['job_id']==sys.argv[1] and value['authority']=='UNTRUSTED'
asyncio.run(main())
"""
        subprocess.run([str(a.python_worker.absolute()), "-c", mcp_code, key, a.portrait.name], env=env, check=True, timeout=60)
        record("real stdio MCP discovery + render/status roundtrip PASS")
        # Restart actual API, keeping the source DB live and committed outputs.
        processes[-1].terminate()
        processes[-1].wait(20)
        restarted = subprocess.Popen([str(a.python_api.absolute()), "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "5055"], cwd=a.source_root, env=env, stdout=logs[-1], stderr=logs[-1])
        processes.append(restarted)
        wait_ready("http://127.0.0.1:5055/health", restarted)
        with httpx.Client(base_url="http://127.0.0.1:5055", trust_env=False, timeout=20,
                          headers={"Authorization": "Bearer ARCHIVE_REDACTED_02"}) as client:
            assert client.get("/api/podcasts/avatars/" + key).json() == manifest
            record("real API restart -> exact provenance recovery PASS")
            path = a.report / "videos" / key / "video.mp4"
            old = path.read_bytes()
            path.write_bytes(b"tampered")
            assert client.get("/api/podcasts/avatars/" + key).status_code == 400
            path.write_bytes(old)
            assert client.get("/api/podcasts/avatars/" + key).json() == manifest
            record("native output tamper rejected and recovery PASS")
        report["status"] = "PASS"
        record("acceptance finished; visual quality and Windows/GPU remain separate gates")
    except Exception as error:
        report["status"] = "FAIL"
        report["error"] = str(error)
        record("acceptance FAIL")
        raise
    finally:
        for process in reversed(processes):
            if process.poll() is None:
                process.terminate()
                try: process.wait(20)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        for stream in logs:
            stream.close()
        episode_audio.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
