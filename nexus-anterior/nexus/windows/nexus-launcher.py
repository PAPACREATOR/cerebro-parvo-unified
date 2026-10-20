"""Tiny Windows launcher for an already-installed Nexus runtime.

This EXE never packages or replaces the Kernel. It only starts the exact
Python environment and repository recorded by the installer.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def fail(message: str) -> int:
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, "Nexus", 0x10)
    except Exception:
        print(message, file=sys.stderr)
    return 1


def main() -> int:
    if os.name != "nt":
        return fail("Este lançador destina-se ao Windows.")
    base = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent
    config_path = base / "nexus-launcher.json"
    if not config_path.is_file():
        return fail("Configuração do lançador Nexus ausente.")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    except Exception:
        return fail("Configuração do lançador Nexus inválida.")
    if (not isinstance(config, dict)
            or set(config) != {"repo_root", "python", "git", "data_root", "expected_origin", "expected_head"}
            or any(not isinstance(value, str) or not value for value in config.values())
            or not re.fullmatch(r"[0-9a-f]{40}", config["expected_head"])
            or config["expected_origin"] != "https://github.com/PAPACREATOR/cerebro-parvo-.git"
            or any(not Path(config[key]).is_absolute() for key in ("repo_root", "python", "git", "data_root"))):
        return fail("Configuração do lançador Nexus incompatível.")
    repo = Path(config["repo_root"]).resolve()
    python = Path(config["python"]).resolve()
    git = Path(config["git"]).resolve()
    data = Path(config["data_root"]).resolve()
    if not python.is_file() or not git.is_file() or not (repo / ".git").is_dir() or not (repo / "nexus" / "app.py").is_file():
        return fail("Instalação Nexus não encontrada.")
    try:
        origin = subprocess.check_output(
            [str(git), "-C", str(repo), "config", "--get", "remote.origin.url"],
            text=True, encoding="utf-8", errors="strict", timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        ).strip()
    except Exception:
        return fail("Não foi possível validar a origem Git do Nexus.")
    if origin != config["expected_origin"]:
        return fail("Origem Git inesperada. Arranque bloqueado.")
    try:
        head = subprocess.check_output(
            [str(git), "-C", str(repo), "rev-parse", "HEAD"],
            text=True, encoding="utf-8", errors="strict", timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        ).strip()
        dirty = subprocess.check_output(
            [str(git), "-C", str(repo), "status", "--porcelain", "--untracked-files=all"],
            text=True, encoding="utf-8", errors="strict", timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        ).strip()
    except Exception:
        return fail("Não foi possível validar o HEAD e o estado Git do Nexus.")
    if head != config["expected_head"] or dirty:
        return fail("Checkout alterado ou HEAD não aceite. Executa o bootstrap com o HEAD revisto.")
    flags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    try:
        proc = subprocess.Popen(
            [str(python), "-m", "nexus.app", "--data", str(data)],
            cwd=str(repo),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
            close_fds=True,
        )
    except Exception:
        return fail("Não foi possível iniciar o Nexus.")
    return 0 if proc.pid else 1


if __name__ == "__main__":
    raise SystemExit(main())
