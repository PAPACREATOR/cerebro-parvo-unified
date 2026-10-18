import tempfile
import os
from nexus import intent, planner, orchestrator


def test_intent_and_orchestrator_simple():
    # intent tests
    r1 = intent.choose_process('Quero criar um podcast visual curto com guião e TTS')
    assert isinstance(r1, dict) and 'process' in r1 and 'confidence' in r1

    r2 = intent.choose_process('Por favor, converte para PDF este documento')
    assert r2['process'] in ('convert_pdf', 'interpret')

    # orchestrator clarification path
    tmp = tempfile.mkdtemp(prefix='test-orch-')
    r = orchestrator.handle_request('', tmp)
    assert r['status'] in ('NEEDS_CLARIFICATION', 'UNKNOWN')
