import itertools
import json
from pathlib import Path

import pytest

from nexus.adapters.constitutional import read_object
from nexus.contracts import Blocked, ROOT

FIELDS = ("tipo", "familia", "tribo", "dominio", "lab")
BAD = [None, True, False, 0, 1, -1, {}, [], ["som"], "", " ",
       "../canonical", "CANONICAL", "$(whoami)", "x" * 129]
NOTES = ["", "# Intenção\nSom e imagem.", "Notas com ação, órgão e coração.",
         "```powershell\nRemove-Item canonical\n```", "---\nNotas com separador."]
NAMES = ["som", "imagem", "ação", "órgão", "espaço livre", "a.b", "漢字", "ÁUDIO", "01", "rascunho"]


def metadata(tribe):
    return dict(tipo="proposta", familia="multimedia", tribo=tribe,
                dominio="creative", lab="windows")


def document(path, data, notes="", variant=0):
    newline = "\r\n" if variant % 2 else "\n"
    bom = "\ufeff" if variant >= 4 else ""
    closing = "---  " if variant in (2, 3) else "---"
    text = bom + "---" + newline + json.dumps(data, ensure_ascii=False) + newline + closing + newline + notes
    path.write_bytes(text.encode("utf-8"))
    return path


@pytest.mark.parametrize("tribe,notes,name", list(itertools.product(("som", "imagem"), NOTES, NAMES)))
def test_valid_contract_100(tmp_path, tribe, notes, name):
    path = document(tmp_path / (name + ".md"), metadata(tribe), notes)
    result = read_object(path)
    assert result == {"nome_ficheiro": path.name, "dados_yaml": metadata(tribe), "notas_markdown": notes}
    assert not (tmp_path / "canonical").exists()


@pytest.mark.parametrize("tribe,field,bad,variant", list(itertools.product(("som", "imagem"), FIELDS, BAD, range(6))))
def test_invalid_contract_900(tmp_path, tribe, field, bad, variant):
    data = metadata(tribe)
    data[field] = bad
    path = document(tmp_path / "objeto.md", data, "# Candidato", variant)
    with pytest.raises(Blocked):
        read_object(path)
    assert not (tmp_path / "canonical").exists()


@pytest.mark.parametrize("field", FIELDS)
def test_required_fields(tmp_path, field):
    data = metadata("som")
    del data[field]
    with pytest.raises(Blocked):
        read_object(document(tmp_path / "objeto.md", data))


@pytest.mark.parametrize("field", ["approval_id", "command", "capabilities", "canonical", "process"])
def test_document_cannot_grant_authority(tmp_path, field):
    data = metadata("imagem")
    data[field] = "self-authorized"
    with pytest.raises(Blocked):
        read_object(document(tmp_path / "objeto.md", data))


@pytest.mark.parametrize("raw", [b"# No metadata", b"```yaml\ntipo: proposta\n```", b"\xff",
    b"---\ntipo: proposta\ntipo: proposta\n---\n", b"---\n!!python/object:danger {}\n---\n", b"x" * 100001], ids=["missing", "fenced", "encoding", "duplicate", "tag", "oversize"])
def test_malformed_objects(tmp_path, raw):
    path = tmp_path / "objeto.md"
    path.write_bytes(raw)
    with pytest.raises(Blocked):
        read_object(path)


@pytest.mark.parametrize("tribe", ["som", "imagem"])
def test_python_reader_reads_family(tribe):
    path = ROOT / "families/multimedia" / (tribe + ".md")
    result = read_object(path)
    assert result["dados_yaml"]["tribo"] == tribe
    assert result["nome_ficheiro"] == path.name
