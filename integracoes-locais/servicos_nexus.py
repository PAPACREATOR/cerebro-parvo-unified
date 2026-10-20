"""Start local Nexus tools under the restricted Windows NexusTool account."""

from pathlib import Path
import ctypes
import getpass
import json
import os
import socket
import subprocess
import time
from ctypes import wintypes


ROOT = Path(__file__).resolve().parent
STATE = ROOT / "registos/processos.json"

TOOL_USER = "NexusTool"
TOOL_DOMAIN = os.environ.get("COMPUTERNAME", "MATRIX")

LOGON_WITH_PROFILE = 0x00000001
CREATE_UNICODE_ENVIRONMENT = 0x00000400
CREATE_NO_WINDOW = 0x08000000
STARTF_USESTDHANDLES = 0x00000100

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_ALWAYS = 4
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 0x00000080
FILE_END = 2
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("nLength", wintypes.DWORD),
        ("lpSecurityDescriptor", wintypes.LPVOID),
        ("bInheritHandle", wintypes.BOOL),
    ]


class STARTUPINFO(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
    ]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]


advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

advapi32.CreateProcessWithLogonW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPWSTR,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.LPCWSTR,
    ctypes.POINTER(STARTUPINFO),
    ctypes.POINTER(PROCESS_INFORMATION),
]
advapi32.CreateProcessWithLogonW.restype = wintypes.BOOL

kernel32.CreateFileW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.POINTER(SECURITY_ATTRIBUTES),
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
]
kernel32.CreateFileW.restype = wintypes.HANDLE

kernel32.SetFilePointerEx.argtypes = [
    wintypes.HANDLE,
    ctypes.c_longlong,
    ctypes.POINTER(ctypes.c_longlong),
    wintypes.DWORD,
]
kernel32.SetFilePointerEx.restype = wintypes.BOOL

kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL


def image_path(pid):
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.QueryFullProcessImageNameW.argtypes = [
        ctypes.c_void_p,
        ctypes.c_uint32,
        ctypes.c_wchar_p,
        ctypes.POINTER(ctypes.c_uint32),
    ]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]

    handle = kernel.OpenProcess(0x1000, False, int(pid))

    if not handle:
        return None

    try:
        size = ctypes.c_uint32(32768)
        buffer = ctypes.create_unicode_buffer(size.value)

        if kernel.QueryFullProcessImageNameW(
            handle,
            0,
            buffer,
            ctypes.byref(size),
        ):
            return Path(buffer.value).resolve()

        return None

    finally:
        kernel.CloseHandle(handle)


def occupied(port):
    with socket.socket() as sock:
        return sock.connect_ex(("127.0.0.1", port)) == 0


def tool_environment(extra=None):
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    profile = Path(r"C:\Users") / TOOL_USER

    env = {
        "SystemRoot": system_root,
        "WINDIR": system_root,
        "ComSpec": str(Path(system_root) / "System32" / "cmd.exe"),
        "OS": "Windows_NT",
        "USERNAME": TOOL_USER,
        "USERDOMAIN": TOOL_DOMAIN,
        "USERPROFILE": str(profile),
        "HOMEDRIVE": "C:",
        "HOMEPATH": rf"\Users\{TOOL_USER}",
        "APPDATA": str(profile / "AppData" / "Roaming"),
        "LOCALAPPDATA": str(profile / "AppData" / "Local"),
        "TEMP": str(profile / "AppData" / "Local" / "Temp"),
        "TMP": str(profile / "AppData" / "Local" / "Temp"),
        "ProgramData": os.environ.get("ProgramData", r"C:\ProgramData"),
        "PUBLIC": os.environ.get("PUBLIC", r"C:\Users\Public"),
        "PATHEXT": os.environ.get(
            "PATHEXT",
            ".COM;.EXE;.BAT;.CMD",
        ),
        "PATH": os.pathsep.join(
            [
                str(ROOT / "ferramentas" / "node"),
                str(ROOT / "ferramentas" / "python"),
                str(Path(system_root) / "System32"),
                system_root,
                str(Path(system_root) / "System32" / "Wbem"),
            ]
        ),
    }

    for key in (
        "ProgramFiles",
        "ProgramFiles(x86)",
        "ProgramW6432",
        "CommonProgramFiles",
        "CommonProgramFiles(x86)",
        "CommonProgramW6432",
        "NUMBER_OF_PROCESSORS",
        "PROCESSOR_ARCHITECTURE",
    ):
        value = os.environ.get(key)
        if value:
            env[key] = value

    if extra:
        for key, value in extra.items():
            env[str(key)] = str(value)

    return env


def environment_buffer(environment):
    pairs = []

    for key, value in sorted(
        environment.items(),
        key=lambda item: item[0].upper(),
    ):
        key = str(key)
        value = str(value)

        if "\0" in key or "\0" in value or "=" in key:
            raise ValueError("Invalid environment variable")

        pairs.append(f"{key}={value}")

    block = "\0".join(pairs) + "\0\0"
    return ctypes.create_unicode_buffer(block)


def launch_as_tool(command, cwd, environment, password, log_path):
    command = [str(part) for part in command]
    executable = str(Path(command[0]).resolve())

    sa = SECURITY_ATTRIBUTES()
    sa.nLength = ctypes.sizeof(sa)
    sa.lpSecurityDescriptor = None
    sa.bInheritHandle = True

    log_handle = kernel32.CreateFileW(
        str(log_path),
        GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        ctypes.byref(sa),
        OPEN_ALWAYS,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )

    if log_handle == INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error())

    nul_handle = kernel32.CreateFileW(
        "NUL",
        GENERIC_READ,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        ctypes.byref(sa),
        OPEN_EXISTING,
        FILE_ATTRIBUTE_NORMAL,
        None,
    )

    if nul_handle == INVALID_HANDLE_VALUE:
        kernel32.CloseHandle(log_handle)
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        if not kernel32.SetFilePointerEx(
            log_handle,
            0,
            None,
            FILE_END,
        ):
            raise ctypes.WinError(ctypes.get_last_error())

        startup = STARTUPINFO()
        startup.cb = ctypes.sizeof(startup)
        startup.dwFlags = STARTF_USESTDHANDLES
        startup.hStdInput = nul_handle
        startup.hStdOutput = log_handle
        startup.hStdError = log_handle

        process_info = PROCESS_INFORMATION()

        command_line = ctypes.create_unicode_buffer(
            subprocess.list2cmdline(command)
        )

        env_buffer = environment_buffer(environment)

        ok = advapi32.CreateProcessWithLogonW(
            TOOL_USER,
            TOOL_DOMAIN,
            password,
            LOGON_WITH_PROFILE,
            executable,
            command_line,
            CREATE_NO_WINDOW | CREATE_UNICODE_ENVIRONMENT,
            ctypes.cast(env_buffer, wintypes.LPVOID),
            str(cwd),
            ctypes.byref(startup),
            ctypes.byref(process_info),
        )

        if not ok:
            raise ctypes.WinError(ctypes.get_last_error())

        pid = int(process_info.dwProcessId)

        kernel32.CloseHandle(process_info.hThread)
        kernel32.CloseHandle(process_info.hProcess)

        return pid

    finally:
        kernel32.CloseHandle(log_handle)
        kernel32.CloseHandle(nul_handle)


def start_all():
    state = (
        json.loads(STATE.read_text(encoding="utf-8"))
        if STATE.exists()
        else {}
    )

    config = json.loads(
        (ROOT / "configuracao/notebook.json").read_text(
            encoding="utf-8"
        )
    )

    tiny = json.loads(
        (ROOT / "configuracao/tiny.json").read_text(
            encoding="utf-8"
        )
    )

    source = ROOT / "bancada/open-notebook"

    base_env = tool_environment()

    notebook_env = tool_environment(
        {
            "SURREAL_URL": "ws://127.0.0.1:18000/rpc",
            "SURREAL_USER": "nexus",
            "SURREAL_PASSWORD": config["database_password"],
            "SURREAL_PASS": config["database_password"],
            "SURREAL_NAMESPACE": "nexus_workbench",
            "SURREAL_DATABASE": "workbench",
            "OPEN_NOTEBOOK_PASSWORD": config["password"],
            "OPEN_NOTEBOOK_ENCRYPTION_KEY": config["encryption_key"],
            "API_HOST": "127.0.0.1",
            "API_PORT": "5055",
            "API_RELOAD": "false",
            "CORS_ORIGINS": "http://127.0.0.1:3000",
            "PYTHONUTF8": "1",
            "PYTHONPATH": str(source),
            "OPEN_NOTEBOOK_WORKER_MAX_TASKS": "1",
            "NEXT_TELEMETRY_DISABLED": "1",
            "API_URL": "http://127.0.0.1:5055",
            "NEXT_PUBLIC_API_URL": "http://127.0.0.1:5055",
        }
    )

    tiny_env = tool_environment(
        {
            "LLAMA_API_KEY": tiny["api_key"],
        }
    )

    ui_env = dict(notebook_env)

    for secret in (
        "SURREAL_PASSWORD",
        "SURREAL_PASS",
        "OPEN_NOTEBOOK_PASSWORD",
        "OPEN_NOTEBOOK_ENCRYPTION_KEY",
    ):
        ui_env.pop(secret, None)

    password = None

    def tool_password():
        nonlocal password

        if password is None:
            password = getpass.getpass(
                "Password da conta NexusTool: "
            )

        return password

    def launch(name, command, cwd, port=None, environment=None):
        record = state.get(name, {})
        existing = image_path(record.get("pid", 0))
        expected = Path(command[0]).resolve()

        if existing != expected:

            if port and occupied(port):
                raise RuntimeError(
                    f"{name}: porta {port} ocupada "
                    "por outro processo; conservado."
                )

            pid = launch_as_tool(
                command=command,
                cwd=cwd,
                environment=environment or base_env,
                password=tool_password(),
                log_path=ROOT / "registos" / f"{name}.log",
            )

            state[name] = {
                "pid": pid,
                "executable": str(expected),
            }

            STATE.write_text(
                json.dumps(state, indent=2),
                encoding="utf-8",
            )

        if port:
            deadline = time.monotonic() + 60

            while not occupied(port):

                if time.monotonic() > deadline:
                    raise RuntimeError(
                        name + ": arranque excedeu 60 segundos"
                    )

                if image_path(state[name]["pid"]) is None:
                    raise RuntimeError(
                        name
                        + ": processo terminou; consultar registo"
                    )

                time.sleep(0.25)

    launch(
        "database",
        [
            str(ROOT / "ferramentas/surreal.exe"),
            "start",
            "--bind",
            "127.0.0.1:18000",
            "--log",
            "warn",
            "rocksdb:" + str(ROOT / "dados/notebook-database"),
        ],
        source,
        18000,
        base_env,
    )

    launch(
        "notebook-api",
        [
            str(source / ".venv/Scripts/python.exe"),
            "run_api.py",
        ],
        source,
        5055,
        notebook_env,
    )

    launch(
        "notebook-worker",
        [
            str(source / ".venv/Scripts/python.exe"),
            "-m",
            "surreal_commands.cli.worker",
            "--import-modules",
            "commands",
            "--max-tasks",
            "1",
        ],
        source,
        environment=notebook_env,
    )

    launch(
        "tiny",
        [
            str(ROOT / "ferramentas/llama/llama-server.exe"),
            "-m",
            str(ROOT / "modelos/Qwen3-4B-Q4_K_M.gguf"),
            "--host",
            "127.0.0.1",
            "--port",
            "8082",
            "--alias",
            "nexus-tiny",
            "-c",
            "4096",
            "-ngl",
            "99",
            "-np",
            "1",
            "--jinja",
            "--chat-template-kwargs",
            '{"enable_thinking":false}',
        ],
        ROOT / "ferramentas/llama",
        8082,
        tiny_env,
    )

    launch(
        "notebook-ui",
        [
            str(ROOT / "ferramentas/node/node.exe"),
            str(
                source
                / "frontend/node_modules/next/dist/bin/next"
            ),
            "dev",
            "--hostname",
            "127.0.0.1",
            "--port",
            "3000",
        ],
        source / "frontend",
        3000,
        ui_env,
    )

    password = None

    return {
        name: record["pid"]
        for name, record in state.items()
    }


if __name__ == "__main__":
    print(json.dumps(start_all()))
