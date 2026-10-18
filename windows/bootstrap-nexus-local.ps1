# Bootstrap script for Windows: create venv, install deps and start Nexus backend + gateway
param(
    [string]$RepoRoot = (Get-Location).Path,
    [int]$BackendPort = 5055,
    [int]$GatewayPort = 3000
)

Set-StrictMode -Version Latest

Write-Host "Bootstrap Nexus local - Repo: $RepoRoot" -ForegroundColor Cyan
Push-Location $RepoRoot

# Ensure python available
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found in PATH. Please install Python 3.12 and retry." -ForegroundColor Red
    exit 1
}

# Create venv
$venvPath = Join-Path $RepoRoot ".venv"
if (-not (Test-Path $venvPath)) {
    python -m venv $venvPath
}

# Activate and install
$activate = Join-Path $venvPath "Scripts/Activate.ps1"
. $activate

pip install --upgrade pip
pip install -r nexus/requirements.txt

# Start backend in background
Write-Host "Starting Nexus backend on port $BackendPort"
$env:NEXUS_BACKEND_PORT = $BackendPort
Start-Process -NoNewWindow -FilePath python -ArgumentList "nexus/app.py --port $BackendPort" -WorkingDirectory $RepoRoot

Start-Sleep -Seconds 2

# Start node gateway
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "Node.js not found in PATH. Please install Node.js to run the gateway." -ForegroundColor Yellow
} else {
    Write-Host "Starting Node gateway on port $GatewayPort"
    $env:PORT = $GatewayPort
    Start-Process -NoNewWindow -FilePath node -ArgumentList "server.js" -WorkingDirectory $RepoRoot
}

Write-Host "Bootstrap complete. Check logs or browser at http://127.0.0.1:$GatewayPort" -ForegroundColor Green
Pop-Location
