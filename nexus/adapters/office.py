import os
import tempfile
import subprocess
from hashlib import sha256


def convert_office_to_pdf(file_bytes: bytes, filename: str):
    """Wrapper that attempts to convert office documents to PDF using the
    local LibreOffice soffice binary. Returns a simple envelope.

    Returns: {status, artifact_sha256, size_bytes, message}
    """
    soffice = os.environ.get('LIBREOFFICE_PATH', 'soffice')
    tmpdir = tempfile.mkdtemp(prefix='nexus-office-')
    inpath = os.path.join(tmpdir, filename)
    with open(inpath, 'wb') as f:
        f.write(file_bytes)

    try:
        proc = subprocess.run([soffice, '--headless', '--convert-to', 'pdf', inpath, '--outdir', tmpdir], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    except FileNotFoundError:
        return {'status': 'UNKNOWN', 'message': f'LibreOffice ({soffice}) not found'}
    except subprocess.TimeoutExpired:
        return {'status': 'FAIL', 'message': 'conversion timed out'}

    base, _ = os.path.splitext(inpath)
    outpdf = base + '.pdf'
    if not os.path.exists(outpdf):
        return {'status': 'FAIL', 'message': 'PDF not produced', 'stdout': proc.stdout.decode('utf-8', errors='ignore'), 'stderr': proc.stderr.decode('utf-8', errors='ignore')}

    with open(outpdf, 'rb') as f:
        data = f.read()
    return {'status': 'OK', 'artifact_sha256': sha256(data).hexdigest(), 'size_bytes': len(data)}
