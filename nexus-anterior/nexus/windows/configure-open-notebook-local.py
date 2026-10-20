"""Configure a pinned local Open Notebook through its public authenticated API.

Installation helper only. It never reads or writes Nexus Creative/Canonical.
Existing named configuration is preserved unless it exactly matches the Nexus
local contract; conflicts fail closed instead of being silently overwritten.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class SetupError(RuntimeError):
    pass


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key.strip()] = value
    return values


class API:
    def __init__(self, base: str, password: str):
        self.base = base.rstrip("/")
        self.password = password

    def call(self, method: str, path: str, payload=None):
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Authorization": "Bearer " + self.password, "Content-Type": "application/json"}
        request = Request(self.base + path, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=45) as response:
                raw = response.read()
        except HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")[:2000]
            raise SetupError(f"Open Notebook API {method} {path} -> {error.code}: {body}") from error
        except URLError as error:
            raise SetupError(f"Open Notebook API unavailable: {error}") from error
        try:
            return json.loads(raw) if raw else None
        except json.JSONDecodeError as error:
            raise SetupError(f"Open Notebook returned invalid JSON for {path}") from error


def normalized_modalities(value) -> list[str]:
    return sorted(str(item) for item in (value or []))


def credential(api: API, provider: str, name: str, payload: dict):
    existing = api.call("GET", "/api/credentials/by-provider/" + quote(provider, safe=""))
    found = [item for item in existing if item.get("name") == name]
    if len(found) > 1:
        raise SetupError(f"Duplicate Open Notebook credential name: {name}")
    if found:
        item = found[0]
        if item.get("provider") != provider:
            raise SetupError(f"Credential provider mismatch: {name}")
        if normalized_modalities(item.get("modalities")) != normalized_modalities(payload.get("modalities")):
            raise SetupError(f"Credential modalities conflict: {name}")
        if (item.get("base_url") or None) != (payload.get("base_url") or None):
            raise SetupError(f"Credential base URL conflict: {name}")
        if bool(payload.get("api_key")) != bool(item.get("has_api_key")):
            raise SetupError(f"Credential key contract conflict: {name}")
        return item
    return api.call("POST", "/api/credentials", payload)


def model(api: API, *, name: str, provider: str, model_type: str, credential_id: str):
    items = api.call("GET", "/api/models")
    matches = [
        item for item in items
        if item.get("name") == name and item.get("provider") == provider and item.get("type") == model_type
    ]
    if len(matches) > 1:
        raise SetupError(f"Duplicate Open Notebook model: {provider}/{model_type}/{name}")
    if matches:
        item = matches[0]
        if item.get("credential") != credential_id:
            raise SetupError(f"Existing model is linked to another credential: {name}")
        return item
    return api.call("POST", "/api/models", {
        "name": name,
        "provider": provider,
        "type": model_type,
        "credential": credential_id,
    })


def speaker_profile(api: API, tts_id: str):
    name = "Nexus Local Test Speaker"
    path = "/api/speaker-profiles/" + quote(name, safe="")
    try:
        item = api.call("GET", path)
    except SetupError as error:
        if "-> 404:" not in str(error):
            raise
        item = None
    expected_speakers = [{
        "name": "Host",
        "voice_id": "af_heart",
        "backstory": "Local Nexus acceptance-test host.",
        "personality": "Clear, restrained and factual.",
    }]
    if item:
        if item.get("voice_model") != tts_id or item.get("speakers") != expected_speakers:
            raise SetupError("Existing Nexus speaker profile conflicts with the pinned local contract")
        return item
    return api.call("POST", "/api/speaker-profiles", {
        "name": name,
        "description": "Nexus local podcast acceptance profile.",
        "voice_model": tts_id,
        "speakers": expected_speakers,
    })


def episode_profile(api: API, language_id: str, speaker_id: str):
    name = "Nexus Local Test Episode"
    path = "/api/episode-profiles/" + quote(name, safe="")
    try:
        item = api.call("GET", path)
    except SetupError as error:
        if "-> 404:" not in str(error):
            raise
        item = None
    payload = {
        "name": name,
        "description": "Short fully local Nexus podcast acceptance profile.",
        "speaker_config": speaker_id,
        "outline_llm": language_id,
        "transcript_llm": language_id,
        "language": "en-US",
        "default_briefing": "Create a concise factual podcast from the selected material. Do not invent sources or claims.",
        "num_segments": 3,
        "max_tokens": 1200,
    }
    if item:
        checks = {
            "speaker_config": speaker_id,
            "outline_llm": language_id,
            "transcript_llm": language_id,
            "language": "en-US",
            "num_segments": 3,
            "max_tokens": 1200,
        }
        if any(item.get(key) != value for key, value in checks.items()):
            raise SetupError("Existing Nexus episode profile conflicts with the pinned local contract")
        return item
    return api.call("POST", "/api/episode-profiles", payload)



def transformation(api: API, language_id: str):
    name = "nexus_strict_cognitive_v1"
    prompt = (
        "Return ONLY one valid JSON object, with no Markdown fences and no text before or after it. "
        "Use exactly these keys: title, summary, quotes. "
        "title must be a non-empty string up to 150 characters. "
        "summary must be a factual summary grounded only in the supplied input, up to 3000 characters. "
        "quotes must be an array containing 1 to 5 exact verbatim substrings copied from the supplied input; "
        "each quote must be non-empty and at most 800 characters. "
        "Do not invent facts. Do not paraphrase inside quotes. "
        "The complete response must be parseable by a strict JSON parser."
    )
    items = api.call("GET", "/api/transformations")
    matches = [item for item in items if item.get("name") == name]
    if len(matches) > 1:
        raise SetupError("Duplicate Nexus cognitive transformation")
    expected = {
        "title": "Nexus strict cognitive JSON v1",
        "description": "Bounded local transformation for the Nexus interpret adapter.",
        "prompt": prompt,
        "apply_default": False,
        "model_id": language_id,
    }
    if matches:
        item = matches[0]
        if any(item.get(key) != value for key, value in expected.items()):
            raise SetupError("Existing Nexus cognitive transformation conflicts with the pinned contract")
        return item
    return api.call("POST", "/api/transformations", {"name": name, **expected})

def documentary_transformation(api: API, language_id: str):
    """Pinned storyboard/script contract consumed by the local documentary bridge."""
    name = "nexus_documentary_script_v1"
    prompt = (
        "Return ONLY one valid JSON object, with no Markdown fences and no text before or after it. "
        "Use exactly these keys: title, script, scenes. "
        "Write the narration in European Portuguese unless the input explicitly requests another language. "
        "title must be a non-empty string up to 180 characters. "
        "script must be a factual documentary narration grounded only in the supplied input; do not invent sources, "
        "quotes, dates, names or claims. Aim for the requested duration when the input supplies one. "
        "scenes must be an array with 6 to 40 objects. Every scene must use exactly these keys: visual_prompt, seconds. "
        "visual_prompt must be a concise English visual description suitable for a documentary still image; "
        "it must not assert facts absent from the supplied input. seconds must be an integer from 3 to 15. "
        "The sum of scene seconds should approximately match the narration duration. "
        "The complete response must be parseable by a strict JSON parser."
    )
    items = api.call("GET", "/api/transformations")
    matches = [item for item in items if item.get("name") == name]
    if len(matches) > 1:
        raise SetupError("Duplicate Nexus documentary transformation")
    expected = {
        "title": "Nexus documentary script JSON v1",
        "description": "Bounded local documentary handoff for MoneyPrinterTurbo.",
        "prompt": prompt,
        "apply_default": False,
        "model_id": language_id,
    }
    if matches:
        item = matches[0]
        if any(item.get(key) != value for key, value in expected.items()):
            raise SetupError("Existing Nexus documentary transformation conflicts with the pinned contract")
        return item
    return api.call("POST", "/api/transformations", {"name": name, **expected})


def product_plan_transformation(api: API, language_id: str):
    """Shared bounded plan contract for video/podcast/visual-podcast routes."""
    name = "nexus_product_plan_v1"
    prompt = (
        "Return ONLY one valid JSON object, with no Markdown fences and no text before or after it. "
        "The input begins with ROUTE: video, podcast or visual_podcast and then SOURCE:. "
        "Use exactly these keys: title, body, steps, quotes. "
        "Write in European Portuguese unless the source explicitly requests another language. "
        "title: non-empty string up to 150 characters. "
        "body: the main usable script/content for the requested route, grounded only in SOURCE. "
        "steps: array of 2 to 40 concise microtasks; for video use shot/storyboard beats, for podcast use episode segments, "
        "for visual_podcast use episode segments with matching visual beats. "
        "quotes: array of 1 to 5 exact verbatim substrings copied only from SOURCE, each up to 800 characters. "
        "Do not invent facts, sources, quotations, dates, names or claims. "
        "The complete response must be parseable by a strict JSON parser."
    )
    items = api.call("GET", "/api/transformations")
    matches = [item for item in items if item.get("name") == name]
    if len(matches) > 1:
        raise SetupError("Duplicate Nexus product-plan transformation")
    expected = {
        "title": "Nexus product plan JSON v1",
        "description": "Bounded local planning handoff for public product routes.",
        "prompt": prompt,
        "apply_default": False,
        "model_id": language_id,
    }
    if matches:
        item = matches[0]
        if any(item.get(key) != value for key, value in expected.items()):
            raise SetupError("Existing Nexus product-plan transformation conflicts with the pinned contract")
        return item
    return api.call("POST", "/api/transformations", {"name": name, **expected})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://127.0.0.1:5055")
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--authorize-install", action="store_true")
    args = parser.parse_args()
    if not args.authorize_install:
        raise SetupError("NEXUS_INSTALL_AUTHORIZATION_REQUIRED")
    values = read_env(args.env_file)
    password = values.get("OPEN_NOTEBOOK_PASSWORD", "")
    if not password:
        raise SetupError("OPEN_NOTEBOOK_PASSWORD is required for the local installation contract")
    api = API(args.api, password)

    language_credential = credential(api, "openai_compatible", "Nexus Local Language", {
        "name": "Nexus Local Language",
        "provider": "openai_compatible",
        "modalities": ["language"],
        "api_key": "ARCHIVE_REDACTED_01",
        "base_url": "http://127.0.0.1:18081/v1",
    })
    embedding_credential = credential(api, "openai_compatible", "Nexus Local Embedding", {
        "name": "Nexus Local Embedding",
        "provider": "openai_compatible",
        "modalities": ["embedding"],
        "api_key": "ARCHIVE_REDACTED_01",
        "base_url": "http://127.0.0.1:18082/v1",
    })
    speech = credential(api, "openai_compatible", "Nexus Local Speech", {
        "name": "Nexus Local Speech",
        "provider": "openai_compatible",
        "modalities": ["text_to_speech"],
        "api_key": "ARCHIVE_REDACTED_01",
        "base_url": "http://127.0.0.1:8969/v1",
    })

    for item in (language_credential, embedding_credential, speech):
        tested = api.call("POST", f"/api/credentials/{quote(item['id'], safe=':')}/test", {})
        if tested.get("success") is not True:
            raise SetupError(f"Provider test failed for {item['name']}: {tested.get('message')}")

    language = model(
        api,
        name="nexus-qwen3-1.7b",
        provider="openai_compatible",
        model_type="language",
        credential_id=language_credential["id"],
    )
    embedding = model(
        api,
        name="nexus-qwen3-embedding-0.6b",
        provider="openai_compatible",
        model_type="embedding",
        credential_id=embedding_credential["id"],
    )
    tts = model(
        api,
        name="speaches-ai/Kokoro-82M-v1.0-ONNX",
        provider="openai_compatible",
        model_type="text_to_speech",
        credential_id=speech["id"],
    )

    defaults = api.call("PUT", "/api/models/defaults", {
        "default_chat_model": language["id"],
        "default_transformation_model": language["id"],
        "large_context_model": language["id"],
        "default_text_to_speech_model": tts["id"],
        "default_embedding_model": embedding["id"],
        "default_tools_model": language["id"],
    })
    expected_defaults = {
        "default_chat_model": language["id"],
        "default_transformation_model": language["id"],
        "large_context_model": language["id"],
        "default_text_to_speech_model": tts["id"],
        "default_embedding_model": embedding["id"],
        "default_tools_model": language["id"],
    }
    if any(defaults.get(key) != value for key, value in expected_defaults.items()):
        raise SetupError("Open Notebook default model assignment did not round-trip")

    settings = api.call("PUT", "/api/settings", {"auto_delete_files": "no"})
    if settings.get("auto_delete_files") != "no":
        raise SetupError("Open Notebook automatic file deletion could not be disabled")

    cognitive = transformation(api, language["id"])
    documentary = documentary_transformation(api, language["id"])
    product_plan = product_plan_transformation(api, language["id"])
    speaker = speaker_profile(api, tts["id"])
    episode = episode_profile(api, language["id"], speaker["id"])

    report = {
        "schema": "nexus.open-notebook-local-config.v1",
        "status": "PASS",
        "providers": {
            "language": {
                "provider": "openai_compatible",
                "runtime": "llama.cpp",
                "credential_id": language_credential["id"],
                "base_url": language_credential.get("base_url"),
            },
            "embedding": {
                "provider": "openai_compatible",
                "runtime": "llama.cpp",
                "credential_id": embedding_credential["id"],
                "base_url": embedding_credential.get("base_url"),
            },
            "speech": {"credential_id": speech["id"], "base_url": speech.get("base_url")},
        },
        "models": {
            "language": {"id": language["id"], "name": language["name"]},
            "embedding": {"id": embedding["id"], "name": embedding["name"]},
            "tts": {"id": tts["id"], "name": tts["name"]},
        },
        "transformation": {"id": cognitive["id"], "name": cognitive["name"]},
        "documentary_transformation": {"id": documentary["id"], "name": documentary["name"]},
        "product_plan_transformation": {"id": product_plan["id"], "name": product_plan["name"]},
        "podcast_profiles": {
            "speaker": {"id": speaker["id"], "name": speaker["name"]},
            "episode": {"id": episode["id"], "name": episode["name"]},
        },
        "auto_delete_files": "no",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("OPEN_NOTEBOOK_LOCAL_CONFIG=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SetupError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
