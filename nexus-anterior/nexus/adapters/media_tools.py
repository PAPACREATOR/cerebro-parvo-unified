"""Bounded health probes for external local multimedia tools.

ACE-Step and Forge are external programs. These probes only verify their local
API surfaces; they do not generate media, mutate Nexus state, or grant authority.
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

from nexus.contracts import Blocked, strict_json


ACE_BASE = "http://127.0.0.1:8001"
FORGE_BASE = "http://127.0.0.1:7861"
MAX_RESPONSE = 1_000_000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise Blocked("Redirecionamento de ferramenta externa proibido.")


def _get_json(base_url: str, path: str):
    if base_url not in (ACE_BASE, FORGE_BASE):
        raise Blocked("Ferramenta externa fora do localhost autorizado.")
    if not isinstance(path, str) or not path.startswith("/") or "://" in path:
        raise Blocked("Caminho de ferramenta externa inválido.")
    request = urllib.request.Request(
        base_url + path,
        method="GET",
        headers={"Accept": "application/json"},
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=8) as response:
            if response.status != 200:
                raise Blocked("Ferramenta externa indisponível.")
            raw = response.read(MAX_RESPONSE + 1)
    except Blocked:
        raise
    except Exception as error:
        raise Blocked("Ferramenta externa indisponível.") from None
    if len(raw) > MAX_RESPONSE:
        raise Blocked("Resposta de ferramenta externa demasiado grande.")
    return strict_json(raw)


def check_ace_step():
    value = _get_json(ACE_BASE, "/health")
    if not isinstance(value, dict) or set(value) != {"data", "code", "error", "timestamp", "extra"}:
        raise Blocked("Resposta ACE-Step incompatível.")
    data = value["data"]
    if (
        value["code"] != 200
        or value["error"] is not None
        or not isinstance(data, dict)
        or data.get("status") != "ok"
        or data.get("service") != "ACE-Step API"
    ):
        raise Blocked("ACE-Step não confirmou saúde.")
    return {
        "tool": "ace-step",
        "status": "PASS",
        "authority": "NONE",
        "endpoint": ACE_BASE,
        "service": "ACE-Step API",
        "version": str(data.get("version", ""))[:40],
        "models_initialized": bool(data.get("models_initialized", False)),
        "llm_initialized": bool(data.get("llm_initialized", False)),
    }


def check_forge():
    options = _get_json(FORGE_BASE, "/sdapi/v1/options")
    samplers = _get_json(FORGE_BASE, "/sdapi/v1/samplers")
    if not isinstance(options, dict) or not isinstance(samplers, list) or not samplers:
        raise Blocked("Resposta Forge incompatível.")
    if not all(isinstance(item, dict) and isinstance(item.get("name"), str) and item["name"] for item in samplers[:32]):
        raise Blocked("Catálogo Forge incompatível.")
    checkpoint = options.get("sd_model_checkpoint")
    if checkpoint is not None and not isinstance(checkpoint, str):
        raise Blocked("Estado Forge incompatível.")
    return {
        "tool": "forge",
        "status": "PASS",
        "authority": "NONE",
        "endpoint": FORGE_BASE,
        "api": "sdapi-v1",
        "sampler_count": len(samplers),
        "checkpoint_configured": bool(checkpoint),
    }
