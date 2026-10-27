# README (short and practical)
# This project uses a TUDO-OU-NADA runner: if a required capability is missing, it exits with UNKNOWN.
# Use a venv and install Python dependencies first.

# Windows PowerShell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r nexus\requirements.txt

# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r nexus/requirements.txt

# Optional OS installs for real artifact generation
# Windows (Admin): choco install -y ffmpeg libreoffice openjdk
# Ubuntu/Debian: sudo apt install -y ffmpeg libreoffice default-jre

# Runner examples
python -m nexus.run_job --process convert_pdf --text "converte para PDF este documento" --run-dir ./runs/test-001
./scripts/runner.sh convert_pdf "converte para PDF este documento" ./runs/test-001
.\windows\runner.ps1 -process convert_pdf -text "converte para PDF este documento" -run_dir .\runs\test-001
