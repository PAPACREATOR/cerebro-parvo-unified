param(
    [switch]$UseChoco = $true,
    [switch]$UseWinget = $false
)

$ErrorActionPreference = 'Stop'

python -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r nexus\requirements.txt

Write-Host ""
Write-Host "=== Recomendado para artefactos reais ==="
Write-Host "- ffmpeg"
Write-Host "- LibreOffice (soffice)"
Write-Host "- OpenJDK / Java"
Write-Host ""
Write-Host "Se quiseres instalar via Chocolatey:"
Write-Host "  choco install -y ffmpeg libreoffice openjdk"
Write-Host ""
Write-Host "Se quiseres instalar via winget:"
Write-Host "  winget install --id Gyan.Dev.FFmpeg -e"
Write-Host "  winget install --id TheDocumentFoundation.LibreOffice -e"
Write-Host "  winget install --id Microsoft.OpenJDK.21 -e"
