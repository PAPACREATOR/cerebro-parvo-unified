"""Explicit install-time downloads; rendering itself is fully offline.

No checkpoint redistribution. Verify pinned upstream hashes before publishing
the downloaded files. gdown handles Google Drive confirmation pages.
"""
import argparse
import hashlib
import os
from pathlib import Path
import tempfile
import urllib.request


WAV2LIP_ID = "1qKU8HG8dR4nW4LvCqpEYmSy6LLpVkZ21"
WAV2LIP_SHA = "dc5b324a04a0e5b150a97422b68b79859e993e1fc1a3b4b87e2fd4a07cfd2e7a"
SFD_URL = "https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth"
# Filled from the same SFD weights used by face-alignment 1.5.0.
SFD_SHA = "619a31681264d3f7f7fc7a16a42cbbe8b23f31a256f75a366e5a1bcd59b33543"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):h.update(chunk)
    return h.hexdigest()


def provision(root, *, authorize_install=False):
    if os.name == "nt" and authorize_install is not True:
        raise RuntimeError("NEXUS_INSTALL_AUTHORIZATION_REQUIRED: protected model provisioning requires explicit human-authorized installation.")
    import gdown
    root.mkdir(parents=True, exist_ok=True)
    for name, expected in [("wav2lip.pth", WAV2LIP_SHA), ("s3fd.pth", SFD_SHA)]:
        target = root / name
        if target.exists():
            if target.is_symlink() or sha(target) != expected:
                raise ValueError("Existing checkpoint differs: " + name)
            print(name + " VERIFIED")
            continue
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            staging = Path(tmp) / name
            if name == "wav2lip.pth":
                if not gdown.download(id=WAV2LIP_ID, output=str(staging), quiet=False):
                    raise RuntimeError("Wav2Lip download failed")
            else:
                with urllib.request.urlopen(SFD_URL, timeout=30) as response, staging.open("wb") as stream:
                    total = 0
                    for chunk in iter(lambda: response.read(1024 * 1024), b""):
                        total += len(chunk)
                        if total > 100_000_000:raise ValueError("SFD download exceeds limit")
                        stream.write(chunk)
            if sha(staging) != expected:
                raise ValueError("Downloaded checkpoint differs: " + name)
            staging.rename(target)
            print(name + " VERIFIED")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    parser.add_argument("--authorize-install", action="store_true")
    args = parser.parse_args()
    provision(args.directory, authorize_install=args.authorize_install)
