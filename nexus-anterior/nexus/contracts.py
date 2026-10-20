"""Strict data boundaries; no workflow execution or reasoning."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class Blocked(ValueError):
    pass


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise Blocked("Campo JSON repetido.")
            result[key] = value
        return result

    def constant(_):
        raise Blocked("Número JSON inválido.")

    def finite_number(text):
        value = float(text)
        if not math.isfinite(value):
            raise Blocked("Número JSON fora do limite.")
        return value

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant, parse_float=finite_number)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise Blocked("JSON inválido.") from error


def validate(name, value):
    from jsonschema import Draft202012Validator

    schema = strict_json((ROOT / "schemas" / (name + ".json")).read_bytes())
    if next(Draft202012Validator(schema).iter_errors(value), None):
        raise Blocked("Os dados não cumprem o contrato " + name + ".")
    return value


def load_policy(root=ROOT):
    policy = strict_json((root / "laws/policy.json").read_bytes())
    expected = {
        "version": "1.0", "canonical_gate": "human_required",
        "automatic_deletion": False, "ai_authority": False,
        "processes": ["verify", "interpret", "proofread", "convert_pdf", "video", "podcast", "visual_podcast", "book", "music", "web"], "max_input_bytes": 2097152,
    }
    if policy != expected or not (root / "laws/CONSTITUTION.md").read_text("utf-8").strip():
        raise Blocked("Leis ausentes ou incompatíveis com este Host.")
    return policy
