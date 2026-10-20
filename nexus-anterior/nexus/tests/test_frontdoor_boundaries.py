"""L4: Front Door boundary and malformed-input cases."""
import pytest

from nexus.frontdoor import MAX_TEXT_CHARS, parse


def test_l4_250_exact_character_limit_preserves_input():
    for i in range(250):
        prefix = "@@ "
        body = ("á" if i % 2 else "x") * (MAX_TEXT_CHARS - len(prefix))
        original = prefix + body
        assert len(original) == MAX_TEXT_CHARS
        parsed = parse(original)
        assert parsed.status == "RESOLVED"
        assert parsed.intent == "arquivo"
        assert parsed.original == original


def test_l4_250_one_over_limit_is_blocked():
    for i in range(250):
        original = ("x" if i % 2 else "á") * (MAX_TEXT_CHARS + 1)
        parsed = parse(original)
        assert parsed.status == "BLOCKED"
        assert parsed.original == original
        assert parsed.intent is None


def test_l4_250_control_character_inputs_are_blocked():
    controls = [chr(i) for i in range(32) if chr(i) not in "\t\n\r"]
    for i in range(250):
        control = controls[i % len(controls)]
        original = "@@ guardar" + control + "segredo-" + str(i)
        parsed = parse(original)
        assert parsed.status == "BLOCKED"
        assert parsed.original == original
        assert parsed.intent is None


def test_l4_250_unicode_and_newline_variants_preserve_original():
    variants = [
        "  # ação\nsegunda linha 日本語",
        "\t?? explica\r\nação ç",
        "\n& melhora\ntexto com áéí",
        "  @ pesquisa na web\nNFKC：ＡＢＣ",
    ]
    for i in range(250):
        original = variants[i % len(variants)] + f" {i}"
        parsed = parse(original)
        assert parsed.status == "RESOLVED"
        assert parsed.original.encode("utf-8") == original.encode("utf-8")


@pytest.mark.parametrize("value", [None, 1, 1.5, True, b"texto", [], {}, object()])
def test_l4_non_string_types_raise_type_error(value):
    with pytest.raises(TypeError):
        parse(value)
