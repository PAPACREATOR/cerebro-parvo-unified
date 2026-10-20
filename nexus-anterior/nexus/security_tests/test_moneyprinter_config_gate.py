"""Fail-closed tests for MoneyPrinterTurbo installation configuration."""
from __future__ import annotations

import subprocess
import sys

from nexus.contracts import ROOT


def test_moneyprinter_config_helper_requires_explicit_install_authority(tmp_path):
    report = tmp_path / "report.json"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "windows" / "configure-moneyprinterturbo-local.py"),
            "--root",
            str(tmp_path / "missing-root"),
            "--ffmpeg",
            str(tmp_path / "missing-ffmpeg.exe"),
            "--report",
            str(report),
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    observed = result.stdout + result.stderr
    assert result.returncode != 0
    assert "NEXUS_INSTALL_AUTHORIZATION_REQUIRED" in observed
    assert not report.exists()
