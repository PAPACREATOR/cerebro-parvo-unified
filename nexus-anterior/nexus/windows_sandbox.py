"""Windows-enforced tool boundary: per-task AppContainer, DACL and Job Object.

No unsafe fallback. The child starts suspended and only resumes after its
AppContainer token and job membership have been checked. Only stdio handles
are inherited. Native API/ACL failures prevent execution.
"""
from __future__ import annotations

import ctypes as C
import os
from pathlib import Path
import subprocess
import sys
import threading
import uuid

from nexus.contracts import Blocked

_acl_lock = threading.RLock()
READ_EXECUTE = 0x1200A9
MODIFY = 0x1301BF


def _windows():
    if os.name != "nt":
        raise Blocked("A execução protegida requer Windows nesta versão.")


class _API:
    def __init__(self):
        _windows()
        from ctypes import wintypes as W
        H, D, P = W.HANDLE, W.DWORD, C.c_void_p
        self.H, self.D, self.P = H, D, P
        self.k = C.WinDLL("kernel32", use_last_error=True)
        self.a = C.WinDLL("advapi32", use_last_error=True)
        self.u = C.WinDLL("userenv", use_last_error=True)
        self.o = C.WinDLL("ole32", use_last_error=True)
        self.b = C.WinDLL("KernelBase", use_last_error=True)

        class SA(C.Structure):
            _fields_ = [("length", D), ("descriptor", P), ("inherit", W.BOOL)]

        class SI(C.Structure):
            _fields_ = [("cb", D), ("reserved", W.LPWSTR), ("desktop", W.LPWSTR),
                        ("title", W.LPWSTR), ("x", D), ("y", D), ("xs", D), ("ys", D),
                        ("xc", D), ("yc", D), ("fill", D), ("flags", D),
                        ("show", W.WORD), ("reserved_size", W.WORD), ("reserved_bytes", P),
                        ("stdin", H), ("stdout", H), ("stderr", H)]

        class SIX(C.Structure):
            _fields_ = [("si", SI), ("attributes", P)]

        class PI(C.Structure):
            _fields_ = [("process", H), ("thread", H), ("pid", D), ("tid", D)]

        class SIDATTR(C.Structure):
            _fields_ = [("sid", P), ("attributes", D)]

        class GROUPS(C.Structure):
            _fields_ = [("count", D), ("items", SIDATTR * 1)]

        class CAPS(C.Structure):
            _fields_ = [("sid", P), ("capabilities", P), ("count", D), ("reserved", D)]

        class TRUSTEE(C.Structure):
            _fields_ = [("multiple", P), ("operation", D), ("form", D), ("type", D), ("name", P)]

        class ACCESS(C.Structure):
            _fields_ = [("permissions", D), ("mode", D), ("inheritance", D), ("trustee", TRUSTEE)]

        class BASIC(C.Structure):
            _fields_ = [("process_time", C.c_int64), ("job_time", C.c_int64), ("flags", D),
                        ("minimum", C.c_size_t), ("maximum", C.c_size_t), ("active", D),
                        ("affinity", C.c_size_t), ("priority", D), ("scheduling", D)]

        class LIMITS(C.Structure):
            _fields_ = [("basic", BASIC), ("io", C.c_uint64 * 6),
                        ("process_memory", C.c_size_t), ("job_memory", C.c_size_t),
                        ("peak_process", C.c_size_t), ("peak_job", C.c_size_t)]

        self.SA, self.SIX, self.PI, self.CAPS, self.ACCESS, self.LIMITS = SA, SIX, PI, CAPS, ACCESS, LIMITS
        self.SIDATTR, self.GROUPS = SIDATTR, GROUPS
        declarations = {
            "k": {
                "CreatePipe": (W.BOOL, [P, P, P, D]), "SetHandleInformation": (W.BOOL, [H, D, D]),
                "CloseHandle": (W.BOOL, [H]), "LocalFree": (P, [P]),
                "InitializeProcThreadAttributeList": (W.BOOL, [P, D, D, P]),
                "UpdateProcThreadAttribute": (W.BOOL, [P, D, C.c_size_t, P, C.c_size_t, P, P]),
                "DeleteProcThreadAttributeList": (None, [P]),
                "CreateProcessW": (W.BOOL, [W.LPCWSTR, W.LPWSTR, P, P, W.BOOL, D, P, W.LPCWSTR, P, P]),
                "CreateFileW": (H, [W.LPCWSTR, D, D, P, D, D, H]),
                "CreateJobObjectW": (H, [P, W.LPCWSTR]),
                "SetInformationJobObject": (W.BOOL, [H, D, P, D]),
                "AssignProcessToJobObject": (W.BOOL, [H, H]),
                "IsProcessInJob": (W.BOOL, [H, H, P]),
                "TerminateJobObject": (W.BOOL, [H, W.UINT]),
                "ResumeThread": (D, [H]), "WaitForSingleObject": (D, [H, D]),
                "GetExitCodeProcess": (W.BOOL, [H, P]),
                "TerminateProcess": (W.BOOL, [H, W.UINT]),
            },
            "a": {
                "OpenProcessToken": (W.BOOL, [H, D, P]),
                "GetTokenInformation": (W.BOOL, [H, D, P, D, P]),
                "EqualSid": (W.BOOL, [P, P]), "FreeSid": (P, [P]),
                "GetLengthSid": (D, [P]),
                "GetNamedSecurityInfoW": (D, [W.LPCWSTR, D, D, P, P, P, P, P]),
                "SetEntriesInAclW": (D, [D, P, P, P]),
                "SetNamedSecurityInfoW": (D, [W.LPWSTR, D, D, P, P, P, P]),
                "SetSecurityInfo": (D, [H, D, D, P, P, P, P]),
                "ConvertStringSecurityDescriptorToSecurityDescriptorW": (W.BOOL, [W.LPCWSTR, D, P, P]),
                "GetSecurityDescriptorSacl": (W.BOOL, [P, P, P, P]),
                "ConvertSidToStringSidW": (W.BOOL, [P, P]),
            },
            "u": {
                "CreateAppContainerProfile": (C.c_long, [W.LPCWSTR, W.LPCWSTR, W.LPCWSTR, P, D, P]),
                "DeleteAppContainerProfile": (C.c_long, [W.LPCWSTR]),
                "DeriveAppContainerSidFromAppContainerName": (C.c_long, [W.LPCWSTR, P]),
                "GetAppContainerFolderPath": (C.c_long, [W.LPCWSTR, P]),
            },
            "o": {"CoTaskMemFree": (None, [P])},
            "b": {"DeriveCapabilitySidsFromName": (W.BOOL, [W.LPCWSTR, P, P, P, P])},
        }
        for library, functions in declarations.items():
            for name, (result, arguments) in functions.items():
                function = getattr(getattr(self, library), name)
                function.restype, function.argtypes = result, arguments

    def check(self, value, operation):
        if not value:
            raise Blocked(f"A proteção Windows não pôde ser aplicada ({operation}, erro {C.get_last_error()}).")
        return value

    def acl(self, path, sid, mask, mode=1, inherit=True):
        old, descriptor, new = self.P(), self.P(), self.P()
        path = str(path)
        error = self.a.GetNamedSecurityInfoW(path, 1, 4, None, None, C.byref(old), None, C.byref(descriptor))
        if error:
            raise Blocked(f"Não foi possível verificar os direitos da tarefa ({error}).")
        try:
            entry = self.ACCESS()
            entry.permissions, entry.mode, entry.inheritance = mask, mode, 3 if inherit else 0
            entry.trustee.form, entry.trustee.type, entry.trustee.name = 0, 5, sid
            error = self.a.SetEntriesInAclW(1, C.byref(entry), old, C.byref(new))
            if not error:
                if not inherit and Path(path).is_dir():
                    # Documented MAXIMUM_ALLOWED handle semantics suppress
                    # propagation to children. Only this task SID's ACE changes;
                    # the tool does not receive the Host handle or its rights.
                    handle = self.k.CreateFileW(path, 0x02000000, 7, None, 3, 0x02000000, None)
                    self.check(handle and handle != self.H(-1).value, "directory ACL handle")
                    try:
                        error = self.a.SetSecurityInfo(handle, 1, 4, None, None, new, None)
                    finally:
                        self.k.CloseHandle(handle)
                else:
                    error = self.a.SetNamedSecurityInfoW(path, 1, 4, None, None, new, None)
            if error:
                raise Blocked(f"Não foi possível delimitar os direitos da tarefa ({error}).")
        finally:
            if new: self.k.LocalFree(new)
            if descriptor: self.k.LocalFree(descriptor)

    def registry_read_sid(self):
        groups, capabilities = C.POINTER(self.P)(), C.POINTER(self.P)()
        ng, nc = self.D(), self.D()
        self.check(self.b.DeriveCapabilitySidsFromName("registryRead", C.byref(groups),
                   C.byref(ng), C.byref(capabilities), C.byref(nc)), "runtime capability")
        try:
            if nc.value != 1:
                raise Blocked("Capacidade de arranque Windows inesperada.")
            return C.create_string_buffer(C.string_at(capabilities[0], self.a.GetLengthSid(capabilities[0])))
        finally:
            for array, count in ((groups, ng.value), (capabilities, nc.value)):
                for i in range(count):
                    self.k.LocalFree(array[i])
                if array:
                    self.k.LocalFree(array)

    def check_capabilities(self, token):
        length = self.D()
        self.a.GetTokenInformation(token, 30, None, 0, C.byref(length))
        data = C.create_string_buffer(length.value)
        self.check(self.a.GetTokenInformation(token, 30, data, length, C.byref(length)), "capabilities")
        groups = C.cast(data, C.POINTER(self.GROUPS)).contents
        expected = self.registry_read_sid()
        if groups.count != 1 or not self.a.EqualSid(groups.items[0].sid, expected):
            raise Blocked("O processo tem capacidades externas não autorizadas.")

    def low_label(self, path):
        descriptor, sacl = self.P(), self.P()
        present, defaulted = self.D(), self.D()
        self.check(self.a.ConvertStringSecurityDescriptorToSecurityDescriptorW(
            "S:(ML;OICI;NW;;;LW)", 1, C.byref(descriptor), None), "work label")
        try:
            self.check(self.a.GetSecurityDescriptorSacl(descriptor, C.byref(present), C.byref(sacl),
                                                       C.byref(defaulted)), "work label read")
            error = self.a.SetNamedSecurityInfoW(str(path), 1, 0x10, None, None, None, sacl)
            if error: raise Blocked(f"Não foi possível preparar a área delimitada ({error}).")
        finally:
            self.k.LocalFree(descriptor)


class ConfinedProcess:
    """Small binary-stdio process object; close terminates the complete job."""
    def __init__(self, command, *, cwd, env, read_roots=(), read_dirs=(), deny_roots=()):
        _windows()
        if not isinstance(command, (list, tuple)) or not command or any(
                not isinstance(x, str) or "\x00" in x for x in command):
            raise Blocked("Comando de ferramenta inválido.")
        executable = Path(command[0])
        work = Path(cwd)
        if not executable.is_absolute() or not executable.is_file() or not work.is_absolute() or not work.is_dir():
            raise Blocked("Área ou executável de ferramenta inválido.")
        for path in (work, executable, *(Path(x) for x in (*read_roots, *read_dirs))):
            if path.is_symlink() or path.resolve() != path.absolute():
                raise Blocked("Ligação de filesystem não autorizada na execução.")
        self.api = _API()
        self.sid = self.api.P()
        self.name = "nexus-" + uuid.uuid4().hex
        self.job = self.process = None
        self.stdin = self.stdout = self.stderr = None
        self.returncode = None
        self.grants, self.handles = [], []
        self.shallow_grants = set()
        self.created, self.locked = False, False
        self.cwd = work
        try:
            _acl_lock.acquire(); self.locked = True
            # Windows needs the per-task profile to launch (ERROR_FILE_NOT_FOUND
            # was observed with a derived SID alone). Deny the tool its storage;
            # only the separately assigned work directory may be used.
            result = self.api.u.CreateAppContainerProfile(self.name, self.name, "Nexus task", None, 0, C.byref(self.sid))
            if result < 0: raise Blocked(f"Não foi possível criar a identidade restrita ({result:#x}).")
            self.created = True
            sid_text, profile = self.api.P(), self.api.P()
            try:
                self.api.check(self.api.a.ConvertSidToStringSidW(self.sid, C.byref(sid_text)), "profile SID")
                result = self.api.u.GetAppContainerFolderPath(C.wstring_at(sid_text), C.byref(profile))
                if result < 0: raise Blocked("Não foi possível delimitar o perfil da tarefa.")
                self.profile_path = C.wstring_at(profile)
                self.api.acl(self.profile_path, self.sid, 0x1F01FF, mode=3)
                self.grants.append(self.profile_path)
            finally:
                if sid_text: self.api.k.LocalFree(sid_text)
                if profile: self.api.o.CoTaskMemFree(profile)
            # Directory enumeration is separate from recursive file access.
            for path in dict.fromkeys(str(Path(x).resolve()) for x in read_dirs):
                if not Path(path).is_dir():
                    raise Blocked("Diretório de runtime inválido.")
                self.api.acl(path, self.sid, READ_EXECUTE, inherit=False)
                self.grants.append(path)
                self.shallow_grants.add(path)
            for path in dict.fromkeys(str(Path(x).resolve()) for x in read_roots):
                self.api.acl(path, self.sid, READ_EXECUTE, inherit=Path(path).is_dir())
                self.grants.append(path)
            for path in deny_roots:
                self.api.acl(Path(path).resolve(), self.sid, 0x1F01FF, mode=3)
                self.grants.append(str(Path(path).resolve()))
            self.api.acl(work, self.sid, MODIFY)
            self.grants.append(str(work))
            self.api.low_label(work)
            self._start(command, work, env)
        except BaseException:
            self.close()
            raise

    def _pipe(self, child_reads):
        a = self.api
        read, write = a.H(), a.H()
        security = a.SA(C.sizeof(a.SA), None, True)
        a.check(a.k.CreatePipe(C.byref(read), C.byref(write), C.byref(security), 0), "stdio pipe")
        child, parent = (read.value, write.value) if child_reads else (write.value, read.value)
        self.handles += [child, parent]
        a.check(a.k.SetHandleInformation(parent, 1, 0), "stdio inheritance")
        return child, parent

    def _start(self, command, work, env):
        import msvcrt
        a = self.api
        child_in, parent_in = self._pipe(True)
        child_out, parent_out = self._pipe(False)
        child_err, parent_err = self._pipe(False)
        size = C.c_size_t()
        a.k.InitializeProcThreadAttributeList(None, 3, 0, C.byref(size))
        attributes = C.create_string_buffer(size.value)
        a.check(a.k.InitializeProcThreadAttributeList(attributes, 3, 0, C.byref(size)), "process attributes")
        runtime_sid = a.registry_read_sid()
        runtime_caps = (a.SIDATTR * 1)(a.SIDATTR(C.cast(runtime_sid, a.P), 4))
        caps = a.CAPS(self.sid, C.cast(runtime_caps, a.P), 1, 0)
        # Only the documented read-only registry runtime capability; no network,
        # device, camera, microphone, COM or registry-write capability.
        handles = (a.H * 3)(child_in, child_out, child_err)
        opt_out = a.D(1)  # LPAC: do not inherit ALL APPLICATION PACKAGES access.
        info, process = a.SIX(), a.PI()
        info.si.cb, info.si.flags = C.sizeof(info), 0x100
        info.si.stdin, info.si.stdout, info.si.stderr = child_in, child_out, child_err
        info.attributes = C.cast(attributes, a.P)
        try:
            for key, value in ((0x20009, caps), (0x20002, handles), (0x2000F, opt_out)):
                a.check(a.k.UpdateProcThreadAttribute(attributes, 0, key, C.byref(value), C.sizeof(value),
                                                      None, None), "restricted attributes")
            self.job = a.check(a.k.CreateJobObjectW(None, None), "job")
            limits = a.LIMITS()
            limits.basic.flags = 0x2000 | 0x8 | 0x200
            limits.basic.active, limits.job_memory = 24, 8 * 1024 ** 3
            a.check(a.k.SetInformationJobObject(self.job, 9, C.byref(limits), C.sizeof(limits)), "job limits")
            environment = dict(env)
            # AppContainer startup needs these names (ERROR_ENVVAR_NOT_FOUND
            # was observed with only the minimal Host environment). Values are
            # explicit task paths, never the human's home/profile or credentials.
            environment.update(USERPROFILE=str(work), APPDATA=str(work),
                               LOCALAPPDATA=str(work), HOME=str(work))
            block = C.create_unicode_buffer("\0".join(k + "=" + v for k, v in
                                                      sorted(environment.items(), key=lambda x: x[0].upper())) + "\0\0")
            line = C.create_unicode_buffer(subprocess.list2cmdline(command))
            a.check(a.k.CreateProcessW(command[0], line, None, None, True,
                                      0x80000 | 0x400 | 0x4 | 0x08000000, block, str(work),
                                      C.byref(info), C.byref(process)), "restricted launch")
            self.process = process.process
            self.handles.append(process.thread)
            a.check(a.k.AssignProcessToJobObject(self.job, self.process), "job assignment")
            in_job = a.D()
            a.check(a.k.IsProcessInJob(self.process, self.job, C.byref(in_job)), "job verification")
            if not in_job.value: raise Blocked("A tarefa não ficou no seu Job Object.")
            self._check_token()
            if a.k.ResumeThread(process.thread) == 0xFFFFFFFF:
                a.check(False, "resume")
            for handle in (child_in, child_out, child_err):
                a.k.CloseHandle(handle); self.handles.remove(handle)
            for name, handle, mode, flags in (("stdin", parent_in, "wb", os.O_WRONLY),
                                             ("stdout", parent_out, "rb", os.O_RDONLY),
                                             ("stderr", parent_err, "rb", os.O_RDONLY)):
                fd = msvcrt.open_osfhandle(handle, flags | os.O_BINARY)
                self.handles.remove(handle)
                setattr(self, name, os.fdopen(fd, mode, buffering=0))
            self.pid = process.pid
        finally:
            a.k.DeleteProcThreadAttributeList(attributes)

    def _check_token(self):
        a = self.api
        token, length, contained = a.H(), a.D(), a.D()
        a.check(a.a.OpenProcessToken(self.process, 8, C.byref(token)), "token query")
        try:
            a.check(a.a.GetTokenInformation(token, 29, C.byref(contained), C.sizeof(contained),
                                            C.byref(length)), "AppContainer token")
            if not contained.value: raise Blocked("O processo não ficou num AppContainer.")
            a.check_capabilities(token)
            # Class 46 is rejected by GetTokenInformation on CI (ERROR_INVALID_PARAMETER).
            # LPAC is requested by the documented opt-out creation attribute;
            # real AAP-access canaries verify its behavior, not an unsupported query.
            a.a.GetTokenInformation(token, 31, None, 0, C.byref(length))
            data = C.create_string_buffer(length.value)
            a.check(a.a.GetTokenInformation(token, 31, data, length, C.byref(length)), "task identity")
            sid = C.cast(data, C.POINTER(a.P))[0]
            if not a.a.EqualSid(sid, self.sid): raise Blocked("Identidade da tarefa diferente da atribuída.")
        finally:
            a.k.CloseHandle(token)

    def wait(self, timeout=None):
        result = self.api.k.WaitForSingleObject(self.process, 0xFFFFFFFF if timeout is None else int(timeout * 1000))
        if result == 258: raise subprocess.TimeoutExpired("confined task", timeout)
        if result != 0: self.api.check(False, "wait")
        code = self.api.D()
        self.api.check(self.api.k.GetExitCodeProcess(self.process, C.byref(code)), "exit code")
        self.returncode = code.value
        return self.returncode

    def kill(self):
        if self.job: self.api.check(self.api.k.TerminateJobObject(self.job, 1), "terminate job")

    def communicate(self, input=None, timeout=None):
        outputs = [bytearray(), bytearray()]
        overflow = threading.Event()
        def drain(stream, output):
            while block := stream.read(65536):
                if len(output) + len(block) > 4_000_000:
                    overflow.set(); self.kill(); break
                output.extend(block)
        threads = [threading.Thread(target=drain, args=(stream, outputs[i]), daemon=True)
                   for i, stream in enumerate((self.stdout, self.stderr))]
        for thread in threads: thread.start()
        try:
            if input: self.stdin.write(input)
            self.stdin.close()
            self.wait(timeout)
        except BaseException:
            self.kill(); self.wait(5); raise
        finally:
            self.kill()  # A parent exit never leaves descendants alive.
            for thread in threads: thread.join(5)
        if overflow.is_set() or any(t.is_alive() for t in threads):
            raise Blocked("A ferramenta excedeu o limite de saída.")
        return tuple(bytes(x) for x in outputs)

    def close(self):
        a = self.api
        errors = []
        if self.job:
            a.k.TerminateJobObject(self.job, 1)
        if self.process:
            a.k.TerminateProcess(self.process, 1)
            a.k.WaitForSingleObject(self.process, 5000)
        for stream in (self.stdin, self.stdout, self.stderr):
            if stream and not stream.closed: stream.close()
        for handle in self.handles:
            a.k.CloseHandle(handle)
        self.handles.clear()
        if self.process: a.k.CloseHandle(self.process); self.process = None
        if self.job: a.k.CloseHandle(self.job); self.job = None
        for path in reversed(self.grants):
            try: a.acl(path, self.sid, 0, mode=4, inherit=path not in self.shallow_grants)
            except Exception as error: errors.append(error)
        self.grants.clear()
        self.shallow_grants.clear()
        if self.created:
            result = a.u.DeleteAppContainerProfile(self.name)
            if result < 0: errors.append(Blocked(f"Limpeza da identidade restrita falhou ({result:#x})."))
            self.created = False
        if self.sid: a.a.FreeSid(self.sid); self.sid = a.P()
        if self.locked: _acl_lock.release(); self.locked = False
        if errors: raise Blocked("A limpeza da fronteira Windows requer reconciliação.") from errors[0]

    def __enter__(self): return self
    def __exit__(self, *_): self.close()


def launch_confined(command, *, cwd, env, read_roots=(), read_dirs=(), deny_roots=()):
    return ConfinedProcess(command, cwd=cwd, env=env, read_roots=read_roots,
                           read_dirs=read_dirs, deny_roots=deny_roots)


def task_environment(work):
    """Explicit task paths; never inherit the human's secrets or cache roots."""
    work = str(work)
    keep = ("SystemRoot", "WINDIR", "COMSPEC", "SYSTEMDRIVE")
    env = {key: os.environ[key] for key in keep if key in os.environ}
    system = Path(os.environ.get("SystemRoot", "C:/Windows")) / "System32"
    env.update(PATH=str(Path(sys.executable).parent) + os.pathsep + str(system),
               TEMP=work, TMP=work, USERPROFILE=work, APPDATA=work,
               LOCALAPPDATA=work, HOME=work, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
               PYTHONDONTWRITEBYTECODE="1")
    return env


def inside_native_boundary():
    """Inspect the actual OS token and job; an environment flag is not authority."""
    if os.name != "nt":
        return False
    a = _API()
    current = a.H(-1)
    token, length, contained, in_job = a.H(), a.D(), a.D(), a.D()
    a.check(a.a.OpenProcessToken(current, 8, C.byref(token)), "current token")
    try:
        a.check(a.a.GetTokenInformation(token, 29, C.byref(contained), C.sizeof(contained),
                                        C.byref(length)), "current AppContainer")
        if not contained.value:
            return False
        a.check_capabilities(token)
        a.check(a.k.IsProcessInJob(current, None, C.byref(in_job)), "current job")
        if not in_job.value:
            raise Blocked("O processo não tem um limite de execução.")
        return True
    finally:
        a.k.CloseHandle(token)


def require_native_boundary():
    if not inside_native_boundary():
        raise Blocked("Esta ferramenta só pode executar através da área protegida.")
