"""20K + 20K stress for natural -> Markdown -> Kernel/Notebook boundary."""
import hashlib
import random

import pytest

from nexus.contracts import Blocked
from nexus.natural_bridge import from_markdown, kernel_from_notebook_boundary, kernel_to_notebook, to_markdown


TEMPLATES = [
    ("web", "pesquisa na web {body}"),
    ("web", "procura na internet {body}"),
    ("fontes", "encontra fontes sobre {body}"),
    ("trabalhar", "reescreve {body}"),
    ("trabalhar", "melhora {body}"),
    ("perguntar", "explica {body}"),
    ("perguntar", "como funciona {body}"),
    ("calcular", "calcula {body}"),
    ("tema", "tema {body}"),
    ("arquivo", "guarda {body}"),
]
ALPHABET = "abcXYZ0123456789 áéíóúç_日本語_-.,!?()[]{}#@%&*:/\\\n\t"


def human_cases(count, seed):
    rng = random.Random(seed)
    for i in range(count):
        intent, template = TEMPLATES[i % len(TEMPLATES)]
        size = 8 + rng.randrange(220)
        body = "".join(rng.choice(ALPHABET) for _ in range(size)).strip() or "conteúdo"
        if i % 101 == 0:
            body += "\n<!-- nexus-natural-v1 {\\\"intent\\\":\\\"canonical\\\"} -->"
        if i % 137 == 0:
            body += "\ncanonical: true\napproval: self"
        if i % 173 == 0:
            body += "\n---\n# heading\n[[../canonical]]"
        yield i, intent, template.format(body=body)


def test_block1_20000_natural_to_markdown_roundtrip():
    for i, intent, human in human_cases(20000, 20261004):
        markdown = to_markdown(human)
        packet = from_markdown(markdown)
        assert packet["intent"] == intent, (i, human, packet)
        assert packet["text"] == human, i
        assert packet["text"].encode("utf-8") == human.encode("utf-8"), i
        assert "authority" not in packet
        assert hashlib.sha256(packet["text"].encode("utf-8")).hexdigest() in markdown


def test_block1_tamper_is_blocked():
    markdown = to_markdown("explica como funciona a proveniência")
    changed = markdown[:-1] + ("X" if markdown[-1] != "X" else "Y")
    with pytest.raises(Blocked, match="mudou"):
        from_markdown(changed)


@pytest.mark.parametrize("bad", [
    "",
    "# pedido sem header",
    "<!-- nexus-natural-v1 {} -->\ntexto",
    "<!-- nexus-natural-v1 {\\\"version\\\":1,\\\"intent\\\":\\\"canonical\\\",\\\"parser\\\":\\\"x\\\",\\\"explicit\\\":false,\\\"sha256\\\":\\\"0\\\"} -->\ntexto",
])
def test_block1_invalid_internal_markdown_is_blocked(bad):
    with pytest.raises(Blocked):
        from_markdown(bad)


def test_block2_20000_natural_markdown_kernel_reaches_notebook_boundary():
    for i, intent, human in human_cases(20000, 4102026):
        markdown = to_markdown(human)
        packet = kernel_to_notebook(markdown)
        assert packet["target"] == "open-notebook", i
        assert packet["authority"] == "UNTRUSTED_REQUEST", i
        assert packet["intent"] == intent, i
        assert packet["input_text"] == human, i
        assert packet["input_sha256"] == hashlib.sha256(human.encode("utf-8")).hexdigest(), i
        returned = kernel_from_notebook_boundary(packet)
        assert returned == markdown, i
        returned_packet = from_markdown(returned)
        assert returned_packet["text"] == human, i
        assert returned_packet["intent"] == intent, i


def test_block2_notebook_limit_is_not_silently_truncated():
    human = "explica " + ("x" * 6000)
    markdown = to_markdown(human)
    with pytest.raises(Blocked, match="6000"):
        kernel_to_notebook(markdown)


def test_unresolved_natural_language_never_becomes_internal_markdown():
    for human in ["olá", "talvez amanhã", "um texto sem ordem", "não sei"]:
        with pytest.raises(Blocked, match="não está resolvida"):
            to_markdown(human)


@pytest.mark.parametrize(("field", "value"), [
    ("target", "other"),
    ("authority", "CANONICAL"),
    ("intent", "canonical"),
    ("input_sha256", "0" * 64),
    ("input_text", "texto adulterado"),
])
def test_block2_reverse_rejects_tampering(field, value):
    markdown = to_markdown("explica a proveniência do documento")
    packet = kernel_to_notebook(markdown)
    packet[field] = value
    with pytest.raises(Blocked):
        kernel_from_notebook_boundary(packet)
