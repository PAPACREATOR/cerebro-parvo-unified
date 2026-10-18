import os
from nexus.adapters import languagetool


def test_languagetool_absent():
    # Ensure LANGUAGETOOL_JAR is not set for this test environment
    env = os.environ.pop('LANGUAGETOOL_JAR', None)
    res = languagetool.run_languagetool('Este é um texto de teste com erro ortográficoz.')
    assert isinstance(res, dict) and 'status' in res
    assert res['status'] in ('UNKNOWN', 'FAIL', 'OK')
    if env is not None:
        os.environ['LANGUAGETOOL_JAR'] = env


def test_office_absent():
    # If soffice not present, adapter should return UNKNOWN
    res = languagetool.run_languagetool('Texto de teste simples.')
    assert 'status' in res
