"""Real Git checkouts; application spawning is observed, never performed."""
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


SOURCE = Path(__file__).resolve().parents[1] / "windows/nexus-launcher.py"
ORIGIN = "https://github.com/PAPACREATOR/cerebro-parvo-.git"


def git(repo, *args):
    completed = subprocess.run([shutil.which("git"), "-C", str(repo), *args],
                               text=True, capture_output=True, timeout=15)
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


@pytest.fixture
def installed(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "nexus").mkdir(parents=True)
    (repo / "nexus/app.py").write_text("# synthetic checkout\n", encoding="utf-8")
    git(repo, "init")
    git(repo, "config", "user.name", "Nexus Test")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "accepted")
    git(repo, "remote", "add", "origin", ORIGIN)
    accepted = git(repo, "rev-parse", "HEAD")
    install = tmp_path / "install"
    install.mkdir()
    spec = importlib.util.spec_from_file_location("nexus_launcher_test", SOURCE)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    failures, spawns = [], []
    monkeypatch.setattr(launcher, "__file__", str(install / SOURCE.name))
    monkeypatch.setattr(launcher, "os", SimpleNamespace(name="nt"))
    monkeypatch.setattr(launcher, "fail", lambda message: failures.append(message) or 1)
    # Git subprocesses are real on both OSes; Windows launch flags are irrelevant
    # to this platform-independent contract. The native Host has its own gate.
    monkeypatch.setattr(launcher, "subprocess", SimpleNamespace(
        check_output=subprocess.check_output, CREATE_NO_WINDOW=0,
        CREATE_NEW_PROCESS_GROUP=0, DEVNULL=subprocess.DEVNULL,
        Popen=lambda *args, **kwargs: spawns.append((args, kwargs)) or SimpleNamespace(pid=1)))
    config = {
        "repo_root": str(repo), "python": sys.executable,
        "git": shutil.which("git"), "data_root": str(tmp_path / "data"),
        "expected_origin": ORIGIN,
    }
    def save(value):
        (install / "nexus-launcher.json").write_text(json.dumps(value), encoding="utf-8")
    save(config)
    return SimpleNamespace(repo=repo, launcher=launcher, config=config, head=accepted,
                           save=save, failures=failures, spawns=spawns)


@pytest.mark.parametrize("change", ["none", "dirty", "head"])
def test_legacy_launcher_without_accepted_head_is_blocked(installed, change):
    if change != "none":
        (installed.repo / "nexus/app.py").write_text("# changed\n", encoding="utf-8")
        if change == "head":
            git(installed.repo, "add", ".")
            git(installed.repo, "commit", "-m", "unaccepted")
    assert installed.launcher.main() == 1
    assert not installed.spawns


def test_exact_accepted_checkout_is_the_only_launch_target(installed):
    installed.save(dict(installed.config, expected_head=installed.head))
    assert installed.launcher.main() == 0, installed.failures
    assert len(installed.spawns) == 1
    command = installed.spawns[0][0][0]
    assert command[:3] == [str(Path(installed.config["python"]).resolve()), "-m", "nexus.app"]


def test_powershell_utf8_bom_configuration_launches_the_accepted_head(installed):
    installed.save(dict(installed.config, expected_head=installed.head))
    target = Path(installed.launcher.__file__).parent / "nexus-launcher.json"
    target.write_bytes(b"\xef\xbb\xbf" + target.read_bytes())
    assert installed.launcher.main() == 0, installed.failures
    assert len(installed.spawns) == 1


def test_origin_cannot_be_redefined_by_launcher_configuration(installed):
    replacement = "https://example.invalid/repo.git"
    git(installed.repo, "remote", "set-url", "origin", replacement)
    installed.save(dict(installed.config, expected_head=installed.head, expected_origin=replacement))
    assert installed.launcher.main() == 1
    assert not installed.spawns


@pytest.mark.parametrize("change", ["tracked", "untracked", "head", "wrong-origin"])
def test_bound_launcher_rejects_unaccepted_or_dirty_checkout(installed, change):
    installed.save(dict(installed.config, expected_head=installed.head))
    if change == "wrong-origin":
        git(installed.repo, "remote", "set-url", "origin", "https://example.invalid/repo.git")
    elif change == "untracked":
        (installed.repo / "unreviewed.py").write_text("# untracked\n", encoding="utf-8")
    else:
        (installed.repo / "nexus/app.py").write_text("# changed\n", encoding="utf-8")
        if change == "head":
            git(installed.repo, "add", ".")
            git(installed.repo, "commit", "-m", "unaccepted")
    assert installed.launcher.main() == 1
    assert not installed.spawns


def test_legitimate_update_requires_explicit_new_head_binding(installed):
    (installed.repo / "nexus/app.py").write_text("# reviewed update\n", encoding="utf-8")
    git(installed.repo, "add", ".")
    git(installed.repo, "commit", "-m", "reviewed update")
    installed.save(dict(installed.config, expected_head=installed.head))
    assert installed.launcher.main() == 1
    installed.save(dict(installed.config, expected_head=git(installed.repo, "rev-parse", "HEAD")))
    assert installed.launcher.main() == 0, installed.failures
    assert len(installed.spawns) == 1


@pytest.mark.parametrize("config", [None, [], "invalid", 1, {}])
def test_malformed_launcher_config_fails_closed(installed, config):
    installed.save(config)
    assert installed.launcher.main() == 1
    assert not installed.spawns
