"""Windows-only end-to-end check of argv and exit-code handling in runner.ps1.

Uses a temporary stand-in nexus.run_job. Does not execute real Nexus tools.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parents[1] / "windows" / "runner.ps1"

STUB = r"""
import argparse
import json
import os
import pathlib
import sys

p = argparse.ArgumentParser()
p.add_argument("--process", required=True)
p.add_argument("--text", required=True)
p.add_argument("--run-dir", required=True)
args = p.parse_args()
pathlib.Path(args.run_dir).mkdir(parents=True, exist_ok=True)
(pathlib.Path(args.run_dir) / "argv.json").write_text(
    json.dumps(vars(args), ensure_ascii=False), encoding="utf-8"
)
print(json.dumps({"status": "OK", "text": args.text}, ensure_ascii=False))
sys.exit(int(os.environ["NEXUS_RUNNER_TEST_RC"]))
"""


@unittest.skipUnless(os.name == "nt", "PowerShell 5.1 runner requires Windows")
class WindowsRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        package = self.root / "nexus"
        package.mkdir()
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "run_job.py").write_text(STUB, encoding="utf-8")
        self.run_dir = self.root / "runs com espaços e ü"

    def invoke(self, user_text, exit_code=0):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.root)
        env["NEXUS_RUNNER_TEST_RC"] = str(exit_code)
        return subprocess.run(
            [
                "powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", str(RUNNER),
                "-process", "interpret", "-text", user_text,
                "-run_dir", str(self.run_dir),
            ],
            cwd=self.root,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=35,
            check=False,
        )

    def test_quotes_metacharacters_unicode_are_literal(self):
        sentinel = self.root / "injected.txt"
        payload = (
            'Pedido "com aspas"; Set-Content -LiteralPath "'
            + str(sentinel)
            + '"; # áçõ 🎵 $(Get-Date) & | >'
        )
        result = self.invoke(payload)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        observed = json.loads((self.run_dir / "argv.json").read_text(encoding="utf-8"))
        self.assertEqual(observed["text"], payload)
        self.assertEqual(observed["process"], "interpret")
        self.assertEqual(observed["run_dir"], str(self.run_dir))
        self.assertFalse(sentinel.exists(), "User text was interpreted as PowerShell code")
        self.assertFalse((self.run_dir / ".lock").exists())
        self.assertIn("runner: OK", (self.run_dir / "runner.log").read_text(errors="replace"))

    def test_unknown_exit_code_preserved(self):
        result = self.invoke("dados insuficientes", exit_code=2)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("runner: UNKNOWN", (self.run_dir / "runner.log").read_text(errors="replace"))
        self.assertFalse((self.run_dir / ".lock").exists())

    def test_failure_exit_code_preserved(self):
        result = self.invoke("erro de execução", exit_code=7)
        self.assertEqual(result.returncode, 7, result.stdout + result.stderr)
        self.assertIn("runner: FAIL (7)", (self.run_dir / "runner.log").read_text(errors="replace"))
        self.assertFalse((self.run_dir / ".lock").exists())

    def test_existing_lock_fails_closed_without_running_tool(self):
        self.run_dir.mkdir(parents=True)
        (self.run_dir / ".lock").write_text("other runner", encoding="utf-8")
        result = self.invoke("não executar")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertFalse((self.run_dir / "argv.json").exists())
        self.assertEqual((self.run_dir / ".lock").read_text(encoding="utf-8"), "other runner")


if __name__ == "__main__":
    unittest.main()
