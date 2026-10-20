"""LanguageTool shadow tests for the Front Door.

LanguageTool is advisory only. The original remains authoritative.
"""
import json
import random

from nexus.frontdoor import parse, parse_with_languagetool


CASES = [
    ("garda", "guarda", "arquivo", " documento"),
    ("pesqisa", "pesquisa", "web", " na web documento"),
    ("enconra", "encontra", "fontes", " fontes sobre documento"),
    ("corige", "corrige", "trabalhar", " este texto"),
    ("esplica", "explica", "perguntar", " isto"),
    ("calcla", "calcula", "calcular", " 2+2"),
    ("asunto", "assunto", "tema", " astronomia"),
]


def lt_response(text, offset, length, replacements, incomplete=False):
    return json.dumps({
        "software": {"name": "LanguageTool", "version": "lab"},
        "warnings": {"incompleteResults": incomplete},
        "language": {"code": "pt-PT"},
        "matches": [{
            "message": "Possível erro ortográfico",
            "offset": offset,
            "length": length,
            "context": {"text": text},
            "replacements": [{"value": value} for value in replacements],
        }],
    }, ensure_ascii=False)


def test_l3_1500_typo_cases_resolve_only_via_shadow():
    rng = random.Random(20261004)
    for i in range(1500):
        typo, correction, intent, tail = CASES[i % len(CASES)]
        suffix = "".join(rng.choice("abc123 áéç_日本語") for _ in range(i % 13))
        original = typo + tail + suffix
        assert parse(original).status == "UNRESOLVED"
        parsed = parse_with_languagetool(
            original,
            lt_response(original, 0, len(typo), [correction]),
        )
        assert parsed.status == "RESOLVED"
        assert parsed.intent == intent
        assert parsed.original == original
        assert parsed.original.encode("utf-8") == original.encode("utf-8")
        assert parsed.shadow != original
        assert parsed.explicit is False


def test_multiple_replacements_do_not_guess():
    original = "garda documento"
    parsed = parse_with_languagetool(
        original,
        lt_response(original, 0, 5, ["guarda", "guardava"]),
    )
    assert parsed.status == "UNRESOLVED"
    assert parsed.intent is None


def test_shadow_cannot_create_explicit_prefix_authority():
    original = "arroba pesquisar"
    parsed = parse_with_languagetool(
        original,
        lt_response(original, 0, 6, ["@"]),
    )
    assert parsed.status == "UNRESOLVED"
    assert parsed.explicit is False
    assert parsed.original == original


def test_invalid_offset_is_ignored_and_never_authorizes():
    original = "garda documento"
    parsed = parse_with_languagetool(
        original,
        lt_response(original, 999, 5, ["guarda"]),
    )
    assert parsed.status == "UNRESOLVED"
    assert parsed.intent is None


def test_incomplete_result_is_ignored():
    original = "garda documento"
    parsed = parse_with_languagetool(
        original,
        lt_response(original, 0, 5, ["guarda"], incomplete=True),
    )
    assert parsed.status == "UNRESOLVED"
    assert parsed.intent is None
