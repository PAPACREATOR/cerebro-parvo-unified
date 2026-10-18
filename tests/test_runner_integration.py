# Runner envelope integration test: start server and call /api/request
import threading
import time
import json
import urllib.request
import urllib.error

from simple_server import serve


def start_server():
    t = threading.Thread(target=serve, daemon=True)
    t.start()
    time.sleep(1)
    return t


def do_request(text):
    data = json.dumps({'text': text}).encode('utf-8')
    req = urllib.request.Request('http://127.0.0.1:5055/api/request', data=data, headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return f'HTTP {e.code}: {e.read().decode()}'
    except Exception as e:
        return f'ERR: {e}'


if __name__ == '__main__':
    start_server()
    tests = [
        ('Importa referências do Zotero para este documento.', 'zotero'),
        ('Converte para PDF o documento anexo.', 'convert_pdf'),
        ('Revisa o texto e devolve diagnóstico.', 'proofread'),
        ('Quero um podcast visual com imagens e guião.', 'visual_podcast'),
    ]
    for text, expected in tests:
        out = do_request(text)
        print('Input:', text)
        print('Output:', out)
        try:
            parsed = json.loads(out)
            assert parsed.get('process') == expected, f"Expected process {expected}, got {parsed.get('process')}"
        except Exception as e:
            print('Test failed:', e)
            raise
    print('runner envelope integration tests passed')
