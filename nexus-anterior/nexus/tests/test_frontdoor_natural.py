"""L1/L2: natural-language and ambiguity matrix for the Front Door."""
import random

import pytest

from nexus.frontdoor import parse


VALID_TEMPLATES = {
    "arquivo": [
        "guarda {body}", "arquiva {body}", "salva {body}", "quero guardar {body}",
    ],
    "web": [
        "pesquisa na web {body}", "procura na internet {body}",
        "pesquisa online {body}", "pesquiza na net {body}",
    ],
    "fontes": [
        "encontra fontes sobre {body}", "procura fontes para {body}",
        "quais são as fontes de {body}", "pesquiza fontes sobre {body}",
    ],
    "trabalhar": [
        "trabalha este texto {body}", "revê {body}", "melhora {body}",
        "reescreve {body}", "corrige {body}",
    ],
    "perguntar": [
        "explica {body}", "responde sobre {body}", "o que é {body}",
        "quem é {body}", "como funciona {body}",
    ],
    "calcular": [
        "calcula {body}", "faz a conta {body}", "quanto é {body}",
        "soma {body}",
    ],
    "tema": [
        "tema {body}", "assunto {body}", "quero falar sobre {body}",
    ],
}


def test_l1_2000_natural_valid_cases():
    rng = random.Random(20261004)
    intents = tuple(VALID_TEMPLATES)
    alphabet = "abcxyz012345 áéç_日本語_-"
    for i in range(2000):
        intent = intents[i % len(intents)]
        template = VALID_TEMPLATES[intent][i % len(VALID_TEMPLATES[intent])]
        body = "".join(rng.choice(alphabet) for _ in range(10 + rng.randrange(40))).strip() or "conteúdo"
        original = template.format(body=body)
        parsed = parse(original)
        assert parsed.status == "RESOLVED", (i, original, parsed)
        assert parsed.intent == intent, (i, original, parsed)
        assert parsed.original == original
        assert parsed.parser == "eliza-rules-v1"
        assert parsed.explicit is False


def test_l2_1500_two_intent_cases_are_unresolved():
    rng = random.Random(4042026)
    intents = tuple(VALID_TEMPLATES)
    for i in range(1500):
        first = intents[i % len(intents)]
        second = intents[(i + 1 + rng.randrange(len(intents) - 1)) % len(intents)]
        if second == first:
            second = intents[(intents.index(first) + 1) % len(intents)]
        # Theme/subject rules are intentionally start-anchored to avoid
        # treating ordinary body words as commands. If theme was selected as
        # the second clause, swap the order so both intents remain detectable.
        if second == "tema" and first != "tema":
            first, second = second, first
        a = VALID_TEMPLATES[first][i % len(VALID_TEMPLATES[first])].format(body="documento alfa")
        b = VALID_TEMPLATES[second][i % len(VALID_TEMPLATES[second])].format(body="documento beta")
        original = a + " e também " + b
        parsed = parse(original)
        assert parsed.status == "UNRESOLVED", (i, first, second, original, parsed)
        assert parsed.intent is None
        assert parsed.original == original


@pytest.mark.parametrize("value", [
    "bom dia",
    "isto é só uma nota",
    "talvez amanhã",
    "não sei o que quero fazer",
    "um texto sem ordem",
    "Nexus",
    "olá mundo",
])
def test_l2_weak_or_chatty_text_is_unresolved(value):
    parsed = parse(value)
    assert parsed.status == "UNRESOLVED"
    assert parsed.intent is None


@pytest.mark.parametrize(("value", "intent"), [
    ("@@ pesquisa na web isto mas guarda como arquivo", "arquivo"),
    ("@ guarda isto depois mas pesquisa agora", "web"),
    ('"" calcula isto e encontra fontes', "fontes"),
    ("& pesquisa online isto e melhora o texto", "trabalhar"),
    ("?? guarda isto mas explica primeiro", "perguntar"),
    ("% procura fontes mas calcula 2+2", "calcular"),
    ("# pesquisa na internet mas o tema é astronomia", "tema"),
])
def test_explicit_prefix_has_priority_over_conflicting_natural_language(value, intent):
    parsed = parse(value)
    assert parsed.status == "RESOLVED"
    assert parsed.intent == intent
    assert parsed.explicit is True
    assert parsed.parser == "prefix-v1"


def test_natural_parser_never_changes_original_bytes():
    value = "  Explica ação 日本語 ç  "
    parsed = parse(value)
    assert parsed.original.encode("utf-8") == value.encode("utf-8")
