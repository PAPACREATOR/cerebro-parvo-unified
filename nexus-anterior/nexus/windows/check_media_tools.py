"""Physical/local ACE-Step + Forge health gate through the Nexus MCP boundary."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from datetime import datetime, timezone

REPO = Path(__file__).resolve().parents[2]
NEXUS = REPO / "nexus"
sys.path.insert(0, str(REPO))

from nexus.contracts import Blocked
from nexus.mcp_client import MCPServerSpec, call_tool


def _spec():
    return MCPServerSpec(
        command=sys.executable,
        args=("-I", str(NEXUS / "mcp_tools_server.py")),
    )


def probe():
    spec = _spec()
    ace = call_tool(spec, "check_ace_step", {}, allowed_tools={"check_ace_step"})
    forge = call_tool(spec, "check_forge", {}, allowed_tools={"check_forge"})
    if ace.get("authority") != "NONE" or forge.get("authority") != "NONE":
        raise Blocked("Ferramenta externa tentou declarar autoridade.")
    return ace, forge


def run(wait_seconds: int):
    deadline = time.monotonic() + max(0, wait_seconds)
    last_error = "Ferramentas externas ainda não responderam."
    while True:
        try:
            ace, forge = probe()
            return {
                "status": "PASS",
                "checked_utc": datetime.now(timezone.utc).isoformat(),
                "chain": "Nexus Python -> MCP -> external localhost tools",
                "authority": "NONE",
                "ace_step": ace,
                "forge": forge,
            }
        except Exception as error:
            last_error = str(error) if isinstance(error, Blocked) else "Falha local inesperada."
            if time.monotonic() >= deadline:
                return {
                    "status": "FAIL",
                    "checked_utc": datetime.now(timezone.utc).isoformat(),
                    "chain": "Nexus Python -> MCP -> external localhost tools",
                    "authority": "NONE",
                    "error": last_error,
                }
            time.sleep(2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-seconds", type=int, default=90)
    args = parser.parse_args()
    value = run(args.wait_seconds)
    print(json.dumps(value, ensure_ascii=False))
    return 0 if value["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
