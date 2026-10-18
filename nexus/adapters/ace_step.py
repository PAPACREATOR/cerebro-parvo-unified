import os
import json
import time
import subprocess


def run_ace_step(job_spec: dict, run_dir: str):
    """Attempt to run ACE-Step orchestration tool with a given job_spec.
    If a local 'ace-step' CLI is available in PATH, call it with the job spec JSON
    otherwise persist the job spec and return UNKNOWN with instructions.

    Returns: {status, result?, trace}
    """
    os.makedirs(run_dir, exist_ok=True)
    spec_path = os.path.join(run_dir, 'ace_job_spec.json')
    try:
        with open(spec_path, 'w', encoding='utf-8') as f:
            json.dump(job_spec, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return {'status': 'FAIL', 'message': f'Failed to write job_spec: {e}'}

    # Check for CLI
    if not shutil.which('ace-step'):
        return {'status': 'UNKNOWN', 'message': 'ace-step CLI not found in PATH. Install ACE-Step or provide a runner.' , 'result': {'spec_path': spec_path}, 'trace': {'time': time.time()}}

    # If present, call the CLI (example usage)
    try:
        proc = subprocess.run(['ace-step', spec_path], capture_output=True, timeout=600)
        stdout = proc.stdout.decode('utf-8', errors='ignore')
        stderr = proc.stderr.decode('utf-8', errors='ignore')
        if proc.returncode != 0:
            return {'status': 'FAIL', 'message': 'ace-step failed', 'trace': {'stdout': stdout, 'stderr': stderr, 'time': time.time()}}
        # Assume the CLI writes outputs in the run_dir or reports artifact path in stdout JSON
        try:
            parsed = json.loads(stdout)
        except Exception:
            parsed = {'stdout': stdout}
        return {'status': 'OK', 'result': parsed, 'trace': {'tool': 'ace-step', 'time': time.time()}}
    except Exception as e:
        return {'status': 'FAIL', 'message': str(e)}
