import tempfile
import os
from nexus.adapters import convert_pdf
from nexus.adapters import proofread


def test_convert_pdf_adapter():
    tmp = tempfile.mkdtemp(prefix='test-convert-')
    # No input file -> should return UNKNOWN
    res = convert_pdf.convert_pdf_from_run(tmp)
    assert isinstance(res, dict)
    assert 'status' in res
    assert res['status'] in ('OK', 'UNKNOWN', 'FAIL')


def test_proofread_adapter():
    tmp = tempfile.mkdtemp(prefix='test-proof-')
    res = proofread.run_proofread('Este é um texto de teste.', tmp)
    assert isinstance(res, dict)
    assert 'status' in res
    assert res['status'] in ('OK', 'UNKNOWN', 'FAIL')
