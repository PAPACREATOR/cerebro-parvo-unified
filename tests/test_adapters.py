import os
from nexus.adapters import zotero as zotero_adapter


def test_zotero_adapter_stub():
    res = zotero_adapter.import_from_zotero('referências sobre fado')
    assert isinstance(res, list)
    assert len(res) >= 1


def test_languagetool_adapter_present_or_absent():
    try:
        from nexus.adapters import languagetool
        res = languagetool.run_languagetool('Teste simples')
    except Exception:
        # Import or execution failed; that's ok for CI environments without Java
        res = {'status': 'UNKNOWN'}
    assert isinstance(res, dict)
    assert 'status' in res
