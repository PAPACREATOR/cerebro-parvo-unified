"""Bounded public product-route adapters.

These routes never write Store/Canonical. Video/podcast/visual-podcast consume
one Host-owned OpenNotebook response; music/web only build deterministic
candidate specifications. Book remains delegated to LibreOffice Writer.
"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

from nexus.contracts import Blocked, strict_json


OPEN_NOTEBOOK_BASE = "http://127.0.0.1:5055"
NOTEBOOK_ROUTES = {"video", "podcast", "visual_podcast"}
MAX_HTTP = 200_000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise Blocked("Redirecionamento da bancada proibido.")


def prepare_text(raw: bytes) -> str:
    try:
        text = raw.decode("utf-8")
    except UnicodeError as error:
        raise Blocked("Esta rota aceita texto UTF-8 nesta versão.") from error
    if not text.strip() or len(text) > 12_000 or "\x00" in text:
        raise Blocked("Usa texto até 12000 caracteres nesta rota.")
    return text


def _config(config: dict) -> tuple[str, str, str, str]:
    required = {"base_url", "password", "model_id", "transformation_id"}
    if not isinstance(config, dict) or set(config) != required:
        raise Blocked("Configuração OpenNotebook de produto inválida.")
    base, password, model_id, transformation_id = (
        config["base_url"], config["password"], config["model_id"], config["transformation_id"]
    )
    if base != OPEN_NOTEBOOK_BASE:
        raise Blocked("OpenNotebook fora do localhost autorizado.")
    if not all(isinstance(x, str) and x and "\x00" not in x for x in (password, model_id, transformation_id)):
        raise Blocked("Configuração OpenNotebook de produto inválida.")
    return base, password, model_id, transformation_id


def fetch_plan(source: str, route: str, config: dict) -> dict:
    if route not in NOTEBOOK_ROUTES:
        raise Blocked("Rota OpenNotebook inválida.")
    base, password, model_id, transformation_id = _config(config)
    payload = {
        "model_id": model_id,
        "transformation_id": transformation_id,
        "input_text": f"ROUTE: {route}\n\nSOURCE:\n{source}",
    }
    request = urllib.request.Request(
        base + "/api/transformations/execute",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + password,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(request, timeout=180) as response:
            raw = response.read(MAX_HTTP + 1)
    except Blocked:
        raise
    except Exception as error:
        raise Blocked("OpenNotebook local indisponível para esta rota.") from None
    if len(raw) > MAX_HTTP:
        raise Blocked("Resposta OpenNotebook demasiado grande.")
    envelope = strict_json(raw)
    if not isinstance(envelope, dict) or not isinstance(envelope.get("output"), str):
        raise Blocked("OpenNotebook devolveu uma resposta incompatível.")
    return {
        "output": envelope["output"],
        "model_id": model_id,
        "transformation_id": transformation_id,
    }


def normalize_plan(raw: str, source: str, route: str, model_id: str, transformation_id: str) -> dict:
    if route not in NOTEBOOK_ROUTES:
        raise Blocked("Rota de produto inválida.")
    value = strict_json(raw.encode("utf-8"))
    if not isinstance(value, dict) or set(value) != {"title", "body", "steps", "quotes"}:
        raise Blocked("Plano OpenNotebook com formato inválido.")
    title, body, steps, quotes = value["title"], value["body"], value["steps"], value["quotes"]
    if not isinstance(title, str) or not title.strip() or len(title) > 150:
        raise Blocked("Título de plano inválido.")
    if not isinstance(body, str) or not body.strip() or len(body) > 30_000:
        raise Blocked("Conteúdo de plano inválido.")
    if not isinstance(steps, list) or not 2 <= len(steps) <= 40:
        raise Blocked("Número de microtarefas inválido.")
    if any(not isinstance(step, str) or not step.strip() or len(step) > 1000 for step in steps):
        raise Blocked("Microtarefa inválida.")
    if not isinstance(quotes, list) or not 1 <= len(quotes) <= 5:
        raise Blocked("Evidência de fonte inválida.")
    if any(not isinstance(q, str) or not q or len(q) > 800 or q not in source for q in quotes):
        raise Blocked("O plano contém evidência que não existe na fonte.")
    labels = {
        "video": "Vídeo/documentário",
        "podcast": "Podcast",
        "visual_podcast": "Podcast visual",
    }
    markdown = "# " + title.strip() + "\n\n" + body.strip()
    markdown += "\n\n## Microtarefas\n" + "\n".join(f"- {step.strip()}" for step in steps)
    markdown += "\n\n## Trechos da fonte\n" + "\n".join("> " + q.replace("\n", "\n> ") for q in quotes)
    evidence = json.dumps({
        "route": route,
        "model_id": model_id,
        "transformation_id": transformation_id,
        "quotes": quotes,
    }, ensure_ascii=False, sort_keys=True)
    return {
        "status": "UNKNOWN",
        "outcome": "candidate",
        "title": labels[route] + " — " + title.strip(),
        "markdown": markdown,
        "ai_calls": 1,
        "evidence": [{"capability": "open-notebook/product-plan", "status": "UNKNOWN", "value": evidence}],
    }


def run_open_notebook(input_path, route: str) -> dict:
    source_path = Path(input_path)
    source = prepare_text(source_path.read_bytes())
    response = strict_json((source_path.parent / "product-plan-response.json").read_bytes())
    if not isinstance(response, dict) or set(response) != {"output", "model_id", "transformation_id"}:
        raise Blocked("Resposta preparada de produto inválida.")
    return normalize_plan(
        response["output"], source, route, response["model_id"], response["transformation_id"]
    )


def _sections(text: str) -> dict[str, str]:
    names = {"tema", "letra", "estilo"}
    values = {name: [] for name in names}
    current = None
    for line in text.splitlines():
        match = re.match(r"^\s*(tema|letra|estilo)\s*:\s*(.*)$", line, re.IGNORECASE)
        if match:
            current = match.group(1).lower()
            if match.group(2).strip():
                values[current].append(match.group(2).strip())
        elif current is not None and line.strip():
            values[current].append(line.strip())
    joined = {key: "\n".join(parts).strip() for key, parts in values.items()}
    if any(not joined[key] for key in names):
        raise Blocked("Música requer palavras-chave Tema:, Letra: e Estilo:.")
    if len(joined["tema"]) > 1000 or len(joined["estilo"]) > 1500 or len(joined["letra"]) > 12_000:
        raise Blocked("Pedido musical demasiado grande.")
    return joined


def music_candidate(text: str) -> dict:
    fields = _sections(text)
    prompt = fields["estilo"] + ". Tema: " + fields["tema"]
    spec = json.dumps({"prompt": prompt, "lyrics": fields["letra"]}, ensure_ascii=False, sort_keys=True)
    markdown = (
        "# Música — candidato de produção\n\n"
        "## Tema\n" + fields["tema"] + "\n\n"
        "## Estilo\n" + fields["estilo"] + "\n\n"
        "## Letra\n" + fields["letra"] + "\n\n"
        "## Destino\nACE-Step local. A geração de áudio físico é validada no gate pós-instalação."
    )
    return {
        "status": "UNKNOWN",
        "outcome": "candidate",
        "title": "Música — especificação ACE-Step",
        "markdown": markdown,
        "ai_calls": 0,
        "evidence": [{"capability": "ace-step/production-spec", "status": "UNKNOWN", "value": spec}],
    }


def run_music(input_path) -> dict:
    return music_candidate(prepare_text(Path(input_path).read_bytes()))


def web_candidate(text: str) -> dict:
    text = text.strip()
    if text.lower().startswith("consulta:"):
        query = text.split(":", 1)[1].strip()
    else:
        query = text
    if not query or len(query) > 2000 or "\x00" in query:
        raise Blocked("Consulta web inválida.")
    markdown = (
        "# Pesquisa web — pedido preparado\n\n"
        "Consulta: " + query + "\n\n"
        "A rota está autorizada, mas não inventa fontes: resultados só entram após um fornecedor web real "
        "devolver fontes verificáveis e o Kernel as comparar."
    )
    return {
        "status": "UNKNOWN",
        "outcome": "candidate",
        "title": "Pesquisa web — consulta",
        "markdown": markdown,
        "ai_calls": 0,
        "evidence": [{"capability": "web/query-spec", "status": "UNKNOWN", "value": query}],
    }


def run_web(input_path) -> dict:
    return web_candidate(prepare_text(Path(input_path).read_bytes()))
