"""Planner: automatically select adapters and execute them without exposing tool names to the user.

Behavior:
- Probe host capabilities (shallow): ffmpeg/soffice/java/powershell/etc.
- For a requested process, determine required tools and whether available.
- If all required available: select the preferred adapter and execute it.
- If some required missing: return status UNKNOWN with user-friendly instruction (do not expose internal tool names by default), persist full probe and chosen plan in run_dir for audit.
- Always write run_planner.json into run_dir with full_trace for admin/audit.

This module does not perform the heavy work itself; it calls adapter functions already implemented in nexus.adapters.*
"""
import os
import json
import time
from nexus import capabilities


def _user_friendly_install_instructions(missing:list):
    # Map internal tool names to short install hints
    hints = {
        'ffmpeg': 'instale o ffmpeg (ex: choco install ffmpeg) ou adicione ffmpeg ao PATH',
        'soffice': 'instale o LibreOffice (soffice) e assegure que soffice está no PATH',
        'java': 'instale o Java (JRE/JDK) e adicione java ao PATH',
        'ace_step': 'instale o ACE-Step CLI e adicione ao PATH',
        'deforum_render': 'instale/renderizador Deforum (requer GPU e configuração manual)',
        'powershell': 'assegure que o PowerShell está disponível (Windows) para TTS',
    }
    return [hints.get(m, f'instale {m} (ver documentação)') for m in missing]


def plan_and_execute(process: str, text: str, run_dir: str, redact_tools: bool = True):
    # Persist probe
    capabilities.save_probe(run_dir)
    probe = capabilities.probe_basic_tools()

    plan = capabilities.check_capabilities_for_process(process)
    full_plan = {'process': process, 'time': time.time(), 'probe': probe, 'plan': plan}
    try:
        os.makedirs(run_dir, exist_ok=True)
        with open(os.path.join(run_dir, 'run_planner.json'), 'w', encoding='utf-8') as f:
            json.dump(full_plan, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    if not plan['ok']:
        # Missing required tools. Return user-friendly instruction but persist full plan for audit.
        missing = plan['missing']
        instructions = _user_friendly_install_instructions(missing)
        envelope = {
            'result': None,
            'trace': {
                'status': 'UNKNOWN',
                'message': 'Ferramentas necessárias em falta para produzir o artefato solicitado.',
                'user_instructions': instructions
            },
            'artifacts': []
        }
        # Also write a full trace file (audit) with the missing tools and probe
        try:
            with open(os.path.join(run_dir, 'run_planner_full_trace.json'), 'w', encoding='utf-8') as f:
                json.dump({'full_plan': full_plan}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return {'status': 'UNKNOWN', 'envelope': envelope}

    # If we get here, required tools are present.
    # Choose adapter and call it. We keep the adapter/tool name out of the user-facing trace by default.
    try:
        if process == 'visual_podcast':
            from nexus.adapters import visual_podcast as vp
            res = vp.create_visual_podcast(text, run_dir)
        elif process == 'convert_pdf':
            from nexus.adapters import convert_pdf as cp
            res = cp.convert_pdf_from_run(run_dir)
        elif process == 'proofread':
            from nexus.adapters import proofread as pr
            res = pr.run_proofread(text, run_dir)
        elif process == 'zotero':
            from nexus.adapters import zotero as zt
            refs = zt.import_from_zotero(text)
            res = {'status': 'OK', 'result': {'references': refs}, 'trace': {'tool': 'zotero', 'time': time.time()}}
        elif process == 'ace_step':
            from nexus.adapters import ace_step as ac
            # Expect text to be a job_spec JSON string or small description; here we persist job spec done earlier
            try:
                job_spec = json.loads(text)
            except Exception:
                job_spec = {'description': text}
            res = ac.run_ace_step(job_spec, run_dir)
        elif process == 'deforium_forge':
            from nexus.adapters import deforium_forge as df
            try:
                job_spec = json.loads(text)
            except Exception:
                job_spec = {'description': text}
            res = df.render_deforum_job(job_spec, run_dir)
        else:
            # Default fallback: try orchestrate if present
            if 'orchestrate' in globals():
                res = orchestrate(process, text)
            else:
                res = {'status': 'FAIL', 'message': 'Process not recognized and no orchestrator available.'}
    except Exception as e:
        res = {'status': 'FAIL', 'message': str(e)}

    # Normalize output into envelope
    status = res.get('status', 'FAIL')
    envelope = {'result': res.get('result'), 'trace': {'status': status, 'message': res.get('message')} }
    # artifacts: if adapters returned artifact metadata include them
    artifacts = []
    if isinstance(res.get('result'), dict) and 'artifact' in res.get('result'):
        artifacts.append(res.get('result')['artifact'])
    # Save full res for audit
    try:
        with open(os.path.join(run_dir, 'run_planner_result_full.json'), 'w', encoding='utf-8') as f:
            json.dump({'res': res, 'full_plan': full_plan, 'time': time.time()}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    # Optionally redact tool names for user
    if redact_tools:
        envelope['trace'].pop('tool', None)
    else:
        envelope['trace']['tool'] = res.get('trace', {}).get('tool')

    envelope['artifacts'] = artifacts
    return {'status': status, 'envelope': envelope}
