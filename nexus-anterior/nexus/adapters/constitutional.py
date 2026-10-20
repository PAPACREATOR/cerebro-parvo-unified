"""Strict Markdown object reader owned by Nexus; no external workflow parser."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from nexus.contracts import Blocked, strict_json, validate

KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]{0,63}$")
VALUE = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")


def _frontmatter(text):
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].lstrip("\ufeff").strip() != "---":
        raise Blocked("Metadados nativos ausentes.")
    end = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end = index
            break
    if end is None:
        raise Blocked("Metadados nativos incompletos.")
    body = "".join(lines[1:end]).strip()
    if not body:
        raise Blocked("Metadados nativos vazios.")
    if body.startswith("{"):
        data = strict_json(body)
    else:
        data = {}
        for raw in body.splitlines():
            line = raw.strip()
            if not line or ":" not in line or line.startswith(("!", "&", "*", "{", "[", "-")):
                raise Blocked("Frontmatter fora do subconjunto seguro.")
            key, value = line.split(":", 1)
            key, value = key.strip(), value.strip()
            if not KEY.fullmatch(key) or not VALUE.fullmatch(value) or key in data:
                raise Blocked("Frontmatter fora do subconjunto seguro.")
            data[key] = value
    if not isinstance(data, dict):
        raise Blocked("Frontmatter precisa de ser um objeto.")
    offset = sum(len(item) for item in lines[: end + 1])
    return data, text[offset:]


def read_object(path):
    path = Path(path)
    if path.suffix.lower() != ".md" or path.is_symlink():
        raise Blocked("É necessário um ficheiro Markdown regular.")
    raw = path.read_bytes()
    if len(raw) > 100_000:
        raise Blocked("Objeto demasiado grande.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeError as error:
        raise Blocked("Markdown precisa de UTF-8.") from error
    data, notes = _frontmatter(text)
    validate("multimedia", data)
    return {"nome_ficheiro": path.name, "dados_yaml": data, "notas_markdown": notes}


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(read_object(sys.argv[1]), ensure_ascii=False))
