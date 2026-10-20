"""Direct deterministic verify capability for equivalence testing.

This module does not own persistence, approval or recovery. It only executes
the existing verify contract without a workflow engine.
"""
import json
import os
import subprocess
from pathlib import Path

from nexus.adapters.tools import hash_python, compare, report
from nexus.contracts import Blocked

POLICY = {
    "agreement": "PASS",
    "conflict": "UNKNOWN",
    "unknown": "UNKNOWN",
    "failure": "FAIL",
}


def powershell_executable():
    root = os.environ.get("SystemRoot") or os.environ.get("WINDIR")
    if not root:
        raise Blocked("PowerShell Windows indisponível.")
    return str(Path(root) / "System32/WindowsPowerShell/v1.0/powershell.exe")



def hash_cng(path):
    """Windows CNG SHA256, inside the assigned task; independent of hashlib."""
    from nexus.windows_sandbox import require_native_boundary
    require_native_boundary()
    import ctypes as C
    dll = C.WinDLL("bcrypt", use_last_error=True)
    P, U, N = C.c_void_p, C.c_ulong, C.c_long
    declarations = {
        "BCryptOpenAlgorithmProvider": ([C.POINTER(P), C.c_wchar_p, C.c_wchar_p, U], N),
        "BCryptGetProperty": ([P, C.c_wchar_p, P, U, C.POINTER(U), U], N),
        "BCryptCreateHash": ([P, C.POINTER(P), P, U, P, U, U], N),
        "BCryptHashData": ([P, P, U, U], N),
        "BCryptFinishHash": ([P, P, U, U], N),
        "BCryptDestroyHash": ([P], N),
        "BCryptCloseAlgorithmProvider": ([P, U], N),
    }
    for name, (args, returns) in declarations.items():
        function = getattr(dll, name)
        function.argtypes, function.restype = args, returns
    def check(status):
        if status < 0:
            raise Blocked(f"A verificação nativa Windows falhou ({status & 0xffffffff:#x}).")
    algorithm, hashed = P(), P()
    try:
        check(dll.BCryptOpenAlgorithmProvider(C.byref(algorithm), "SHA256",
                                              "Microsoft Primitive Provider", 0))
        size, used, digest_size = U(), U(), U()
        check(dll.BCryptGetProperty(algorithm, "ObjectLength", C.byref(size),
                                   C.sizeof(size), C.byref(used), 0))
        if used.value != C.sizeof(size) or not 0 < size.value <= 1_000_000:
            raise Blocked("Provider Windows devolveu um limite inválido.")
        check(dll.BCryptGetProperty(algorithm, "HashDigestLength", C.byref(digest_size),
                                   C.sizeof(digest_size), C.byref(used), 0))
        if used.value != C.sizeof(digest_size) or digest_size.value != 32:
            raise Blocked("Provider Windows devolveu um algoritmo inválido.")
        storage, output = C.create_string_buffer(size.value), C.create_string_buffer(32)
        check(dll.BCryptCreateHash(algorithm, C.byref(hashed), storage, len(storage), None, 0, 0))
        total = 0
        with Path(path).open("rb") as stream:
            while block := stream.read(65536):
                total += len(block)
                if total > 2_097_152:
                    raise Blocked("Input fora do limite de verificação.")
                buffer = C.create_string_buffer(block)
                check(dll.BCryptHashData(hashed, buffer, len(block), 0))
        check(dll.BCryptFinishHash(hashed, output, len(output), 0))
        return {"status": "PASS", "sha256": output.raw.hex(), "capability": "windows.cng-sha256"}
    finally:
        try:
            if hashed:
                check(dll.BCryptDestroyHash(hashed))
        finally:
            if algorithm:
                check(dll.BCryptCloseAlgorithmProvider(algorithm, 0))


def hash_windows(path, *, executable=None, timeout=15):
    if os.name == "nt" and executable is None:
        from nexus.windows_sandbox import inside_native_boundary
        if inside_native_boundary():
            return hash_cng(path)
    script = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$p = [Console]::In.ReadToEnd().TrimEnd([char]10, [char]13)
try {
  $algorithm = [System.Security.Cryptography.SHA256]::Create()
  try { $hash = [BitConverter]::ToString($algorithm.ComputeHash([System.IO.File]::ReadAllBytes($p))).Replace('-', '').ToLowerInvariant() }
  finally { $algorithm.Dispose() }
  [Console]::Out.WriteLine('{"status":"PASS","sha256":"' + $hash + '","capability":"windows.dotnet-sha256"}')
} catch {
  [Console]::Error.WriteLine($_.Exception.Message)
  [Console]::Out.WriteLine('{"status":"FAIL","sha256":null,"capability":"windows.dotnet-sha256","error":"Não foi possível ler o ficheiro."}')
}
"""
    command = executable or powershell_executable()
    try:
        completed = subprocess.run(
            [command, "-NoProfile", "-NonInteractive", "-Command", script],
            input=str(Path(path).resolve()),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise Blocked("A verificação Windows excedeu o tempo permitido.") from error
    except OSError as error:
        raise Blocked("PowerShell Windows indisponível.") from error

    if completed.returncode != 0 or not completed.stdout.strip():
        raise Blocked("A verificação Windows falhou.")
    try:
        value = json.loads(completed.stdout.strip().splitlines()[-1])
    except (ValueError, UnicodeError) as error:
        raise Blocked("A verificação Windows devolveu dados inválidos.") from error
    if not isinstance(value, dict) or value.get("status") not in ("PASS", "FAIL"):
        raise Blocked("A verificação Windows devolveu contrato inválido.")
    return value


def execute(path, *, powershell=None, timeout=15):
    a = hash_windows(path, executable=powershell, timeout=timeout)
    b = hash_python(path)
    comparison = compare(a, b)
    result = report({"comparison": comparison, "status": POLICY[comparison["outcome"]]})
    return {
        "result": result,
        "trace": {
            "engine": "nexus/python-direct",
            "version": "1.0.0",
            "summary": {
                "usage": {"total_tokens": 0},
                "agents_executed": ["hash_windows", "hash_python", "compare", "report"],
            },
            "events": [
                {"type": "step.completed", "step": "hash_windows"},
                {"type": "step.completed", "step": "hash_python"},
                {"type": "step.completed", "step": "compare"},
                {"type": "step.completed", "step": "report"},
            ],
        },
    }
