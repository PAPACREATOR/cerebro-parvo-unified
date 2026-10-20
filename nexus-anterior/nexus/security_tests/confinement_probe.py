"""Disposable canary worker; never accepts paths outside a marked test area."""
import errno
import json
import os
from pathlib import Path
import sys


def probe(work):
    # Host already canonicalized this assigned path before applying native ACLs.
    # GetFinalPathNameByHandle can demand reads of unassigned ancestors; compare
    # the actual cwd and marked work directly without expanding any target rights.
    work = Path(work).absolute()
    if Path.cwd() != work:
        raise ValueError("Probe is not in its assigned work area")
    root = Path((work / "probe-root.txt").read_text(encoding="utf-8"))
    if (work / "TEST-AREA-ONLY").read_text() != "nexus-disposable-confinement-v1":
        raise ValueError("Not a marked disposable test area")
    manifest = json.loads((work / "probe-input.json").read_text())
    observations = {}
    for item in manifest:
        path = root / item["path"]
        if not path.is_relative_to(root) or path == root:
            raise ValueError("Probe path escapes disposable area")
        action = item["action"]
        try:
            if action == "read":
                path.read_bytes()
            elif action == "overwrite":
                path.write_bytes(b"unauthorized-canary-change")
            elif action == "create":
                with path.open("xb") as stream:
                    stream.write(b"unauthorized-canary-create")
            elif action == "delete":
                path.unlink()
            elif action == "rename":
                path.rename(path.with_name(path.name + ".moved"))
            elif action == "mkdir":
                path.mkdir()
            else:
                raise ValueError("Unknown action")
            outcome = "ALLOWED"
        except OSError as error:
            # Missing paths, sharing violations and unrelated I/O errors are not PASS.
            winerror = getattr(error, "winerror", None)
            denied = winerror == 5 or (winerror is None and error.errno in (errno.EACCES, errno.EPERM))
            outcome = "DENIED" if denied else "ERROR:" + type(error).__name__
        observations[item["name"]] = outcome
    return observations


if __name__ == "__main__":
    results = probe(sys.argv[1])
    # The cwd is the Host-assigned run directory. No callback or network traffic.
    Path("confinement-observations.json").write_text(json.dumps(results), encoding="utf-8")
    print(json.dumps(results))  # Rejected envelope; OS must already have denied side effects.
