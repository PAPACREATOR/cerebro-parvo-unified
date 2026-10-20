"""Pure deterministic transport probe; no model, vault, network or approval API."""
import hashlib
import json
import re
import sys
from pathlib import Path


def raw_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def check_packet(packet):
    if not isinstance(packet, dict) or set(packet) != {'version', 'objective', 'trust', 'sources'}:
        raise ValueError('packet fields')
    if packet['version'] != 1 or packet['trust'] != 'UNTRUSTED_CONTEXT':
        raise ValueError('packet authority')
    if not isinstance(packet['objective'], str) or not packet['objective'].strip() or len(packet['objective']) > 500:
        raise ValueError('objective limit')
    if not isinstance(packet['sources'], list) or not 1 <= len(packet['sources']) <= 8:
        raise ValueError('source count')
    seen = set()
    for source in packet['sources']:
        if not isinstance(source, dict) or set(source) != {'run_id', 'content_sha256', 'provenance_sha256', 'authority', 'content', 'process_id', 'input_sha256'}:
            raise ValueError('source fields')
        if not isinstance(source['run_id'], str) or not re.fullmatch('[0-9a-f]{32}', source['run_id']) or source['run_id'] in seen:
            raise ValueError('source identity')
        seen.add(source['run_id'])
        for name in ('content_sha256', 'provenance_sha256', 'input_sha256'):
            if not isinstance(source[name], str) or not re.fullmatch('[0-9a-f]{64}', source[name]):
                raise ValueError('source hash')
        if source['authority'] not in ('creative', 'canonical') or source['process_id'] not in ('verify', 'interpret', 'proofread', 'convert_pdf'):
            raise ValueError('source classification')
        if not isinstance(source['content'], str) or not source['content'].strip() or '\x00' in source['content']:
            raise ValueError('source content')
        if digest(source['content'].encode('utf-8')) != source['content_sha256']:
            raise ValueError('content hash mismatch')
    if len(raw_json(packet).decode('utf-8')) > 6000 or '\x00' in packet['objective']:
        raise ValueError('context limit')
    return packet


def summarize(packet):
    check_packet(packet)
    return {'status': 'UNKNOWN', 'outcome': 'candidate', 'title': 'Inventário experimental de contexto',
            'markdown': '# Contexto recebido\n\n' + '\n'.join(
                '- ' + s['run_id'] + ' [' + s['authority'] + ']' for s in packet['sources']),
            'evidence': [{'capability': 'lab.context-transport', 'status': 'PASS', 'value': digest(raw_json(packet))}],
            'ai_calls': 0}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    raw = Path(sys.argv[1]).read_bytes()
    if len(raw) > 24000:
        raise ValueError('input byte limit')
    print(json.dumps(summarize(json.loads(raw)), ensure_ascii=False))
