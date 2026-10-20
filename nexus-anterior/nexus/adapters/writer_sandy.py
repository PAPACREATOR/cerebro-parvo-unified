"""Trusted, bounded Writer bridge using the pinned Sandy LPAC launcher.

Only a synthetic profile initialization executes outside LPAC. The user's DOCX
or ODT is opened exclusively by soffice.bin in Sandy LPAC. This module owns
neither policy, decisions nor Store; Host retains all authority and Human Gate.
Hrvoje Abraham's MIT demo/launcher contract is vendored with its license.
"""
import ctypes as C
import ctypes.wintypes as W
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

from nexus.contracts import Blocked, strict_json
from nexus.adapters.office import document_kind, pdf_bytes
from nexus.adapters.runner import PROCESS_TO_TOOL, _trace

SANDY_SHA256 = "cbfc30709f80e63b201f1944c34692fc430d8aa42d6cd2823fcc670675307eac"
SANDY_SIZE = 1159680
# CI authenticates the official 26.2.6.2 MSI by its published SHA-256.
# Never invent per-binary hashes: the installed tree is verified byte-for-byte
# against an isolated disposable copy before any user document is opened.
VENDOR = Path(__file__).resolve().parent / "vendor" / "sandy"


def digest_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _native_dacl(path):
    a, k = C.WinDLL("advapi32", use_last_error=True), C.WinDLL("kernel32", use_last_error=True)
    a.GetNamedSecurityInfoW.argtypes = [W.LPCWSTR, W.DWORD, W.DWORD, C.c_void_p,
        C.c_void_p, C.c_void_p, C.c_void_p, C.POINTER(C.c_void_p)]
    a.GetNamedSecurityInfoW.restype = W.DWORD
    a.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = [
        C.c_void_p, W.DWORD, W.DWORD, C.POINTER(C.c_void_p), C.c_void_p]
    a.ConvertSecurityDescriptorToStringSecurityDescriptorW.restype = W.BOOL
    k.LocalFree.argtypes = [C.c_void_p]
    desc, value = C.c_void_p(), C.c_void_p()
    err = a.GetNamedSecurityInfoW(str(path), 1, 4, None, None, None, None, C.byref(desc))
    if err:
        raise Blocked("Não foi possível verificar a DACL do ensaio Writer.")
    try:
        if not a.ConvertSecurityDescriptorToStringSecurityDescriptorW(desc, 1, 4, C.byref(value), None):
            raise Blocked("DACL Writer ilegível.")
        return C.wstring_at(value)
    finally:
        if value: k.LocalFree(value)
        if desc: k.LocalFree(desc)


def _restore_exact_ai_only(before, roots):
    """Restore only AI control-bit bookkeeping after child and Sandy cleanup.

    Reject any changed ACE/control flag, wrong path or incomplete restore.
    No general permission grant, no silent normalization and no host tree ACL.
    """
    a, k = C.WinDLL("advapi32", use_last_error=True), C.WinDLL("kernel32", use_last_error=True)
    a.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
        W.LPCWSTR, W.DWORD, C.POINTER(C.c_void_p), C.c_void_p]
    a.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = W.BOOL
    a.SetFileSecurityW.argtypes = [W.LPCWSTR, W.DWORD, C.c_void_p]
    a.SetFileSecurityW.restype = W.BOOL
    k.LocalFree.argtypes = [C.c_void_p]
    changes = []
    checked_roots = tuple(Path(x).resolve() for x in roots)
    for path, old in before.items():
        real = Path(path).resolve()
        if real != Path(path).absolute() or real.is_junction() or real.is_symlink():
            raise Blocked("Diretório Writer redirecionado.")
        after = _native_dacl(real)
        if after == old:
            # Host task is a read-only security canary; never mutate it.
            continue
        if not any(real == root or root in real.parents for root in checked_roots):
            raise Blocked("Permissões fora da área Writer mudaram; recusa de restauro.")
        if not old.startswith("D:(") or after != "D:AI" + old[2:]:
            raise Blocked("DACL Writer inesperada: revisão humana necessária.")
        changes.append((real, old))
    restored = []
    for path, original in changes:
        descriptor = C.c_void_p()
        if not a.ConvertStringSecurityDescriptorToSecurityDescriptorW(original, 1, C.byref(descriptor), None):
            raise Blocked("Não foi possível construir a DACL original Writer.")
        try:
            if not a.SetFileSecurityW(str(path), 4, descriptor):
                raise Blocked("Restauro estrito da DACL Writer falhou.")
        finally:
            if descriptor: k.LocalFree(descriptor)
        if _native_dacl(path) != original:
            raise Blocked("A DACL Writer mudou após o restauro.")
        restored.append(str(path))
    if any(_native_dacl(path) != value for path, value in before.items()):
        raise Blocked("Ficaram direitos Writer por reconciliar.")
    return restored


def _tree_identity(root):
    """Exact read-only file identity; fails on junctions/symlinks."""
    paths = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or path.is_junction():
            raise Blocked("Árvore LibreOffice contém redirecionamento não autorizado.")
        if path.is_file():
            paths.append(path)
    h = hashlib.sha256()
    # Hash every file, retaining the original sorted order and identity format.
    # Bounded I/O concurrency avoids serial antivirus/file-open latency on Windows.
    with ThreadPoolExecutor(max_workers=4) as pool:
        for path, digest in zip(paths, pool.map(digest_file, paths)):
            relative = str(path.relative_to(root)).replace("\\", "/")
            h.update(relative.encode("utf-8"))
            h.update(b"\0")
            h.update(bytes.fromhex(digest))
    return len(paths), h.hexdigest()


def _copy_runtime(source, target):
    """Copy all bytes/metadata with bounded I/O; never follow redirections."""
    target.mkdir()
    directories = [(source, target)]
    pending = set()
    with ThreadPoolExecutor(max_workers=4) as pool:
        for item in source.rglob("*"):
            if item.is_symlink() or item.is_junction():
                raise Blocked("Instalação Writer contém redirecionamento.")
            destination = target / item.relative_to(source)
            if item.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                directories.append((item, destination))
            elif item.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                pending.add(pool.submit(shutil.copy2, item, destination))
                if len(pending) >= 32:
                    completed, pending = wait(pending, return_when=FIRST_COMPLETED)
                    for future in completed:
                        future.result()
        for future in pending:
            future.result()
    for original, copied in reversed(directories):
        shutil.copystat(original, copied)


def _convert_impl(process, work, stage_root):
    """Run the verified user task using a short, disposable Writer-only root."""
    if os.name != "nt" or process not in ("book", "convert_pdf"):
        raise Blocked("Writer requer o Windows e uma operação autorizada.")
    work = Path(work).resolve()
    if work.is_symlink() or work.is_junction() or work.name == "":
        raise Blocked("Área temporária inválida.")
    original = work / "input.bin"
    raw = original.read_bytes()
    kind = document_kind(raw)
    cfg = strict_json((work / "libreoffice.json").read_bytes())
    if not isinstance(cfg, dict) or set(cfg) != {"executable", "sandy"}:
        raise Blocked("Writer LPAC requer instalação e Sandy fixados na configuração.")
    if any(not isinstance(x, str) for x in cfg.values()):
        raise Blocked("Configuração Writer inválida.")
    executable, sandy = (Path(cfg[key]) for key in ("executable", "sandy"))
    if (not executable.is_absolute() or executable.name.lower() != "soffice.com"
            or not executable.is_file() or not sandy.is_absolute()
            or sandy.name.lower() != "sandy.exe" or not sandy.is_file()):
        raise Blocked("Writer/Sandy instalado não corresponde ao contrato.")
    if (sandy.is_symlink() or sandy.is_junction() or sandy.resolve() != sandy.absolute()
            or sandy.stat().st_size != SANDY_SIZE or digest_file(sandy) != SANDY_SHA256):
        raise Blocked("Sandy não corresponde ao binário v0.9994 aprovado.")
    install = executable.parent.parent
    if (install.is_junction() or install.is_symlink() or
            install.resolve() != install.absolute()):
        raise Blocked("Instalação Writer redirecionada.")
    for name in ("soffice.bin", "soffice.com", "version.ini"):
        item = install / "program" / name
        if not item.is_file() or item.is_symlink() or item.is_junction():
            raise Blocked("A instalação Writer está incompleta ou foi redirecionada.")
    source_identity = _tree_identity(install)
    # LibreOffice still has Win32 components that fail with deep nested paths.
    # Lab success used a short user-owned scratch root; keep the Host/Store
    # input path untouched and copy only the selected document under LPAC.
    if (not stage_root.is_absolute() or not stage_root.is_dir()
            or stage_root.is_symlink() or stage_root.is_junction()
            or len(str(stage_root)) > 150):
        raise Blocked("Área de sandbox Writer demasiado longa ou redirecionada.")
    stage, copied = stage_root / "stage", stage_root / "runtime"
    # Do not operate on the user-installed Writer tree. Sandy may change ACL
    # metadata, so its entire runtime is copied to this disposable task.
    _copy_runtime(install, copied)
    identity = _tree_identity(copied)
    if identity != source_identity:
        raise Blocked("Cópia Writer diferente da instalação de origem.")
    sandy_copy = stage_root / "sandy.exe"
    shutil.copy2(sandy, sandy_copy)
    if sandy_copy.stat().st_size != SANDY_SIZE or digest_file(sandy_copy) != SANDY_SHA256:
        raise Blocked("Cópia do Sandy diferente da fonte autenticada.")
    stage.mkdir()
    for name in ("profile", "work", "temp"):
        (stage / name).mkdir()
    document = stage / "work" / ("resultado" + kind)
    document.write_bytes(raw)
    # Also observe the Host's staging directory; Sandy is never granted its
    # path. Recovery may only touch the new isolated scratch, not Host/Store.
    paths = (work, stage_root, stage, copied,
             stage / "profile", stage / "work", stage / "temp")
    before = {str(p): _native_dacl(p) for p in paths}
    script = VENDOR / "libreoffice-demo.py"
    cmd = [sys.executable, "-I", str(script), "--scratch", str(stage),
           "--libreoffice", str(copied), "--sandy", str(sandy_copy), "--",
           "--headless", "--convert-to", "pdf:writer_pdf_Export",
           "--outdir", str(stage / "work"), str(document)]
    # The trusted subprocess only warms up a synthetic fixture. The real
    # user-supplied document is read only after Sandy's LPAC setup.
    process_handle = None
    try:
        process_handle = subprocess.Popen(cmd, cwd=stage_root, stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP)
        out, err = process_handle.communicate(timeout=135)
    except subprocess.TimeoutExpired:
        if process_handle is not None:
            subprocess.run([str(Path(os.environ["SystemRoot"]) / "System32/taskkill.exe"),
                            "/PID", str(process_handle.pid), "/T", "/F"],
                           capture_output=True, timeout=10)
            process_handle.kill()
            process_handle.wait()
        raise Blocked("Execução Writer excedeu o prazo global do ensaio.") from None
    finally:
        # The original Sandy proof established the job closes on launcher
        # termination. Cleanup is also required before assessing the DACL.
        clean = subprocess.run([str(sandy_copy), "--cleanup"], capture_output=True, timeout=15)
        if clean.returncode != 0:
            raise Blocked("Limpeza Sandy falhou; o resultado não pode ser aceite.")
    _restore_exact_ai_only(before, (stage_root,))
    state_path = stage / "last-run.json"
    # Report only a bounded phase and numeric exit code; never publish paths,
    # document bytes, environment, or unrestricted sandbox logs in the UI.
    if state_path.is_file():
        state = strict_json(state_path.read_bytes())
    else:
        state = {}
    phase = state.get("phase") if state.get("phase") in (
        "preparing", "initializing", "sandboxed", "failed", "finished"
    ) else "unreported"
    # Preserve only fixed diagnostic categories; the subprocess output may
    # contain absolute paths, document text and private profile information.
    diagnostic = "indefinida"
    stderr_text = err.decode("utf-8", errors="replace") if process_handle is not None else ""
    stdout_text = out.decode("utf-8", errors="replace") if process_handle is not None else ""
    if "initialization failed" in stderr_text:
        diagnostic = "inicialização normal do perfil sem PDF sintético"
    elif "Cannot lock scratch folder" in stderr_text:
        diagnostic = "bloqueio de pasta temporária"
    elif "Runtime must be separate" in stderr_text or "runtime must be separate" in stderr_text:
        diagnostic = "separação da runtime e dados"
    elif "Cannot determine the Windows user SID" in stderr_text:
        diagnostic = "identidade do utilizador"
    elif "Cannot launch" in stderr_text or "access denied" in stderr_text.lower():
        diagnostic = "restrição de acesso"
    elif "Sandy exit:" in stdout_text:
        diagnostic = "saída do sandbox"
    elif "Initializing outside LPAC" in stdout_text:
        diagnostic = "preparação de perfil"
    if process_handle is None or process_handle.returncode != 0:
        code = process_handle.returncode if process_handle is not None else -1
        exits = state.get("exit_codes", [])
        exits = exits[:3] if isinstance(exits, list) and all(type(v) is int for v in exits[:3]) else []
        raise Blocked(f"Writer LPAC recusado: {diagnostic}; fase {phase}; launcher {code}; subprocessos {exits}.")
    if phase != "finished" or state.get("exit_code") != 0:
        raise Blocked(f"Sandy não confirmou a execução (fase {phase}; saída não aprovada).")
    if original.read_bytes() != raw or document.read_bytes() != raw:
        raise Blocked("Os bytes originais mudaram durante a conversão.")
    if _tree_identity(copied) != identity:
        raise Blocked("O runtime Writer foi alterado.")
    if digest_file(sandy_copy) != SANDY_SHA256:
        raise Blocked("O executável Sandy mudou durante a tarefa.")
    generated = stage / "work" / "resultado.pdf"
    pdf = pdf_bytes(generated)
    if (work / "resultado.pdf").exists():
        raise Blocked("O resultado PDF já existe.")
    (work / "resultado.pdf").write_bytes(pdf)
    evidence_hash = hashlib.sha256(pdf).hexdigest()
    result = {
        "status": "UNKNOWN", "outcome": "candidate", "title": "PDF convertido",
        "markdown": "# PDF convertido\n\nO original foi conservado. Revê o PDF antes de aprovar; a conversão não prova a fidelidade do conteúdo.",
        "ai_calls": 0, "artifact": {"name": "resultado.pdf", "sha256": evidence_hash},
        "evidence": [{"capability": "libreoffice.writer-pdf", "status": "PASS", "value": evidence_hash}],
    }
    return {"result": result, "trace": _trace(process, PROCESS_TO_TOOL[process])}


def convert(process, work):
    """Return a Host-compatible envelope; one short scratch per Writer run.

    No Store contents, permissions or executable paths are moved. The only
    external runtime copy and Sandbox grants belong to the disposable root.
    """
    if os.name != "nt" or process not in ("book", "convert_pdf"):
        raise Blocked("Writer só está autorizado para estas operações em Windows.")
    with tempfile.TemporaryDirectory(prefix="nw-") as short_scratch:
        root = Path(short_scratch).resolve()
        return _convert_impl(process, work, root)
