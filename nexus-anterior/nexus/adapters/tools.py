"""Deterministic verification helpers used by the current Nexus Python/MCP runtime."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from nexus.contracts import strict_json


def hash_python(path):
    try:
        value = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        return {"status": "PASS", "sha256": value, "capability": "python.hashlib"}
    except OSError:
        return {"status": "FAIL", "sha256": None, "capability": "python.hashlib"}


def compare(a, b):
    if a.get("status") == "FAIL" or b.get("status") == "FAIL":
        outcome = "failure"
    elif a.get("status") != "PASS" or b.get("status") != "PASS" or not a.get("sha256") or not b.get("sha256"):
        outcome = "unknown"
    elif a["sha256"] == b["sha256"]:
        outcome = "agreement"
    else:
        outcome = "conflict"
    return {"outcome": outcome, "a": a, "b": b}


def report(data):
    messages = {
        "agreement": "Os dois métodos obtiveram a mesma impressão digital do conteúdo.",
        "conflict": "Os métodos deram resultados diferentes. A divergência foi preservada.",
        "unknown": "Não há informação suficiente para confirmar a comparação.",
        "failure": "Uma das verificações falhou. Os resultados disponíveis foram preservados.",
    }
    outcome = data["comparison"]["outcome"]
    evidence = [
        {"capability": item["capability"], "status": item["status"], "value": item.get("sha256")}
        for item in (data["comparison"]["a"], data["comparison"]["b"])
    ]
    content = "# Verificação de conteúdo\n\n" + messages[outcome]
    content += "\n\nEsta verificação compara os bytes do ficheiro ou do texto. Não confirma a veracidade do conteúdo."
    for i, item in enumerate(evidence, 1):
        content += "\n\nMétodo " + str(i) + ": " + item["status"] + "\n" + (item["value"] or "Sem resultado")
    return {"status": data["status"], "outcome": outcome, "title": "Verificação de conteúdo",
            "markdown": content, "evidence": evidence, "ai_calls": 0}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    mode = sys.argv[1]
    if mode == "hash":
        value = hash_python(sys.argv[2])
    elif mode == "compare":
        data = strict_json(sys.stdin.read())
        value = compare(data["a"], data["b"])
    elif mode == "report":
        value = report(strict_json(sys.stdin.read()))
    else:
        raise SystemExit("Capability unavailable")
    print(json.dumps(value, ensure_ascii=False))
