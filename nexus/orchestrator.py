import os
import json
import time
from nexus import intent, planner


def handle_request(text: str, run_dir: str, confidence_threshold: float = 0.5):
    """Top-level orchestrator for a single user request.

    - decides the process using intent.choose_process
    - if confidence < threshold returns NEEDS_CLARIFICATION
    - otherwise calls planner.plan_and_execute (which enforces TUDO-OU-NADA)
    - writes run.json with metadata and returns the planner result
    """
    os.makedirs(run_dir, exist_ok=True)
    # persist raw request
    try:
        with open(os.path.join(run_dir, 'request.json'), 'w', encoding='utf-8') as f:
            json.dump({'text': text, 'time': time.time()}, f, ensure_ascii=False)
    except Exception:
        pass

    sel = intent.choose_process(text)
    process = sel.get('process')
    confidence = sel.get('confidence', 0.0)

    if confidence < confidence_threshold or process == 'interpret':
        # Ask for clarification
        envelope = {
            'result': None,
            'trace': {
                'status': 'NEEDS_CLARIFICATION',
                'message': 'Pedido ambíguo — por favor clarifique o objetivo (ex.: "gerar PDF", "criar podcast visual").'
            },
            'artifacts': []
        }
        # write run metadata
        try:
            with open(os.path.join(run_dir, 'run.json'), 'w', encoding='utf-8') as f:
                json.dump({'process': process, 'confidence': confidence, 'status': 'NEEDS_CLARIFICATION', 'time': time.time()}, f, ensure_ascii=False)
        except Exception:
            pass
        return {'status': 'NEEDS_CLARIFICATION', 'envelope': envelope}

    # proceed to planner which enforces capability checks and executes adapters
    res = planner.plan_and_execute(process, text, run_dir, redact_tools=True)

    # write run metadata
    try:
        with open(os.path.join(run_dir, 'run.json'), 'w', encoding='utf-8') as f:
            json.dump({'process': process, 'confidence': confidence, 'status': res.get('status'), 'time': time.time()}, f, ensure_ascii=False)
    except Exception:
        pass

    return res
