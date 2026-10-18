import os
import time
from nexus.utils import sha256_bytes, save_bytes
from nexus.adapters import office as office_adapter


def convert_pdf_from_run(run_dir: str):
    """Look for an input document in run_dir (input.docx or input.odt). If found,
    convert to PDF using LibreOffice via office_adapter.convert_office_to_pdf.
    Writes output.pdf in run_dir and returns envelope dict.
    """
    candidates = ['input.docx', 'input.odt', 'input.doc']
    input_path = None
    for c in candidates:
        p = os.path.join(run_dir, c)
        if os.path.exists(p):
            input_path = p
            break

    if not input_path:
        return {'status': 'UNKNOWN', 'message': 'No input document found in run_dir. Place input.docx or input.odt in the run directory and retry.'}

    with open(input_path, 'rb') as f:
        data = f.read()

    # Use office adapter to convert
    res = office_adapter.convert_office_to_pdf(data, os.path.basename(input_path))
    if res.get('status') != 'OK':
        return {'status': res.get('status', 'FAIL'), 'message': res.get('message', 'conversion failed'), 'stdout': res.get('stdout'), 'stderr': res.get('stderr')}

    # office_adapter returns artifact_sha256 and size_bytes; find output file in run_dir
    base = os.path.splitext(input_path)[0]
    outpdf = base + '.pdf'
    if not os.path.exists(outpdf):
        return {'status': 'FAIL', 'message': 'Conversion reported success but PDF not found at expected path.'}

    with open(outpdf, 'rb') as f:
        pdfdata = f.read()
    sha = sha256_bytes(pdfdata)
    size = len(pdfdata)
    # Persist metadata
    metadata = {'artifact': {'path': outpdf, 'sha256': sha, 'size_bytes': size}, 'trace': {'tool': 'libreoffice', 'time': time.time()}}
    return {'status': 'OK', 'result': metadata}
