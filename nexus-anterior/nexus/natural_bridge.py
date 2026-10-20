"""Natural language -> internal Markdown -> bounded Kernel handoff.

The Markdown header carries no authority. It only binds the ELIZA parse to the
exact human text. Kernel/Store remain the authority for IDs, state, provenance
and Human Gate.
"""
from __future__ import annotations

import hashlib
import json
import re

from nexus.contracts import Blocked
from nexus.frontdoor import ParsedInput, parse, parse_with_languagetool, requires_clarification
from nexus.adapters.notebook import prepare_source
from nexus.tiny_classifier import TinyLocalSpec, classify as classify_tiny

HEADER_RE = re.compile(r"\A<!-- nexus-natural-v1 (\{[^\n]*\}) -->\n", re.ASCII)
INTENTS = {"arquivo", "web", "fontes", "trabalhar", "perguntar", "calcular", "tema"}


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def to_markdown(value: str | ParsedInput) -> str:
    parsed = parse(value) if isinstance(value, str) else value
    if not isinstance(parsed, ParsedInput):
        raise TypeError("value must be text or ParsedInput")
    if parsed.status != "RESOLVED" or parsed.intent not in INTENTS:
        raise Blocked("A intenção humana ainda não está resolvida.")
    meta = {
        "version": 1,
        "intent": parsed.intent,
        "parser": parsed.parser,
        "explicit": parsed.explicit,
        "sha256": _digest(parsed.original),
    }
    header = json.dumps(meta, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "<!-- nexus-natural-v1 " + header + " -->\n" + parsed.original


def from_markdown(markdown: str) -> dict:
    if not isinstance(markdown, str):
        raise TypeError("markdown must be str")
    match = HEADER_RE.match(markdown)
    if match is None:
        raise Blocked("Markdown interno sem cabeçalho Nexus válido.")
    try:
        meta = json.loads(match.group(1))
    except (ValueError, TypeError) as error:
        raise Blocked("Cabeçalho Nexus inválido.") from error
    if not isinstance(meta, dict) or set(meta) != {"version", "intent", "parser", "explicit", "sha256"}:
        raise Blocked("Cabeçalho Nexus inválido.")
    if meta["version"] != 1 or meta["intent"] not in INTENTS:
        raise Blocked("Cabeçalho Nexus incompatível.")
    if not isinstance(meta["parser"], str) or not meta["parser"] or len(meta["parser"]) > 100:
        raise Blocked("Parser Nexus inválido.")
    if type(meta["explicit"]) is not bool:
        raise Blocked("Marca de intenção explícita inválida.")
    original = markdown[match.end():]
    if _digest(original) != meta["sha256"]:
        raise Blocked("O texto humano mudou depois da interpretação.")
    return {"intent": meta["intent"], "parser": meta["parser"], "explicit": meta["explicit"], "text": original}


def kernel_to_notebook(markdown: str) -> dict:
    """Validate ELIZA Markdown and prepare exact human text for Notebook."""
    packet = from_markdown(markdown)
    source = prepare_source(packet["text"].encode("utf-8"))
    return {
        "intent": packet["intent"],
        "parser": packet["parser"],
        "explicit": packet["explicit"],
        "input_text": source,
        "input_sha256": _digest(source),
        "target": "open-notebook",
        "authority": "UNTRUSTED_REQUEST",
    }


def kernel_from_notebook_boundary(packet: dict) -> str:
    """Reverse the bounded Notebook handoff back to the exact internal Markdown."""
    required = {"intent", "parser", "explicit", "input_text", "input_sha256", "target", "authority"}
    if not isinstance(packet, dict) or set(packet) != required:
        raise Blocked("Pacote de retorno Notebook inválido.")
    if packet["target"] != "open-notebook" or packet["authority"] != "UNTRUSTED_REQUEST":
        raise Blocked("Pacote Notebook com destino ou autoridade inválidos.")
    if packet["intent"] not in INTENTS:
        raise Blocked("Intenção Notebook inválida.")
    if not isinstance(packet["parser"], str) or not packet["parser"] or len(packet["parser"]) > 100:
        raise Blocked("Parser Notebook inválido.")
    if type(packet["explicit"]) is not bool or not isinstance(packet["input_text"], str):
        raise Blocked("Pacote Notebook inválido.")
    if _digest(packet["input_text"]) != packet["input_sha256"]:
        raise Blocked("O texto mudou durante a passagem pelo Notebook.")
    meta = {
        "version": 1,
        "intent": packet["intent"],
        "parser": packet["parser"],
        "explicit": packet["explicit"],
        "sha256": packet["input_sha256"],
    }
    header = json.dumps(meta, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    markdown = "<!-- nexus-natural-v1 " + header + " -->\n" + packet["input_text"]
    from_markdown(markdown)
    return markdown


def resolve_natural(text: str, *, languagetool_raw=None, tiny_hints=None) -> ParsedInput:
    """Conservative escalation: ELIZA -> LanguageTool shadow -> tiny hint -> human.

    Tiny hints classify intent only. They never carry process names, authority,
    approval, capabilities or Canonical state.
    """
    first = parse(text)
    if first.status != "UNRESOLVED" or first.explicit:
        return first

    needs_human = requires_clarification(text)
    if languagetool_raw is not None and not needs_human:
        second = parse_with_languagetool(text, languagetool_raw)
        if second.status == "RESOLVED":
            return second
        needs_human = second.shadow is not None and requires_clarification(second.shadow)

    if tiny_hints is not None and not needs_human:
        if not isinstance(tiny_hints, (list, tuple)):
            raise TypeError("tiny_hints must be a list or tuple")
        valid = [item for item in tiny_hints if isinstance(item, str) and item in INTENTS]
        unique = set(valid)
        if len(unique) == 1 and len(valid) == len(tiny_hints) and len(valid) > 0:
            return ParsedInput(
                "RESOLVED",
                valid[0],
                text,
                text,
                "tiny-hint-v1",
                False,
            )

    return ParsedInput(
        "ASK_HUMAN",
        None,
        text,
        text,
        "human-clarification-v1",
        False,
    )


def resolve_natural_with_tiny(
    text: str,
    tiny_spec: TinyLocalSpec,
    *,
    languagetool_raw=None,
) -> ParsedInput:
    """ELIZA -> LanguageTool shadow -> local tiny -> human clarification."""
    deterministic = resolve_natural(text, languagetool_raw=languagetool_raw)
    if deterministic.status != "ASK_HUMAN":
        return deterministic
    if requires_clarification(text):
        return deterministic
    if languagetool_raw is not None:
        shadow = parse_with_languagetool(text, languagetool_raw).shadow
        if shadow is not None and requires_clarification(shadow):
            return deterministic
    try:
        hints = classify_tiny(text, tiny_spec)
    except Blocked:
        hints = []
    return resolve_natural(
        text,
        languagetool_raw=languagetool_raw,
        tiny_hints=hints,
    )
