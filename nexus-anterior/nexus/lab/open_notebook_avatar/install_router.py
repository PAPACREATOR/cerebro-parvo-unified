"""Add the optional router to a local Open Notebook 1.15.0 source checkout.

Run after installing this package in Open Notebook's environment. Preserves a
backup, checks syntax before replacing, and is idempotent. No dependency install
or service restart is hidden in this operation.
"""
import argparse
import ast
import os
from pathlib import Path
import tempfile
import tomllib

MARKER = "# Nexus optional Open Notebook avatar extension"
BLOCK = '\n' + MARKER + '\nfrom notebook_avatar.router import router as avatar_router\napp.include_router(avatar_router, prefix="/api", tags=["podcast-avatar"])\n'


def install(root: Path):
    version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    if version != "1.15.0":
        raise ValueError("This installer is validated for Open Notebook 1.15.0 only")
    target = root / "api/main.py"
    text = target.read_text(encoding="utf-8")
    if BLOCK in text:
        return "ALREADY_INSTALLED"
    if MARKER in text or 'app.include_router(podcasts.router, prefix="/api", tags=["podcasts"])' not in text:
        raise ValueError("Unexpected API layout; refusing to rewrite")
    anchor = 'app.include_router(podcasts.router, prefix="/api", tags=["podcasts"])'
    result = text.replace(anchor, anchor + BLOCK, 1)
    ast.parse(result)
    backup = target.with_suffix(".py.pre-avatar")
    with backup.open("xb") as stream:
        stream.write(target.read_bytes())
    fd, name = tempfile.mkstemp(dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(result)
        os.replace(name, target)
    finally:
        Path(name).unlink(missing_ok=True)
    return "INSTALLED"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("open_notebook_root", type=Path)
    print(install(parser.parse_args().open_notebook_root.resolve()))
