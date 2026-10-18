"""Simple Windows-focused Nexus mini-host for the white-sheet UI with direct adapters.

This server accepts POST /api/request with JSON {"text": "..."}, chooses a
micro-process, attempts to run a local adapter when available (proofread, zotero),
otherwise falls back to the Windows runner-shell.cmd shim. Returns a normalized
envelope with result + trace.
"""
import base64
import json
import os
import subprocess
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Direct adapters
try:
    from nexus.adapters import languagetool as lt_adapter
except Exception:
    lt_adapter = None
try:
    from nexus.adapters import zotero as zotero_adapter
except Exception:
    zotero_adapter = None

HOST = '127.0.0.1'
PORT = int(os.environ.get('NEXUS_BACKEND_PORT', '5055'))
ROOT = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(ROOT, 'windows', 'runner-shell.cmd')
VALID_PROCESSES = {
    'interpret',
    'proofread',
    'convert_pdf',
    'web',
    'zotero',
    'ace_step',
    'deforium_forge',
    'visual_podcast',
}


def choose_process(text: str) -> str:
    t = (text or '').lower().strip()
    if not t:
        return 'interpret'

    if any(k in t for k in ['visual podcast', 'podcast visual', 'show visual', 'storyboard visual']):
        return 'visual_podcast'
    if any(k in t for k in ['zotero', 'referência', 'referencias', 'bibliografia', 'bibliográfico', 'citação', 'citacao']):
        return 'zotero'
    if any(k in t for k in ['ace-step', 'ace step', 'ace', 'forge', 'aceforge']):
        return 'ace_step'
    if any(k in t for k in ['deforum', 'deforium', 'deforum forge', 'deforium forge']):
        return 'deforium_forge'
    if any(k in t for k in ['pdf', 'converter', 'converter para pdf']):
        return 'convert_pdf'
    if any(k in t for k in ['rever', 'revê', 'revisar', 'revisão', 'proofread', 'linguagem']):
        return 'proofread'
    if any(k in t for k in ['pesquisa', 'procurar', 'web', 'procura', 'fontes']):
        return 'web'
    return 'interpret'


def _safe_json(obj):
    try:
        return json.loads(obj)
    except Exception:
        return None


def run_process_with_runner(process: str, text: str):
    # Fallback path that calls the external Windows runner-shell.cmd
    if process not in VALID_PROCESSES:
        return {'status': 'FAIL', 'error': 'unsupported_process', 'process': process}

    if not os.path.exists(RUNNER):
        return {'status': 'FAIL', 'error': 'missing_runner', 'runner': RUNNER, 'process': process}

    b64 = base64.b64encode(text.encode('utf-8')).decode('ascii')
    cmd = ['cmd.exe', '/C', RUNNER, process, b64]
    try:
        completed = subprocess.run(cmd, capture_output=True, timeout=60)
    except Exception as e:
        return {'status': 'FAIL', 'error': 'runner_failed', 'message': str(e), 'process': process}

    stdout = completed.stdout.decode('utf-8', errors='ignore')
    stderr = completed.stderr.decode('utf-8', errors='ignore')
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]

    if completed.returncode != 0:
        return {'status': 'FAIL', 'error': 'runner_return_code', 'process': process, 'stdout': stdout, 'stderr': stderr}

    if not lines or not lines[0].startswith('NEXUS_SHELL_READY:'):
        return {'status': 'FAIL', 'error': 'invalid_ready_line', 'process': process, 'stdout': stdout, 'stderr': stderr}

    payload = '\n'.join(lines[1:]).strip()
    parsed = _safe_json(payload) if payload else None
    if parsed is None:
        return {'status': 'FAIL', 'error': 'invalid_json', 'process': process, 'raw': payload, 'stdout': stdout, 'stderr': stderr}

    # Normalize the envelope
    if isinstance(parsed, dict) and 'result' in parsed and 'trace' in parsed:
        return {'status': 'OK', 'process': process, 'envelope': parsed}

    return {'status': 'OK', 'process': process, 'envelope': {'result': parsed, 'trace': {'source': 'mini-host'}}}


def orchestrate(process: str, text: str):
    """Try direct adapters first for supported processes, else fall back to runner.

    Returns a dict with keys: status, process, envelope (result+trace) and optional error/message.
    """
    # Direct proofread using LanguageTool adapter if present
    if process == 'proofread' and lt_adapter is not None:
        try:
            res = lt_adapter.run_languagetool(text)
            if res.get('status') == 'OK':
                envelope = {'result': {'alerts': res.get('alerts', 0), 'evidence': res.get('evidence')},
                            'trace': {'tool': 'languagetool', 'status': 'OK'}}
                return {'status': 'OK', 'process': process, 'envelope': envelope}
            else:
                return {'status': res.get('status', 'FAIL'), 'process': process, 'envelope': {'result': None, 'trace': {'tool': 'languagetool', 'status': res.get('status'), 'message': res.get('message')}}}
        except Exception as e:
            return {'status': 'FAIL', 'error': 'adapter_exception', 'message': str(e)}

    # Direct Zotero adapter
    if process == 'zotero' and zotero_adapter is not None:
        try:
            refs = zotero_adapter.import_from_zotero(text)
            envelope = {'result': {'references': refs}, 'trace': {'tool': 'zotero', 'status': 'OK'}}
            return {'status': 'OK', 'process': process, 'envelope': envelope}
        except Exception as e:
            return {'status': 'FAIL', 'error': 'adapter_exception', 'message': str(e)}

    # Otherwise, fallback to runner-shell
    return run_process_with_runner(process, text)


class Handler(BaseHTTPRequestHandler):
    def _reply(self, code, payload):
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ('/', '/health'):
            self._reply(200, {'status': 'ok', 'service': 'simple-nexus-mini-host', 'processes': sorted(VALID_PROCESSES)})
            return
        self._reply(404, {'error': 'not_found'})

    def do_POST(self):
        if self.path != '/api/request':
            self._reply(404, {'error': 'not_found'})
            return

        length = int(self.headers.get('Content-Length', '0'))
        if length <= 0 or length > 3_200_000:
            self._reply(400, {'error': 'invalid_length'})
            return

        raw = self.rfile.read(length)
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError('body must be object')
            text = str(data.get('text', ''))
        except Exception:
            self._reply(400, {'error': 'invalid_json'})
            return

        process = choose_process(text)
        run_id = uuid.uuid4().hex

        # Orchestrate: prefer adapter direct calls when available
        orchestration = orchestrate(process, text)

        # Normalize response
        response = {
            'run_id': run_id,
            'process': process,
            'status': orchestration.get('status', 'FAIL'),
            'envelope': orchestration.get('envelope', {'result': None, 'trace': {'error': orchestration.get('error')}}),
            'message': orchestration.get('message') if orchestration.get('message') else None,
            'error': orchestration.get('error') if orchestration.get('error') else None,
        }
        self._reply(200, response)

    def log_message(self, format, *args):
        # Keep console log minimal but visible.
        print('[simple_server] ' + (format % args))


def serve():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Simple Nexus mini-host listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == '__main__':
    serve()
