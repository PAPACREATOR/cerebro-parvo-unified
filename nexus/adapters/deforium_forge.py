import os
import json
import time
import subprocess
import shutil


def render_deforum_job(job_spec: dict, run_dir: str):
    """Attempt to run a Deforum/Forge rendering job. If local renderer not present,
    persist the job spec and return UNKNOWN with instructions. If renderer present,
    invoke it and expect it to write output video(s) to run_dir.
    """
    os.makedirs(run_dir, exist_ok=True)
    job_path = os.path.join(run_dir, 'deforum_job.json')
    try:
        with open(job_path, 'w', encoding='utf-8') as f:
            json.dump(job_spec, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return {'status': 'FAIL', 'message': f'Failed to write job spec: {e}'}

    # Check for a hypothetical 'deforum-render' executable
    if not shutil.which('deforum-render'):
        return {'status': 'UNKNOWN', 'message': 'deforum-render executable not found. Stable Diffusion/Deforum requires GPU and manual setup.', 'result': {'job_path': job_path}, 'trace': {'time': time.time()}}

    try:
        proc = subprocess.run(['deforum-render', job_path], capture_output=True, timeout=3600)
        stdout = proc.stdout.decode('utf-8', errors='ignore')
        stderr = proc.stderr.decode('utf-8', errors='ignore')
        if proc.returncode != 0:
            return {'status': 'FAIL', 'message': 'Renderer failed', 'trace': {'stdout': stdout, 'stderr': stderr, 'time': time.time()}}
        # Assume outputs in run_dir
        return {'status': 'OK', 'result': {'stdout': stdout}, 'trace': {'tool': 'deforum-render', 'time': time.time()}}
    except Exception as e:
        return {'status': 'FAIL', 'message': str(e)}
