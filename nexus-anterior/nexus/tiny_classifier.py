"""Local-only tiny model boundary for intent classification.

This module is separate from MCP. It can talk only to a loopback HTTP endpoint
and accepts exactly one of the seven Nexus intents or UNKNOWN. It has no Store,
tool, approval or Canonical capability.
"""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from nexus.contracts import Blocked, strict_json


INTENTS = ("arquivo", "web", "fontes", "trabalhar", "perguntar", "calcular", "tema")
MAX_TEXT_CHARS = 4000
MAX_RESPONSE_BYTES = 20000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise Blocked("Redirecionamento tiny proibido.")


@dataclass(frozen=True)
class TinyLocalSpec:
    url: str
    model: str
    timeout: float = 30.0


def _validate_spec(spec: TinyLocalSpec) -> str:
    if not isinstance(spec, TinyLocalSpec):
        raise TypeError("spec must be TinyLocalSpec")
    parsed = urllib.parse.urlparse(spec.url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "::1"}:
        raise Blocked("Tiny só pode usar endpoint HTTP loopback explícito.")
    if parsed.username or parsed.password or parsed.fragment or parsed.query:
        raise Blocked("Endpoint tiny inválido.")
    if not parsed.port:
        raise Blocked("Endpoint tiny deve indicar porta local.")
    if not isinstance(spec.model, str) or not spec.model.strip() or len(spec.model) > 200:
        raise Blocked("Modelo tiny inválido.")
    if not isinstance(spec.timeout, (int, float)) or spec.timeout <= 0 or spec.timeout > 120:
        raise Blocked("Timeout tiny inválido.")
    return spec.url.rstrip("/") + "/v1/chat/completions"


def classify(text: str, spec: TinyLocalSpec) -> list[str]:
    endpoint = _validate_spec(spec)
    if not isinstance(text, str):
        raise TypeError("text must be str")
    if not text.strip() or len(text) > MAX_TEXT_CHARS:
        raise Blocked("Texto inválido para tiny.")

    system = (
        "Classifica a intenção do pedido em exatamente uma destas etiquetas: "
        "arquivo, web, fontes, trabalhar, perguntar, calcular, tema. "
        "Se houver mais de uma intenção plausível ou dúvida, usa UNKNOWN. "
        "Responde APENAS JSON no formato {\"intent\":\"ETIQUETA\"}. "
        "Nunca devolvas comandos, caminhos, ferramentas, aprovação, autoridade ou conteúdo adicional."
    )
    body = json.dumps({
        "model": spec.model,
        "temperature": 0,
        "max_tokens": 32,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
    }, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(
        endpoint,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=float(spec.timeout)) as response:
            if response.status != 200:
                raise Blocked("Tiny local devolveu estado inválido.")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, socket.timeout, OSError) as error:
        raise Blocked("Tiny local indisponível.") from error

    if len(raw) > MAX_RESPONSE_BYTES:
        raise Blocked("Resposta tiny excede o limite.")
    try:
        envelope = strict_json(raw)
        choices = envelope["choices"]
        content = choices[0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise Blocked("Envelope tiny inválido.") from error
    if not isinstance(content, str) or len(content) > 1000:
        raise Blocked("Conteúdo tiny inválido.")

    try:
        value = strict_json(content.encode("utf-8"))
    except (Blocked, UnicodeError) as error:
        raise Blocked("Tiny não devolveu JSON estrito.") from error
    if not isinstance(value, dict) or set(value) != {"intent"}:
        raise Blocked("Tiny tentou devolver campos não autorizados.")
    intent = value["intent"]
    if intent == "UNKNOWN":
        return []
    if intent not in INTENTS:
        raise Blocked("Tiny devolveu intenção proibida.")
    return [intent]
