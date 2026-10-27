#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv || true
source .venv/bin/activate || . .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r nexus/requirements.txt

# Suggest OS package installs when needed.
cat <<'EOF'

=== Recomendado para artefactos reais ===
- ffmpeg
- libreoffice (soffice)
- openjdk / default-jre

Ubuntu/Debian:
  sudo apt update
  sudo apt install -y ffmpeg libreoffice default-jre

macOS (Homebrew):
  brew install ffmpeg libreoffice openjdk
EOF
