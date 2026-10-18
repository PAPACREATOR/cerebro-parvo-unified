import shutil
import os
import json
import time

# Capability probing and registry
# Simple functions to detect whether required binaries are present on the host.

def which(binname: str) -> bool:
    return shutil.which(binname) is not None

def probe_basic_tools():
    """Return a dict of detected tools and versions (best effort).
    Keys: ffmpeg, soffice, java, ace_step, deforum_render, powershell
    """
    res = {
        'ffmpeg': which('ffmpeg'),
        'soffice': which('soffice'),
        'java': which('java'),
        'ace_step': which('ace-step') or which('ace_step'),
        'deforum_render': which('deforum-render'),
        'powershell': which('powershell') or which('pwsh'),
    }
    return res

# Mapping of logical processes to required capabilities and preferred adapters
PROCESS_CAPABILITY_MAP = {
    'visual_podcast': {
        'required': ['powershell', 'ffmpeg'],
        'adapters': ['visual_podcast'],
    },
    'convert_pdf': {
        'required': ['soffice'],
        'adapters': ['convert_pdf'],
    },
    'proofread': {
        'required': ['java'],
        'adapters': ['proofread'],
    },
    'zotero': {
        'required': [],
        'adapters': ['zotero'],
    },
    'ace_step': {
        'required': ['ace_step'],
        'adapters': ['ace_step'],
    },
    'deforium_forge': {
        'required': ['deforum_render'],
        'adapters': ['deforium_forge'],
    },
}


def check_capabilities_for_process(process: str):
    tools = probe_basic_tools()
    entry = PROCESS_CAPABILITY_MAP.get(process, None)
    if not entry:
        return {'ok': False, 'missing': [], 'available': tools}
    missing = [t for t in entry['required'] if not tools.get(t, False)]
    return {'ok': len(missing) == 0, 'missing': missing, 'available': tools}


def save_probe(run_dir: str):
    try:
        os.makedirs(run_dir, exist_ok=True)
        p = probe_basic_tools()
        with open(os.path.join(run_dir, 'capabilities_probe.json'), 'w', encoding='utf-8') as f:
            json.dump({'probe': p, 'time': time.time()}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
