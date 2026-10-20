"""Create and validate the Nexus-owned MoneyPrinterTurbo local configuration.

Installation helper only. It never reads or writes Nexus Creative/Canonical.
The upstream repository is pinned by the PowerShell installer; this helper
fails if the expected configuration anchors are absent instead of guessing.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path


class SetupError(RuntimeError):
    pass


def replace_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise SetupError(f"MoneyPrinterTurbo config anchor missing or ambiguous: {label}")
    return updated


def configure(root: Path, ffmpeg: Path, device: str) -> dict:
    example = root / "config.example.toml"
    target = root / "config.toml"
    if not example.is_file():
        raise SetupError("MoneyPrinterTurbo config.example.toml missing")
    if not ffmpeg.is_file():
        raise SetupError("FFmpeg executable missing")

    text = example.read_text(encoding="utf-8")
    text = replace_once(text, r'^llm_provider = "moonshot"$', 'llm_provider = "openai"', "llm_provider")
    text = replace_once(text, r'^openai_api_key = ""$', 'openai_api_key = "ARCHIVE_REDACTED_01"', "openai_api_key")
    text = replace_once(text, r'^openai_base_url = ""$', 'openai_base_url = "http://127.0.0.1:18081/v1"', "openai_base_url")
    text = replace_once(text, r'^openai_model_name = ""$', 'openai_model_name = "nexus-qwen3-1.7b"', "openai_model_name")
    text = replace_once(text, r'^subtitle_provider = "edge"$', 'subtitle_provider = "whisper"', "subtitle_provider")

    ffmpeg_toml = ffmpeg.resolve().as_posix().replace('"', '\\"')
    text = replace_once(
        text,
        r'^# ffmpeg_path = ""$',
        f'ffmpeg_path = "{ffmpeg_toml}"',
        "ffmpeg_path",
    )

    # The 8 GB target cannot justify large-v3 for this assembly role.
    text = replace_once(text, r'^model_size = "large-v3"$', 'model_size = "small"', "whisper.model_size")
    text = replace_once(text, r'^device = "cpu"$', f'device = "{device}"', "whisper.device")
    compute = "int8_float16" if device == "cuda" else "int8"
    text = replace_once(text, r'^compute_type = "int8"$', f'compute_type = "{compute}"', "whisper.compute_type")

    # No TTS provider is configured for the Nexus documentary path. If narration
    # is supplied, MoneyPrinterTurbo receives it through --custom-audio-file and
    # Whisper may derive subtitles. Without narration the render is silent.

    # Never auto-open Explorer from a headless Nexus-owned render.
    text = replace_once(
        text,
        r'^open_task_folder_on_completion = true$',
        'open_task_folder_on_completion = false',
        "ui.open_task_folder_on_completion",
    )

    target.write_text(text, encoding="utf-8")
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise SetupError(f"Generated MoneyPrinterTurbo config is invalid TOML: {error}") from error

    expected = {
        "llm_provider": "openai",
        "openai_api_key": "ARCHIVE_REDACTED_01",
        "openai_base_url": "http://127.0.0.1:18081/v1",
        "openai_model_name": "nexus-qwen3-1.7b",
        "subtitle_provider": "whisper",
        "ffmpeg_path": ffmpeg.resolve().as_posix(),
    }
    for key, value in expected.items():
        if parsed.get("app", {}).get(key) != value:
            raise SetupError(f"MoneyPrinterTurbo local config did not round-trip: {key}")
    return {
        "schema": "nexus.moneyprinterturbo-local-config.v1",
        "status": "PASS",
        "config": str(target),
        "llm": {
            "provider": "openai",
            "transport": "local-openai-compatible",
            "runtime": "llama.cpp",
            "base_url": expected["openai_base_url"],
            "model": expected["openai_model_name"],
        },
        "tts": {"provider": "none", "mode": "custom-audio-or-silent"},
        "subtitles": {"provider": "whisper", "model": "small", "device": device, "compute_type": compute},
        "ffmpeg": str(ffmpeg.resolve()),
        "network_contract": "LOCAL_RUNTIME_ONLY_FOR_NEXUS_PATH",
        "authority": "NONE",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--authorize-install", action="store_true")
    args = parser.parse_args()
    if not args.authorize_install:
        raise SetupError("NEXUS_INSTALL_AUTHORIZATION_REQUIRED")
    report = configure(args.root.resolve(), args.ffmpeg.resolve(), args.device)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("MONEYPRINTERTURBO_LOCAL_CONFIG=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SetupError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
