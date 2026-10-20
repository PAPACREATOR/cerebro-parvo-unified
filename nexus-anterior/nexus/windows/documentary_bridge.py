"""Local documentary production bridge: OpenNotebook -> Forge -> MoneyPrinterTurbo -> FFmpeg.

This is an installation/lab entrypoint, not a Canonical writer. It produces an
auditable candidate directory only. The Nexus Host will get a public route only
after real Windows acceptance proves this chain.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


OPEN_NOTEBOOK_BASE = "http://127.0.0.1:5055"
FORGE_BASE = "http://127.0.0.1:7861"
MAX_HTTP = 20_000_000


class BridgeError(RuntimeError):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise BridgeError("Redirect from local tool is ARCHIVE_REDACTED_04")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise BridgeError(f"Invalid JSON configuration: {path.name}") from error
    if not isinstance(value, dict):
        raise BridgeError(f"JSON configuration must be an object: {path.name}")
    return value


def _opener():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())


def get_local_json(url: str, timeout: int = 5):
    if not (url.startswith(OPEN_NOTEBOOK_BASE) or url.startswith(FORGE_BASE)):
        raise BridgeError("Non-local network endpoint is ARCHIVE_REDACTED_04")
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with _opener().open(request, timeout=timeout) as response:
            raw = response.read(MAX_HTTP + 1)
    except BridgeError:
        raise
    except Exception as error:
        raise BridgeError(f"Local service unavailable: {url}") from error
    if len(raw) > MAX_HTTP:
        raise BridgeError("Local service response too large")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise BridgeError("Local service returned invalid JSON") from error


def post_local_json(url: str, payload: dict, *, bearer: str = "", timeout: int = 120):
    if not (url.startswith(OPEN_NOTEBOOK_BASE) or url.startswith(FORGE_BASE)):
        raise BridgeError("Non-local network endpoint is ARCHIVE_REDACTED_04")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if bearer:
        headers["Authorization"] = "Bearer " + bearer
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with _opener().open(request, timeout=timeout) as response:
            raw = response.read(MAX_HTTP + 1)
    except BridgeError:
        raise
    except Exception as error:
        raise BridgeError(f"Local POST failed: {url}") from error
    if len(raw) > MAX_HTTP:
        raise BridgeError("Local POST response too large")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise BridgeError("Local POST returned invalid JSON") from error


def load_source(path: Path, brief: str, minutes: int) -> str:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeError) as error:
        raise BridgeError("Documentary source must be readable UTF-8 text") from error
    if not text.strip() or len(raw) > 200_000 or "\x00" in text:
        raise BridgeError("Documentary source is empty, binary, or over 200 KB")
    brief = brief.strip()
    if not brief or len(brief) > 2000 or "\x00" in brief:
        raise BridgeError("Documentary brief must contain 1-2000 characters")
    return (
        f"USER BRIEF:\n{brief}\n\n"
        f"TARGET DURATION:\nApproximately {minutes} minutes.\n\n"
        "SOURCE MATERIAL — factual authority for the narration:\n"
        + text
    )


def validate_storyboard(value) -> dict:
    if not isinstance(value, dict) or set(value) != {"title", "script", "scenes"}:
        raise BridgeError("OpenNotebook documentary output has the wrong shape")
    title, script, scenes = value["title"], value["script"], value["scenes"]
    if not isinstance(title, str) or not title.strip() or len(title) > 180:
        raise BridgeError("Invalid documentary title")
    if not isinstance(script, str) or len(script.strip()) < 100 or len(script) > 30_000 or "\x00" in script:
        raise BridgeError("Invalid documentary narration")
    if not isinstance(scenes, list) or not 6 <= len(scenes) <= 40:
        raise BridgeError("Documentary storyboard must contain 6-40 scenes")
    normalized = []
    for index, scene in enumerate(scenes, 1):
        if not isinstance(scene, dict) or set(scene) != {"visual_prompt", "seconds"}:
            raise BridgeError(f"Scene {index} has the wrong shape")
        prompt, seconds = scene["visual_prompt"], scene["seconds"]
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 1000 or "\x00" in prompt:
            raise BridgeError(f"Scene {index} has an invalid visual prompt")
        if type(seconds) is not int or not 3 <= seconds <= 15:
            raise BridgeError(f"Scene {index} has an invalid duration")
        normalized.append({"visual_prompt": prompt.strip(), "seconds": seconds})
    return {"title": title.strip(), "script": script.strip(), "scenes": normalized}


def open_notebook_storyboard(config: dict, input_text: str) -> dict:
    required = {"base_url", "password", "model_id", "transformation_id"}
    if set(config) != required or config.get("base_url") != OPEN_NOTEBOOK_BASE:
        raise BridgeError("Unauthorized OpenNotebook documentary configuration")
    for key in required:
        if not isinstance(config[key], str) or not config[key] or "\x00" in config[key]:
            raise BridgeError("Invalid OpenNotebook documentary configuration")
    envelope = post_local_json(
        OPEN_NOTEBOOK_BASE + "/api/transformations/execute",
        {
            "model_id": config["model_id"],
            "transformation_id": config["transformation_id"],
            "input_text": input_text,
        },
        bearer=config["password"],
        timeout=180,
    )
    output = envelope.get("output") if isinstance(envelope, dict) else None
    if not isinstance(output, str) or len(output) > 100_000:
        raise BridgeError("OpenNotebook returned no bounded documentary JSON")
    try:
        return validate_storyboard(json.loads(output))
    except json.JSONDecodeError as error:
        raise BridgeError("OpenNotebook documentary output is not strict JSON") from error


def forge_dimensions(aspect: str) -> tuple[int, int]:
    if aspect == "16:9":
        return 768, 432
    if aspect == "9:16":
        return 432, 768
    if aspect == "1:1":
        return 512, 512
    raise BridgeError("Unsupported video aspect")


def render_scene_images(storyboard: dict, output: Path, aspect: str) -> list[Path]:
    # Prove the API surface before spending GPU time.
    options = get_local_json(FORGE_BASE + "/sdapi/v1/options", timeout=10)
    if not isinstance(options, dict):
        raise BridgeError("Forge API did not return options")
    width, height = forge_dimensions(aspect)
    images_dir = output / "scenes"
    images_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    negative = "text, watermark, logo, signature, low quality, distorted, extra limbs"
    for index, scene in enumerate(storyboard["scenes"], 1):
        response = post_local_json(
            FORGE_BASE + "/sdapi/v1/txt2img",
            {
                "prompt": scene["visual_prompt"],
                "negative_prompt": negative,
                "steps": 18,
                "width": width,
                "height": height,
                "batch_size": 1,
                "n_iter": 1,
            },
            timeout=300,
        )
        encoded = response.get("images") if isinstance(response, dict) else None
        if not isinstance(encoded, list) or len(encoded) != 1 or not isinstance(encoded[0], str):
            raise BridgeError(f"Forge returned no image for scene {index}")
        try:
            raw = base64.b64decode(encoded[0].split(",", 1)[-1], validate=True)
        except Exception as error:
            raise BridgeError(f"Forge returned invalid base64 for scene {index}") from error
        if len(raw) < 1000 or len(raw) > 20_000_000 or not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise BridgeError(f"Forge returned an invalid PNG for scene {index}")
        target = images_dir / f"scene-{index:02d}.png"
        target.write_bytes(raw)
        paths.append(target)
    return paths


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def run_moneyprinter(config: dict, storyboard: dict, scene_paths: list[Path], output: Path, aspect: str, audio: Path | None = None) -> Path:
    required = {"root", "uv", "ffmpeg", "commit"}
    if set(config) != required:
        raise BridgeError("MoneyPrinterTurbo runtime configuration has the wrong shape")
    root = Path(config["root"]).resolve()
    uv = Path(config["uv"]).resolve()
    ffmpeg = Path(config["ffmpeg"]).resolve()
    if not root.is_dir() or not uv.is_file() or not ffmpeg.is_file() or not (root / "cli.py").is_file():
        raise BridgeError("MoneyPrinterTurbo runtime is incomplete")
    materials = ",".join(str(path.resolve()) for path in scene_paths)
    command = [
        str(uv), "run", "--frozen", "python", "cli.py",
        "--video-script", storyboard["script"],
        "--video-source", "local",
        "--video-materials", materials,
        "--video-aspect", aspect,
        "--video-fit-mode", "cover",
        "--video-concat-mode", "sequential",
        "--video-transition-mode", "fade-in",
        "--video-clip-duration", "10",
        "--bgm-type", "none",
        "--video-count", "1",
        "--n-threads", "2",
        "--stop-at", "video",
    ]
    if audio is None:
        command += ["--voice-name", "no-voice", "--no-subtitle-enabled"]
    else:
        audio = audio.resolve()
        if not audio.is_file() or audio.suffix.lower() not in {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}:
            raise BridgeError("Narration audio must be an existing supported audio file")
        command += ["--custom-audio-file", str(audio), "--subtitle-enabled"]
    env = dict(__import__("os").environ)
    env["PATH"] = str(ffmpeg.parent) + __import__("os").pathsep + env.get("PATH", "")
    completed = subprocess.run(
        command,
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=7200,
    )
    (output / "moneyprinter.stdout.json").write_text(completed.stdout, encoding="utf-8")
    (output / "moneyprinter.stderr.txt").write_text(completed.stderr, encoding="utf-8")
    if completed.returncode != 0:
        raise BridgeError(f"MoneyPrinterTurbo failed with exit code {completed.returncode}")
    try:
        envelope = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise BridgeError("MoneyPrinterTurbo did not return its documented JSON result") from error
    result = envelope.get("result") if isinstance(envelope, dict) else None
    videos = result.get("videos") if isinstance(result, dict) else None
    if not isinstance(videos, list) or len(videos) != 1 or not isinstance(videos[0], str):
        raise BridgeError("MoneyPrinterTurbo returned no single final video")
    candidate = Path(videos[0])
    if not candidate.is_absolute():
        candidate = (root / candidate).resolve()
    else:
        candidate = candidate.resolve()
    if not _is_within(candidate, root) or not candidate.is_file():
        raise BridgeError("MoneyPrinterTurbo video escaped its pinned tool root")
    target = output / "documentary-candidate.mp4"
    shutil.copy2(candidate, target)
    if target.stat().st_size < 1000:
        raise BridgeError("Final video candidate is unexpectedly small")
    return target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--brief", required=True)
    parser.add_argument("--minutes", type=int, default=4)
    parser.add_argument("--aspect", choices=("16:9", "9:16", "1:1"), default="16:9")
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--audio", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.minutes <= 6:
        raise BridgeError("Documentary duration must be between 1 and 6 minutes")
    runtime = args.runtime.resolve()
    open_config = read_json(runtime / "open-notebook-documentary.json")
    mpt_config = read_json(runtime / "moneyprinterturbo.json")
    source = load_source(args.source.resolve(), args.brief, args.minutes)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)

    report = {
        "schema": "nexus.documentary-candidate.v1",
        "status": "RUNNING",
        "authority": "NONE",
        "canonical_write": False,
        "pipeline": ["open-notebook", "forge", "moneyprinterturbo", "ffmpeg"],
        "narration": "custom-audio+whisper" if args.audio else "silent-for-clipchamp",
        "source_sha256": sha256_bytes(args.source.read_bytes()),
    }
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    try:
        storyboard = open_notebook_storyboard(open_config, source)
        storyboard_raw = json.dumps(storyboard, ensure_ascii=False, indent=2).encode("utf-8")
        (output / "storyboard.json").write_bytes(storyboard_raw)
        scene_paths = render_scene_images(storyboard, output, args.aspect)
        video = run_moneyprinter(
            mpt_config, storyboard, scene_paths, output, args.aspect,
            args.audio.resolve() if args.audio else None,
        )
        report.update({
            "status": "PASS_CANDIDATE",
            "title": storyboard["title"],
            "storyboard_sha256": sha256_bytes(storyboard_raw),
            "scenes": [
                {"name": p.name, "sha256": sha256_bytes(p.read_bytes())}
                for p in scene_paths
            ],
            "video": {
                "name": video.name,
                "bytes": video.stat().st_size,
                "sha256": sha256_bytes(video.read_bytes()),
            },
            "note": "Candidate only. Promotion requires the normal Nexus human gate after Host integration.",
        })
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except Exception as error:
        report["status"] = "FAIL"
        report["error"] = str(error)
        raise
    finally:
        (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BridgeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
