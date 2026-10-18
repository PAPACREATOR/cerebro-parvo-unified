import os
import time
from nexus.adapters import languagetool as lt
from nexus.utils import save_bytes
import json


def run_proofread(text: str, run_dir: str):
    """Run LanguageTool against text and save evidence in run_dir. Returns envelope dict.
    If LanguageTool not configured, returns UNKNOWN with instructions.
    """
    os.makedirs(run_dir, exist_ok=True)
    if lt is None:
        return {'status': 'UNKNOWN', 'message': 'LanguageTool adapter not available.'}

    res = lt.run_languagetool(text)
    if res.get('status') != 'OK':
        return {'status': res.get('status', 'FAIL'), 'message': res.get('message')}

    evidence = res.get('evidence')
    alerts = res.get('alerts', 0)
    # save evidence
    evpath = os.path.join(run_dir, 'linguistic_evidence.json')
    try:
        with open(evpath, 'w', encoding='utf-8') as f:
            json.dump(evidence, f, ensure_ascii=False)
    except Exception as e:
        return {'status': 'FAIL', 'message': 'Failed to save evidence: ' + str(e)}

    # Optionally save corrected text if LanguageTool provides replacements (not implemented here)
    corrected_path = os.path.join(run_dir, 'corrected.txt')
    try:
        with open(corrected_path, 'w', encoding='utf-8') as f:
            f.write(text)
    except Exception:
        pass

    return {'status': 'OK', 'result': {'alerts': alerts, 'evidence_path': evpath}, 'trace': {'tool': 'languagetool', 'time': time.time()}}
