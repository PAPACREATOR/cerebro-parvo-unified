"""100K realistic ambiguity/noise stress for the natural-language front door."""
import json
import random

import pytest

from nexus.contracts import Blocked
from nexus.natural_bridge import from_markdown, resolve_natural, to_markdown

INTENTS = ["arquivo", "web", "fontes", "trabalhar", "perguntar", "calcular", "tema"]
CLEAR = {
    "arquivo": ["guarda, {body}", "arquiva... {body}", "SALVA   {body}"],
    "web": ["pesquisa!!! na web {body}", "PROCURA   na internet, {body}", "pesquiza... na net {body}"],
    "fontes": ["encontra, fontes sobre {body}", "PROCURA   fontes para {body}", "quais sao as fontes de {body}"],
    "trabalhar": ["reve, {body}", "MELHORA... {body}", "reescreve   {body}"],
    "perguntar": ["explica, {body}", "COMO   funciona {body}", "o que e, {body}"],
    "calcular": ["calcula, {body}", "soma... {body}", "faz   a conta {body}"],
    "tema": ["tema, {body}", "ASSUNTO   {body}", "quero falar sobre, {body}"],
}
COMMAND = {
    "arquivo": "guarda documento alfa",
    "web": "pesquisa na web documento beta",
    "fontes": "encontra fontes sobre documento gama",
    "trabalhar": "melhora documento delta",
    "perguntar": "explica documento epsilon",
    "calcular": "calcula 2+2",
    "tema": "tema astronomia",
}
LT_CASES = [
    ("garda", "guarda", "arquivo", " documento"),
    ("pesqisa", "pesquisa", "web", " na web documento"),
    ("enconra", "encontra", "fontes", " fontes sobre documento"),
    ("corige", "corrige", "trabalhar", " este texto"),
    ("esplica", "explica", "perguntar", " isto"),
    ("calcla", "calcula", "calcular", " 2+2"),
    ("asunto", "assunto", "tema", " astronomia"),
]

def lt_response(text, typo, correction, *, multi=False):
    replacements = [correction, correction + "x"] if multi else [correction]
    return json.dumps({
        "software": {"name": "LanguageTool", "version": "stress"},
        "warnings": {"incompleteResults": False},
        "language": {"code": "pt-PT"},
        "matches": [{
            "message": "Possível erro",
            "offset": 0,
            "length": len(typo),
            "context": {"text": text},
            "replacements": [{"value": item} for item in replacements],
        }],
    }, ensure_ascii=False)

def assert_roundtrip(parsed, original, intent):
    assert parsed.status == "RESOLVED"
    assert parsed.intent == intent
    assert parsed.original == original
    markdown = to_markdown(parsed)
    back = from_markdown(markdown)
    assert back["intent"] == intent
    assert back["text"] == original
    assert back["text"].encode("utf-8") == original.encode("utf-8")

def test_100k_family_a_20000_clear_but_messy_punctuation_spacing_case():
    rng = random.Random(2026100401)
    alphabet = "abcXYZ012345 áéç_日本語_-.:;!?()[]{}"
    for i in range(20000):
        intent = INTENTS[i % len(INTENTS)]
        template = CLEAR[intent][i % len(CLEAR[intent])]
        body = "".join(rng.choice(alphabet) for _ in range(8 + rng.randrange(80))).strip() or "conteudo"
        original = template.format(body=body)
        parsed = resolve_natural(original)
        assert_roundtrip(parsed, original, intent)

def test_100k_family_b_20000_two_real_intents_must_ask_human():
    rng = random.Random(2026100402)
    for i in range(20000):
        first = INTENTS[i % len(INTENTS)]
        second = INTENTS[(i + 1 + rng.randrange(len(INTENTS) - 1)) % len(INTENTS)]
        if second == first:
            second = INTENTS[(INTENTS.index(first) + 1) % len(INTENTS)]
        if second == "tema" and first != "tema":
            first, second = second, first
        original = COMMAND[first] + " ; e também ; " + COMMAND[second]
        parsed = resolve_natural(original)
        assert parsed.status == "ASK_HUMAN", (i, first, second, original, parsed)
        assert parsed.intent is None
        assert parsed.original == original
        with pytest.raises(Blocked):
            to_markdown(parsed)

def test_100k_family_c_20000_typo_cases_resolve_via_languagetool_shadow():
    for i in range(20000):
        typo, correction, intent, tail = LT_CASES[i % len(LT_CASES)]
        punctuation = [",", "...", "!", "??", ""][i % 5]
        original = typo + punctuation + tail + " caso " + str(i)
        raw = lt_response(original, typo, correction)
        parsed = resolve_natural(original, languagetool_raw=raw)
        assert parsed.parser == "languagetool-shadow+eliza-v1", (i, original, parsed)
        assert parsed.shadow is not None
        assert_roundtrip(parsed, original, intent)

def test_100k_family_d_20000_unresolved_cases_accept_only_one_tiny_intent_hint():
    for i in range(20000):
        intent = INTENTS[i % len(INTENTS)]
        original = "faz la isto, por favor... caso " + str(i) + " 日本語"
        parsed = resolve_natural(original, tiny_hints=[intent])
        assert parsed.parser == "tiny-hint-v1"
        assert parsed.explicit is False
        assert_roundtrip(parsed, original, intent)

def test_100k_family_e_20000_conflict_invalid_help_falls_back_to_human():
    modes = ("none", "conflict", "invalid", "empty", "lt-multiple")
    for i in range(20000):
        mode = modes[i % len(modes)]
        if mode == "lt-multiple":
            typo, correction, _, tail = LT_CASES[i % len(LT_CASES)]
            original = typo + tail + " caso " + str(i)
            parsed = resolve_natural(original, languagetool_raw=lt_response(original, typo, correction, multi=True))
        elif mode == "conflict":
            original = "faz la isto caso " + str(i)
            parsed = resolve_natural(original, tiny_hints=["web", "trabalhar"])
        elif mode == "invalid":
            original = "faz la isto caso " + str(i)
            parsed = resolve_natural(original, tiny_hints=["canonical"])
        elif mode == "empty":
            original = "faz la isto caso " + str(i)
            parsed = resolve_natural(original, tiny_hints=[])
        else:
            original = "fa...z   la, is-to?? caso " + str(i)
            parsed = resolve_natural(original)
        assert parsed.status == "ASK_HUMAN", (i, mode, original, parsed)
        assert parsed.intent is None
        assert parsed.original == original
        assert parsed.parser == "human-clarification-v1"
        with pytest.raises(Blocked):
            to_markdown(parsed)

def test_tiny_hint_type_and_authority_injection_never_bypass_contract():
    with pytest.raises(TypeError):
        resolve_natural("faz la isto", tiny_hints={"intent": "web"})
    for hints in [["canonical"], ["approve"], ["admin"], ["web", "canonical"]]:
        parsed = resolve_natural("faz la isto", tiny_hints=hints)
        assert parsed.status == "ASK_HUMAN"
        assert parsed.intent is None
