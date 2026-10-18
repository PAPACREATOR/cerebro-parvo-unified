import json
import os
import subprocess
import tempfile
from hashlib import sha256


def run_languagetool(text: str):
    """Run LanguageTool CLI (if configured) against `text` and return a structured
    envelope. Environment variable LANGUAGETOOL_JAR should point to the
    language-tool-commandline jar. If not present, return status UNKNOWN.

    Returns: {status: 'OK'|'UNKNOWN'|'FAIL', evidence: {...}, alerts: int, message: str}
    """
    jar = os.environ.get('LANGUAGETOOL_JAR')
    if not jar:
        return {'status': 'UNKNOWN', 'message': 'LanguageTool not configured (set LANGUAGETOOL_JAR)'}
    cmd = ['java', '-jar', jar, '--json', '-l', 'pt-PT']
    try:
        proc = subprocess.run(cmd, input=text.encode('utf-8'), stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    except FileNotFoundError:
        return {'status': 'UNKNOWN', 'message': 'java not found in PATH'}
    except subprocess.TimeoutExpired:
        return {'status': 'FAIL', 'message': 'LanguageTool timed out'}

    if proc.returncode != 0 and not proc.stdout:
        return {'status': 'FAIL', 'message': proc.stderr.decode('utf-8', errors='ignore')}

    try:
        parsed = json.loads(proc.stdout.decode('utf-8') or '{}')
    except Exception as e:
        return {'status': 'FAIL', 'message': 'Failed to parse LanguageTool JSON: ' + str(e), 'raw': proc.stdout.decode('utf-8', errors='ignore')}

    matches = parsed.get('matches', []) if isinstance(parsed, dict) else []
    return {'status': 'OK', 'evidence': parsed, 'alerts': len(matches)}


def convert_document_to_pdf(file_bytes: bytes, filename: str):
    """Convert a DOCX/ODT file to PDF using LibreOffice soffice if available.
    Environment variable LIBREOFFICE_PATH may override the soffice binary name.

    Returns: {status: 'OK'|'UNKNOWN'|'FAIL', artifact_sha256: str, size_bytes: int, message: str}
    """
    soffice = os.environ.get('LIBREOFFICE_PATH', 'soffice')
    tmpdir = tempfile.mkdtemp(prefix='nexus-')
    inpath = os.path.join(tmpdir, filename)
    with open(inpath, 'wb') as f:
        f.write(file_bytes)
    try:
        # LibreOffice will create the PDF next to the input file.
        proc = subprocess.run([soffice, '--headless', '--convert-to', 'pdf', inpath, '--outdir', tmpdir], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    except FileNotFoundError:
        return {'status': 'UNKNOWN', 'message': f'LibreOffice ({soffice}) not found in PATH'}
    except subprocess.TimeoutExpired:
        return {'status': 'FAIL', 'message': 'LibreOffice conversion timed out'}

    # Look for resulting PDF
    base, _ = os.path.splitext(inpath)
    outpdf = base + '.pdf'
    if not os.path.exists(outpdf):
        return {'status': 'FAIL', 'message': 'No PDF produced', 'stdout': proc.stdout.decode('utf-8', errors='ignore'), 'stderr': proc.stderr.decode('utf-8', errors='ignore')}
    with open(outpdf, 'rb') as f:
        data = f.read()
    digest = sha256(data).hexdigest()
    return {'status': 'OK', 'artifact_sha256': digest, 'size_bytes': len(data)}
