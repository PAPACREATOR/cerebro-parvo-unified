# Start only the already-tested isolated Nexus checkout and its separate data vault.
[CmdletBinding()]
param(
    [string]$ExpectedHead = '',
    [string]$WorkspaceRoot = ''
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'NEXUS_TEST_WINDOWS_REQUIRED' }
if (-not $ExpectedHead) {
    $file = Join-Path $PSScriptRoot 'candidate-head.txt'
    if (-not (Test-Path -LiteralPath $file)) { throw 'NEXUS_TEST_EXPECTED_HEAD_REQUIRED' }
    $ExpectedHead = (Get-Content -LiteralPath $file -Raw).Trim()
}
if ($ExpectedHead -cnotmatch '^[0-9a-f]{40}$') { throw 'NEXUS_TEST_INVALID_HEAD' }
if (-not $WorkspaceRoot) { $WorkspaceRoot = Join-Path $env:LOCALAPPDATA 'Nexus-Acceptance' }
$root = [IO.Path]::GetFullPath($WorkspaceRoot)
$repo = Join-Path (Join-Path $root 'revisions') $ExpectedHead
$report = Join-Path (Join-Path (Join-Path $root 'reports') $ExpectedHead) 'acceptance.json'
if (-not (Test-Path -LiteralPath $report)) { throw 'NEXUS_TEST_ACCEPTANCE_REPORT_MISSING' }
$state = Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
if ($state.status -cne 'PASS_TESTABLE_CORE' -or $state.head -cne $ExpectedHead -or $state.source -cne $repo) {
    throw 'NEXUS_TEST_CORE_NOT_APPROVED_FOR_LOCAL_TESTING'
}
$python = Join-Path $repo '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'NEXUS_TEST_PYTHON_MISSING' }
$git = (Get-Command 'git.exe' -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$head = (& $git -C $repo rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $head -cne $ExpectedHead) { throw 'NEXUS_TEST_HEAD_CHANGED' }
$origin = (& $git -C $repo config --get remote.origin.url).Trim()
if ($LASTEXITCODE -ne 0 -or $origin -cne 'https://github.com/PAPACREATOR/cerebro-parvo-.git') {
    throw 'NEXUS_TEST_WRONG_ORIGIN'
}
$dirty = @(& $git -C $repo status --porcelain=v1 --untracked-files=all)
if ($LASTEXITCODE -ne 0 -or ($dirty -join '').Trim()) { throw 'NEXUS_TEST_DIRTY_CHECKOUT' }
$previous = Get-Location
try {
    Set-Location -LiteralPath $repo
    & $python -c "from nexus.host import verify_integrity; verify_integrity(); print('INTEGRITY=PASS')"
    if ($LASTEXITCODE -ne 0) { throw 'NEXUS_TEST_INTEGRITY_FAILED' }
    $dataRoot = Join-Path (Join-Path $root 'data') $ExpectedHead
    $null = New-Item -ItemType Directory -Force -Path $dataRoot
    Write-Host ('Isolated Nexus source: ' + $repo)
    Write-Host ('Isolated data: ' + $dataRoot)
    Write-Host 'This is a local test build, NOT the final release.'
    & $python -m nexus.app --data $dataRoot
    if ($LASTEXITCODE -ne 0) { throw ('NEXUS_TEST_LAUNCH_FAILED: ' + $LASTEXITCODE) }
} finally {
    Set-Location $previous
}
