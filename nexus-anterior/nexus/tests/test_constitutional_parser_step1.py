"""Step 1 stress: Nexus-owned frontmatter preserves the accepted contract."""
import random
from pathlib import Path

import pytest

from nexus.adapters.constitutional import read_object
from nexus.contracts import Blocked, validate

BASE = {"tipo":"proposta","familia":"multimedia","tribo":"som","dominio":"creative","lab":"windows"}

def write_case(path, data, notes="", bom=False, newline="\n", closing="---"):
    text = newline.join(["---"] + [f"{k}: {v}" for k, v in data.items()] + [closing]) + newline + notes
    if bom:
        text = "\ufeff" + text
    path.write_bytes(text.encode("utf-8"))
    return path

def test_5000_valid_cases_preserve_contract(tmp_path):
    rng = random.Random(20261004)
    names = ["som.md","imagem.md","ação.md","日本語.md","espaço livre.md"]
    notes = ["", "# Nota\nconteúdo", "ação órgão coração", "---\nseparador no corpo", "dados com canonical=true como texto"]
    keys = list(BASE)
    for i in range(5000):
        data = dict(BASE)
        data["tribo"] = "som" if i % 2 == 0 else "imagem"
        order = list(keys); rng.shuffle(order)
        ordered = {k: data[k] for k in order}
        path = write_case(tmp_path / f"{i:04d}-{names[i % len(names)]}", ordered, notes[i % len(notes)], bom=(i % 3 == 0), newline="\r\n" if i % 4 == 0 else "\n", closing="---  " if i % 5 == 0 else "---")
        result = read_object(path)
        assert result["nome_ficheiro"] == path.name
        assert result["dados_yaml"] == ordered
        assert result["notas_markdown"] == notes[i % len(notes)]

def test_3000_invalid_or_authority_cases_block(tmp_path):
    invalid = [("tipo","autoridade"),("familia","sistema"),("tribo","video"),("dominio","canonical"),("lab","cloud"),("approval_id","self"),("canonical","true"),("process","interpret"),("capabilities","admin"),("allow_ai","true")]
    for i in range(3000):
        data = dict(BASE)
        key, value = invalid[i % len(invalid)]
        data[key] = value
        path = write_case(tmp_path / f"bad-{i}.md", data, "# candidato")
        with pytest.raises((Blocked, ValueError, TypeError, KeyError)):
            read_object(path)

@pytest.mark.parametrize("raw", [
    b"# no frontmatter",
    b"---\n---\nbody",
    b"---\ntipo: proposta\ntipo: proposta\n---\n",
    b"---\n!!python/object:danger {}\n---\n",
    b"---\n&anchor x: y\n---\n",
    b"---\n- list\n---\n",
    b"---\ntipo proposta\n---\n",
    b"\xff",
])
def test_malformed_inputs_block(raw, tmp_path):
    path = tmp_path / "bad.md"
    path.write_bytes(raw)
    with pytest.raises((Blocked, ValueError, UnicodeError, TypeError, KeyError)):
        read_object(path)

def test_oversize_blocks(tmp_path):
    path = tmp_path / "large.md"; path.write_bytes(b"x" * 100001)
    with pytest.raises(Blocked): read_object(path)

def test_symlink_boundary_blocks(tmp_path, monkeypatch):
    path = write_case(tmp_path / "object.md", BASE)
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda self: True if self == path else original(self))
    with pytest.raises(Blocked): read_object(path)

def test_body_preserved_exactly(tmp_path):
    body = "\r\n# Título\r\ntexto 日本語 ç\r\n---\r\nfim"
    path = write_case(tmp_path / "body.md", BASE, body, bom=True, newline="\r\n")
    assert read_object(path)["notas_markdown"] == body
