"""Minimal deterministic Front Door: data-driven rules, no authority."""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from nexus.contracts import ROOT, Blocked, strict_json, validate
from nexus.adapters.languagetool import correction_shadow


_RULES = validate("frontdoor_rules", strict_json((ROOT / "frontdoor_rules.json").read_bytes()))
PREFIXES = tuple((item[0], item[1]) for item in _RULES["prefixes"])
NATURAL_RULES = _RULES["natural_rules"]
CLARIFICATION_PATTERNS = _RULES["clarification_patterns"]
OPERATION_RULES = _RULES["operation_rules"]
MAX_TEXT_CHARS = _RULES["max_text_chars"]
_INLINE_PROOFREAD = re.compile(
    r"\A[ \t]*(?:corrige|corrigir|revê|reve|rever)[ \t]+este[ \t]+texto[ \t]*:(?P<source>[\s\S]*)\Z",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ParsedInput:
    status: str
    intent: str | None
    original: str
    content: str
    parser: str
    explicit: bool
    shadow: str | None = None

    def as_dict(self) -> dict:
        value = {
            "status": self.status,
            "intent": self.intent,
            "original": self.original,
            "content": self.content,
            "parser": self.parser,
            "explicit": self.explicit,
        }
        if self.shadow is not None:
            value["shadow"] = self.shadow
        return value


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).casefold()).strip()


def inline_proofread_source(text: str) -> str | None:
    """Recognize one exact review command; everything after ':' is only data."""
    if not isinstance(text, str):
        raise TypeError("text must be str")
    match = _INLINE_PROOFREAD.fullmatch(text)
    if match is None:
        return None
    source = match.group("source")
    if (not source.strip() or len(source) > 6000
            or any((ord(char) < 32 and char not in "\t\n\r")
                   or 127 <= ord(char) < 160 for char in source)):
        raise Blocked("Escreve depois dos dois-pontos um texto até 6000 caracteres, sem caracteres de controlo.")
    try:
        source.encode("utf-8")
    except UnicodeError as error:
        raise Blocked("O texto de revisão deve ser UTF-8 válido.") from error
    return source


def requires_clarification(text: str) -> bool:
    """Keep refusals, quoted instructions and conflicting intents with humans."""
    normal = _normalise(text)
    return (any(re.search(pattern, normal) for pattern in CLARIFICATION_PATTERNS)
            or sum(any(re.search(pattern, normal) for pattern in patterns)
                   for patterns in NATURAL_RULES.values()) > 1)


def _natural(text: str, *, original: str | None = None, parser="eliza-rules-v1",
             shadow: str | None = None) -> ParsedInput:
    normal = _normalise(text)
    matches = [
        intent for intent, patterns in NATURAL_RULES.items()
        if any(re.search(pattern, normal) for pattern in patterns)
    ]
    source = text if original is None else original
    if len(matches) != 1 or requires_clarification(source) or requires_clarification(text):
        return ParsedInput("UNRESOLVED", None, source, source, parser, False, shadow)
    return ParsedInput("RESOLVED", matches[0], source, source, parser, False, shadow)



def propose_operation(parsed: ParsedInput, *, filename: str, attachment: str) -> str | None:
    """Return one explicitly configured process proposal; never execute it."""
    if type(parsed) is not ParsedInput or parsed.status != "RESOLVED":
        return None
    if not isinstance(filename, str) or not isinstance(attachment, str):
        return None
    if inline_proofread_source(parsed.original) is not None:
        return "proofread" if parsed.intent == "trabalhar" and not filename and not attachment else None
    normal = _normalise(parsed.content)
    matches = []
    for rule in OPERATION_RULES:
        if rule["intent"] != parsed.intent:
            continue
        if rule["requires_attachment"] and (not filename or not attachment):
            continue
        if any(re.search(pattern, normal) for pattern in rule["patterns"]):
            matches.append(rule["process"])
    return matches[0] if len(matches) == 1 else None

def parse_explicit(text: str) -> ParsedInput:
    if not isinstance(text, str):
        raise TypeError("text must be str")
    if len(text) > MAX_TEXT_CHARS or any((ord(c) < 32 and c not in "\t\n\r") or 127 <= ord(c) < 160 for c in text):
        return ParsedInput("BLOCKED", None, text, "", "prefix-v1", False)
    if not text.strip():
        return ParsedInput("UNRESOLVED", None, text, "", "prefix-v1", False)

    candidate = text.lstrip()
    for prefix, intent in PREFIXES:
        if candidate.startswith(prefix):
            content = candidate[len(prefix):].lstrip()
            return ParsedInput(
                "RESOLVED" if content else "UNRESOLVED",
                intent,
                text,
                content,
                "prefix-v1",
                True,
            )
    return ParsedInput("UNRESOLVED", None, text, text, "prefix-v1", False)


def parse(text: str) -> ParsedInput:
    explicit = parse_explicit(text)
    if explicit.status != "UNRESOLVED" or explicit.explicit:
        return explicit
    if inline_proofread_source(text) is not None:
        # The command is bounded by ':'. Never route instructions occurring in
        # the review body, including quoted commands or questions, as actions.
        return ParsedInput("RESOLVED", "trabalhar", text, text, "inline-proofread-v1", False)
    return _natural(text)


def parse_with_languagetool(text: str, raw) -> ParsedInput:
    first = parse(text)
    if first.status != "UNRESOLVED" or first.explicit or requires_clarification(text):
        return first
    try:
        shadow = correction_shadow(text, raw)
    except (Blocked, TypeError, ValueError, KeyError):
        return first
    if shadow == text:
        return first
    return _natural(
        shadow,
        original=text,
        parser="languagetool-shadow+eliza-v1",
        shadow=shadow,
    )
