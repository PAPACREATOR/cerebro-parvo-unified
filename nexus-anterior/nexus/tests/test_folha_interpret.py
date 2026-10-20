"""Read-only Folha HTTP interpretation never creates execution or state."""
import pytest
from urllib.error import HTTPError
from nexus.host import Host
from nexus.tests.test_reverse_flow import http

@pytest.mark.parametrize(("text","intent"), [
    ("@@ Guardar rascunho", "arquivo"),
    ('"" Lista referencias', "fontes"),
    ("?? Pergunta estudo", "perguntar"),
    ("& Rever um capitulo", "trabalhar"),
    ("% 3 + 4", "calcular"),
    ("# Literatura", "tema"),
    ("@ pesquisa local", "web"),
])
def test_seven_prefixes_interpret_read_only(tmp_path, text, intent):
    host=Host(tmp_path)
    with http(host) as call:
        result=call("/api/interpret", {"text":text})
        assert result["intent"] == intent
        assert result["status"] == "RESOLVED"
        assert result["original"] == text
        assert result["execution"] == "NOT_AUTHORIZED"
        assert result["confirmation_required"] is False
        assert call("/api/runs") == []
    assert all(not any((tmp_path/n).iterdir()) for n in ("runs","creative","canonical"))

@pytest.mark.parametrize("value", [
    {"text":"Guarda", "process":"book"},
    {"text":1},
    {},
])
def test_interpret_rejects_unexpected_fields(tmp_path, value):
    host=Host(tmp_path)
    with http(host) as call:
        with pytest.raises(HTTPError) as error:
            call("/api/interpret", value)
        assert error.value.code == 403
        assert call("/api/runs") == []
    assert all(not any((tmp_path/n).iterdir()) for n in ("runs","creative","canonical"))

@pytest.mark.parametrize("text", [
    "Nao guardes o ficheiro.",
    "Guarda esta nota e pesquisa na web.",
    "",
])
def test_uncertain_requests_do_not_execute(tmp_path,text):
    host=Host(tmp_path)
    with http(host) as call:
        result=call("/api/interpret",{"text":text})
        assert result["status"]!="RESOLVED"
        assert result["execution"]=="NOT_AUTHORIZED"
        assert call("/api/runs")==[]
    assert all(not any((tmp_path/n).iterdir()) for n in ("runs","creative","canonical"))
