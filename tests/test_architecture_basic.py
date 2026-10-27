import tempfile
import os

from nexus import intent, orchestrator


def test_intent_chooser_detects_known_processes():
    r1 = intent.choose_process('Quero um podcast visual curto com guião e voz')
    assert r1['process'] == 'visual_podcast'
    assert r1['confidence'] > 0.5

    r2 = intent.choose_process('converte este documento para PDF')
    assert r2['process'] == 'convert_pdf'

    r3 = intent.choose_process('revisa e corrige a escrita')
    assert r3['process'] == 'proofread'


def test_orchestrator_needs_clarification_when_request_is_empty():
    tmp = tempfile.mkdtemp(prefix='orch-empty-')
    res = orchestrator.handle_request('', tmp)
    assert res['status'] in ('NEEDS_CLARIFICATION', 'UNKNOWN')


def test_run_dir_is_created_by_orchestrator():
    tmp = tempfile.mkdtemp(prefix='orch-run-')
    orchestrator.handle_request('revisa este texto', tmp)
    assert os.path.exists(os.path.join(tmp, 'request.json'))
    assert os.path.exists(os.path.join(tmp, 'run.json'))
