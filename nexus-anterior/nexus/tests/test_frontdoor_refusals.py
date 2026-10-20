"""Human refusals and quoted data must survive advisory interpretation.

These are parser/bridge contracts, not an integrated Folha acceptance gate.
"""
import json
from pathlib import Path
import subprocess
import sys

import pytest

from nexus.contracts import Blocked
from nexus.frontdoor import parse, parse_with_languagetool
from nexus.natural_bridge import resolve_natural, resolve_natural_with_tiny, to_markdown
from nexus.tests.test_frontdoor_languagetool_shadow import lt_response


REFUSALS = [
    ("Não guarda esta nota.", "arquivo"),
    ("NAO ARQUIVA este documento.", "arquivo"),
    ("Nunca salva este original.", "arquivo"),
    ("Não quero que guardes esta nota.", "arquivo"),
    ("Jamais calcula estes valores.", "calcular"),
    ("Não pesquisa na web este texto.", "web"),
    ("Não corrige esta frase.", "trabalhar"),
    ('O documento contém "guarda este texto".', "arquivo"),
    ("O texto diz «corrige este parágrafo».", "trabalhar"),
    ("O texto diz «guarda esta nota.", "arquivo"),
    ("O texto diz “corrige este parágrafo.", "trabalhar"),
    ('O documento contém "calcula estes valores.', "calcular"),
    ("A palavra guarda aparece no documento.", "arquivo"),
    ("A frase calcula foi citada.", "calcular"),
]


@pytest.mark.parametrize("original,intent", REFUSALS)
def test_refusal_or_quotation_is_not_a_positive_natural_command(original, intent):
    parsed = parse(original)
    assert parsed.status == "UNRESOLVED"
    assert parsed.intent is None
    assert parsed.original.encode("utf-8") == original.encode("utf-8")
    with pytest.raises(Blocked):
        to_markdown(parsed)


@pytest.mark.parametrize("original,intent", REFUSALS)
def test_tiny_hint_cannot_override_refusal_or_turn_quoted_data_into_command(original, intent):
    parsed = resolve_natural(original, tiny_hints=[intent])
    assert parsed.status == "ASK_HUMAN"
    assert parsed.intent is None
    assert parsed.original == original
    with pytest.raises(Blocked):
        to_markdown(parsed)


def test_language_correction_cannot_remove_a_human_refusal():
    original = "Não guarda a nota."
    raw = lt_response(original, 0, 3, ["Agora"])
    parsed = parse_with_languagetool(original, raw)
    assert parsed.status == "UNRESOLVED"
    assert parsed.intent is None
    assert parsed.original == original
    assert parsed.shadow is None
    assert resolve_natural(original, languagetool_raw=raw,
                           tiny_hints=["arquivo"]).status == "ASK_HUMAN"


def test_refusal_does_not_call_the_optional_local_model(monkeypatch):
    def unexpected_call(*_):
        pytest.fail("A refused operation was sent to the model")
    monkeypatch.setattr("nexus.natural_bridge.classify_tiny", unexpected_call)
    parsed = resolve_natural_with_tiny("Não guarda esta nota.", None)
    assert parsed.status == "ASK_HUMAN"
    assert parsed.intent is None


@pytest.mark.parametrize("text", [
    "Guarda esta nota e corrige este texto.",
    "Calcula estes valores e pesquisa na web o resultado.",
])
def test_mixed_deterministic_intents_cannot_be_selected_by_a_model_hint(text):
    parsed = resolve_natural(text, tiny_hints=["arquivo"])
    assert parsed.status == "ASK_HUMAN"
    assert parsed.intent is None


def test_correction_shadow_with_conflicting_intents_still_needs_human():
    original = "garda esta nota e corige este texto."
    assert parse(original).status == "UNRESOLVED"
    raw = json.loads(lt_response(original, 0, 5, ["guarda"]))
    raw["matches"].append({"message": "Gralha", "offset": original.index("corige"),
                           "length": 6, "context": {"text": original},
                           "replacements": [{"value": "corrige"}]})
    parsed = resolve_natural(original, languagetool_raw=raw,
                             tiny_hints=["arquivo"])
    assert parsed.status == "ASK_HUMAN"
    assert parsed.intent is None
    assert parsed.original == original


def test_maximum_length_unclosed_quotes_do_not_stall_clarification():
    # A separate process bounds a potential regex stall without hanging pytest.
    code = (
        "from nexus.natural_bridge import resolve_natural\n"
        "for quote in (chr(171), chr(8220), chr(34)):\n"
        " for text in ('nota '+quote*99995, 'nota '+quote+'a'*99994):\n"
        "  value=resolve_natural(text)\n"
        "  assert value.status=='ASK_HUMAN' and value.original==text\n"
    )
    subprocess.run([sys.executable, "-c", code],
                   cwd=Path(__file__).resolve().parents[2], check=True, timeout=5)


@pytest.mark.parametrize("text,intent", [
    ("Guarda esta nota.", "arquivo"),
    ("Corrige este parágrafo.", "trabalhar"),
    ("Calcula estes valores.", "calcular"),
    ("@@ Não guarda esta nota.", "arquivo"),
    ('?? O documento contém "guarda este texto".', "perguntar"),
])
def test_affirmative_requests_and_explicit_prefix_priority_remain(text, intent):
    parsed = parse(text)
    assert parsed.status == "RESOLVED"
    assert parsed.intent == intent
    assert parsed.original == text
    assert parsed.explicit is text.startswith(("@@", "??"))
