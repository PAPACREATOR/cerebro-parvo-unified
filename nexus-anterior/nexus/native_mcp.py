"""Pipe-only MCP runtime inside the verified Windows boundary.

Adapt AnyIO's existing Trio backend and CPython local pipes. OS capabilities
are unchanged; asyncio networking/subprocess backends are unavailable here.
The IOCP adaptation is pinned to Trio 0.34.0 and accepts only the observed
WSAEACCES at its final Winsock startup probe, after IOCP initialization.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

if __package__ in (None, ""):
    spec = importlib.util.spec_from_file_location(
        "nexus", Path(__file__).absolute().parent / "__init__.py",
        submodule_search_locations=[str(Path(__file__).absolute().parent)])
    package = importlib.util.module_from_spec(spec)
    sys.modules["nexus"] = package
    spec.loader.exec_module(package)

from nexus.contracts import Blocked

if __name__ == "__main__":
    sys.modules["nexus.native_mcp"] = sys.modules[__name__]

_configured = False


def configure():
    global _configured
    if os.name != "nt" or _configured:
        return
    from nexus.windows_sandbox import inside_native_boundary
    if not inside_native_boundary():
        return
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    import types
    # Permit imports of asyncio's public data types without loading _overlapped,
    # whose import itself creates a network socket. Actual asyncio loops fail
    # closed; all MCP concurrency below uses AnyIO/Trio and local pipes.
    if "asyncio" in sys.modules:
        raise Blocked("Runtime assíncrono já iniciado antes do isolamento.")
    windows = types.ModuleType("asyncio.windows_events")
    class NoNetworkPolicy:
        def __init__(self, *args, **kwargs):
            raise Blocked("Este runtime protegido só aceita stdio local.")
    windows.DefaultEventLoopPolicy = NoNetworkPolicy
    windows.WindowsProactorEventLoopPolicy = NoNetworkPolicy
    windows.WindowsSelectorEventLoopPolicy = NoNetworkPolicy
    windows.__all__ = ("DefaultEventLoopPolicy", "WindowsProactorEventLoopPolicy",
                       "WindowsSelectorEventLoopPolicy")
    asyncio_spec = importlib.util.find_spec("asyncio")
    module = importlib.util.module_from_spec(asyncio_spec)
    module.windows_events = windows
    sys.modules["asyncio.windows_events"] = windows
    sys.modules["asyncio"] = module
    asyncio_spec.loader.exec_module(module)

    from asyncio import windows_utils
    import _winapi
    import uuid

    # Adapt CPython 3.12 windows_utils.pipe: AppContainer pipes must use LOCAL.
    # https://github.com/python/cpython/blob/v3.12.10/Lib/asyncio/windows_utils.py
    # CPython is licensed under PSF-2.0. No network/backend emulation is added.
    def local_pipe(*, duplex=False, overlapped=(True, True), bufsize=8192):
        address = r"\\.\pipe\LOCAL\nexus-" + uuid.uuid4().hex
        access = _winapi.GENERIC_WRITE
        mode = _winapi.PIPE_ACCESS_INBOUND | _winapi.FILE_FLAG_FIRST_PIPE_INSTANCE
        if duplex:
            mode = _winapi.PIPE_ACCESS_DUPLEX | _winapi.FILE_FLAG_FIRST_PIPE_INSTANCE
            access |= _winapi.GENERIC_READ
        if overlapped[0]:
            mode |= _winapi.FILE_FLAG_OVERLAPPED
        flags = _winapi.FILE_FLAG_OVERLAPPED if overlapped[1] else 0
        first = second = None
        try:
            first = _winapi.CreateNamedPipe(address, mode, _winapi.PIPE_WAIT | 8,
                    1, bufsize if duplex else 0, bufsize, 0, _winapi.NULL)
            second = _winapi.CreateFile(address, access, 0, _winapi.NULL,
                    _winapi.OPEN_EXISTING, flags, _winapi.NULL)
            connected = _winapi.ConnectNamedPipe(first, overlapped=True)
            connected.GetOverlappedResult(True)
            return first, second
        except BaseException:
            for handle in (first, second):
                if handle is not None:
                    _winapi.CloseHandle(handle)
            raise
    windows_utils.pipe = local_pipe

    from importlib import metadata
    if metadata.version("trio") != "0.34.0":
        raise Blocked("Versão do runtime stdio precisa de validação.")
    import trio._core._io_windows as io
    original = io.WindowsIOManager.__init__
    import linecache
    def pipe_only_init(self):
        try:
            original(self)
        except PermissionError as error:
            tb = error.__traceback__
            probe = False
            while tb:
                if (tb.tb_frame.f_code is original.__code__ and
                        linecache.getline(original.__code__.co_filename, tb.tb_lineno).strip()
                        == "with socket.socket() as s:"):
                    probe = True
                tb = tb.tb_next
            ready = all(hasattr(self, name) for name in (
                "_events", "_vacant_afd_groups", "_afd_ops", "_afd_waiters",
                "_overlapped_waiters", "_posted_too_late_to_cancel",
                "_completion_key_queues", "_completion_key_counter"))
            if not (error.winerror == 10013 and probe and ready and self._iocp is not None):
                raise
            # The rejected final check concerns socket LSPs; this stdio runtime
            # never uses socket polling. IOCP and all pipe state are ready.
    io.WindowsIOManager.__init__ = pipe_only_init
    # Trio's entry queue also uses a TCP socketpair. Use an unnamed, task-local
    # auto-reset Win32 event; wakes coalesce without blocking a worker/signal.
    # Noninteractive child lifetime/interrupts are controlled by the Host Job.
    from trio._core._wakeup_socketpair import WakeupSocketpair
    def event_init(self):
        self._event = io.kernel32.CreateEventA(io.ffi.NULL, False, False, io.ffi.NULL)
        if self._event == io.ffi.NULL:
            io.raise_winerror()
    def event_wakeup(self):
        if not io.kernel32.SetEvent(self._event):
            io.raise_winerror()
    async def event_wait(self):
        import trio
        while True:
            status = io.kernel32.WaitForSingleObject(self._event, 0)
            if status == 0:
                return
            if status != 258:
                io.raise_winerror()
            await trio.sleep(0.01)
    def event_close(self):
        handle, self._event = self._event, io.ffi.NULL
        if handle != io.ffi.NULL and not io.kernel32.CloseHandle(handle):
            io.raise_winerror()
    WakeupSocketpair.__init__ = event_init
    WakeupSocketpair.wakeup_thread_and_signal_safe = event_wakeup
    WakeupSocketpair.wait_woken = event_wait
    WakeupSocketpair.drain = lambda self: None
    WakeupSocketpair.wakeup_on_signals = lambda self: None
    WakeupSocketpair.close = event_close
    import anyio
    run = anyio.run
    def local_run(function, *args, backend="trio", backend_options=None):
        if backend != "trio":
            raise Blocked("Backend de rede não autorizado na execução stdio.")
        return run(function, *args, backend="trio", backend_options=backend_options)
    anyio.run = local_run
    _configured = True


def command_for(command):
    """Trusted caller selects only the same Python script or installed entry."""
    from nexus.contracts import ROOT
    executable = Path(command[0])
    prefix = [str(Path(sys.executable).resolve()), "-I", str(ROOT / "native_mcp.py")]
    args = list(command[1:])
    if executable.name.lower() in {"python.exe", "pythonw.exe"}:
        while args and args[0] in {"-I", "-u", "-B", "-E", "-s"}:
            args.pop(0)
        if not args or args[0].startswith("-") or not Path(args[0]).is_absolute():
            raise Blocked("Entrada MCP Python não autorizada.")
        return prefix + ["--script", *args]
    if executable.parent.name.lower() == "scripts" and not args:
        return prefix + ["--entry", executable.stem]
    raise Blocked("Este servidor MCP precisa de um runtime stdio validado.")


def main():
    configure()
    from nexus.windows_sandbox import require_native_boundary
    require_native_boundary()
    if len(sys.argv) < 3:
        raise Blocked("Entrada stdio inválida.")
    mode, entry, *args = sys.argv[1:]
    if mode == "--script":
        import runpy
        sys.argv = [entry, *args]
        runpy.run_path(entry, run_name="__main__")
    elif mode == "--entry" and not args:
        import importlib.metadata
        points = list(importlib.metadata.entry_points(group="console_scripts", name=entry))
        if len(points) != 1:
            raise Blocked("Entrada instalada MCP indisponível ou ambígua.")
        sys.argv = [entry]
        points[0].load()()
    else:
        raise Blocked("Entrada stdio não autorizada.")


if __name__ == "__main__":
    main()
