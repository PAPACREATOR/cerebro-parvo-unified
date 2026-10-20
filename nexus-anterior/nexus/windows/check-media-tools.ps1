[CmdletBinding()]
param(
    [string]$PythonPath,
    [int]$WaitSeconds = 90,
    [string]$ToolsRoot = 'C:\Nexus-Tools'
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$checker = Join-Path $PSScriptRoot 'check_media_tools.py'
if (-not (Test-Path -LiteralPath $checker)) { throw 'Verificador Nexus ausente.' }

if (-not $PythonPath) {
    $repoPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
    if (Test-Path -LiteralPath $repoPython) {
        $PythonPath = $repoPython
    } else {
        $cmd = Get-Command python.exe -CommandType Application -ErrorAction SilentlyContinue
        if (-not $cmd) { throw 'Python Nexus não encontrado. Indica -PythonPath.' }
        $PythonPath = $cmd.Source
    }
}
$PythonPath = (Get-Command $PythonPath -CommandType Application -ErrorAction Stop).Source

$null = New-Item -ItemType Directory -Force -Path $ToolsRoot
$ToolsRoot = (Resolve-Path -LiteralPath $ToolsRoot).Path
$reportPath = Join-Path $ToolsRoot 'media-health.json'
$stderrPath = Join-Path $ToolsRoot 'media-health.stderr.txt'

$raw = & $PythonPath $checker '--wait-seconds' ([string]$WaitSeconds) 2> $stderrPath
$code = $LASTEXITCODE
if (-not $raw) {
    throw 'O verificador não devolveu JSON.'
}
try {
    $value = ($raw -join [Environment]::NewLine) | ConvertFrom-Json
} catch {
    throw 'O verificador devolveu uma resposta inválida.'
}
($value | ConvertTo-Json -Depth 10) | Set-Content -LiteralPath $reportPath -Encoding UTF8

if ($code -ne 0 -or $value.status -ne 'PASS' -or $value.authority -ne 'NONE') {
    Write-Host 'NEXUS MEDIA HEALTH = FAIL'
    Write-Host ("Report: " + $reportPath)
    exit 1
}
Write-Host 'NEXUS MEDIA HEALTH = PASS'
Write-Host ("ACE-Step: " + $value.ace_step.endpoint)
Write-Host ("Forge: " + $value.forge.endpoint)
Write-Host ("Report: " + $reportPath)
exit 0
