"""L0: explicit-prefix front-door tests.

1000 deterministic valid cases plus negative/adversarial boundary cases.
"""
import random

import pytest

from nexus.frontdoor import MAX_TEXT_CHARS, PREFIXES, parse_explicit


def test_l0_1000_explicit_prefix_cases():
    rng = random.Random(20261004)
    alphabet = "abcXYZ0123 áéç_日本語_-.!?"
    for i in range(1000):
        prefix, intent = PREFIXES[i % len(PREFIXES)]
        size = 1 + rng.randrange(80)
        body = "".join(rng.choice(alphabet) for _ in range(size)).strip() or "pedido"
        lead = (" ", "  ", "\t", "\n", " \t")[i % 5]
        original = lead + prefix + (" " * (i % 4)) + body
        parsed = parse_explicit(original)
        assert parsed.status == "RESOLVED"
        assert parsed.intent == intent
        assert parsed.original == original
        assert parsed.content == body
        assert parsed.explicit is True
        assert parsed.parser == "prefix-v1"


@pytest.mark.parametrize("value", [
    "",
    " ",
    "\t\n",
    "@@",
    "@@   ",
    '@@\t',
    '""',
    "??",
    "&",
    "%",
    "#",
    "@",
])
def test_l0_empty_or_prefix_only_is_unresolved(value):
    parsed = parse_explicit(value)
    assert parsed.status == "UNRESOLVED"
    assert parsed.original == value


@pytest.mark.parametrize("value", [
    "isto contém @ web mas é texto normal",
    "citação: @@ arquivo",
    "email teste@example.com",
    "100% correto",
    "C# é uma linguagem",
    "a & b",
    'ele escreveu "" fontes no texto',
    "será?? talvez",
])
def test_l0_prefix_inside_data_is_not_command(value):
    parsed = parse_explicit(value)
    assert parsed.status == "UNRESOLVED"
    assert parsed.intent is None
    assert parsed.original == value
    assert parsed.content == value


def test_l0_long_input_blocked_without_truncating_original():
    value = "x" * (MAX_TEXT_CHARS + 1)
    parsed = parse_explicit(value)
    assert parsed.status == "BLOCKED"
    assert parsed.original == value
    assert parsed.content == ""


@pytest.mark.parametrize("value", [None, b"@@ ficheiro", 123, [], {}])
def test_l0_non_text_rejected(value):
    with pytest.raises(TypeError):
        parse_explicit(value)


@pytest.mark.parametrize(("value", "intent"), [
    ("@@ guardar isto", "arquivo"),
    ("@ pesquisar isto", "web"),
    ('"" encontrar fontes', "fontes"),
    ("& trabalhar este texto", "trabalhar"),
    ("?? explica isto", "perguntar"),
    ("% 2+2", "calcular"),
    ("# astronomia", "tema"),
])
def test_l0_all_seven_prefixes(value, intent):
    parsed = parse_explicit(value)
    assert parsed.status == "RESOLVED"
    assert parsed.intent == intent
    assert parsed.original == value


def test_l0_double_at_wins_over_single_at():
    parsed = parse_explicit("@@ arquivo")
    assert parsed.intent == "arquivo"
    assert parsed.content == "arquivo"


def test_l0_double_question_is_command_but_single_question_is_not():
    assert parse_explicit("?? pergunta").intent == "perguntar"
    assert parse_explicit("? pergunta").intent is None


def test_l0_original_is_byte_equivalent_utf8():
    value = "  # ação_日本語_ç"
    parsed = parse_explicit(value)
    assert parsed.original.encode("utf-8") == value.encode("utf-8")
