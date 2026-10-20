# Nexus Windows acceptance installer (isolated, non-production).
# This script never runs the full external-tools installer.
[CmdletBinding()]
param(
    [string]$ExpectedHead = '',
    [string]$WorkspaceRoot = '',
    [switch]$AuthorizeInstall,
    [switch]$CiRunnerElevationException
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT' -or -not [Environment]::Is64BitOperatingSystem) {
    throw 'NEXUS_TEST_WINDOWS_X64_REQUIRED'
}
if (-not $AuthorizeInstall) {
    throw 'NEXUS_TEST_EXPLICIT_AUTHORIZATION_REQUIRED: inspect this script, then add -AuthorizeInstall.'
}
if (-not $ExpectedHead) {
    $headFile = Join-Path $PSScriptRoot 'candidate-head.txt'
    if (-not (Test-Path -LiteralPath $headFile)) {
        throw 'NEXUS_TEST_EXPECTED_HEAD_REQUIRED'
    }
    $ExpectedHead = (Get-Content -LiteralPath $headFile -Raw).Trim()
}
if ($ExpectedHead -cnotmatch '^[0-9a-f]{40}$') {
    throw 'NEXUS_TEST_BAD_HEAD'
}
if (-not $WorkspaceRoot) {
    $WorkspaceRoot = Join-Path $env:LOCALAPPDATA 'Nexus-Acceptance'
}
$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$elevated = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($elevated -and -not $CiRunnerElevationException) {
    throw 'NEXUS_TEST_STANDARD_USER_REQUIRED: close elevated PowerShell and use a normal Windows session.'
}
$gitCmd = Get-Command 'git.exe' -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $gitCmd) { throw 'NEXUS_TEST_GIT_REQUIRED: install Git separately before continuing.' }
$git = $gitCmd.Source
$pythonCmd = Get-Command 'py.exe' -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
$pythonArgs = @()
if ($pythonCmd) {
    & $pythonCmd.Source -3.12 -c 'import sys; assert sys.version_info[:2] == (3, 12)' *> $null
    if ($LASTEXITCODE -eq 0) { $pythonArgs = @('-3.12') }
    else { $pythonCmd = $null }
}
if (-not $pythonCmd) {
    $pythonCmd = Get-Command 'python.exe' -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $pythonCmd) { throw 'NEXUS_TEST_PYTHON_312_REQUIRED' }
    & $pythonCmd.Source -c 'import sys; assert sys.version_info[:2] == (3, 12)' *> $null
    if ($LASTEXITCODE -ne 0) { throw 'NEXUS_TEST_PYTHON_312_REQUIRED' }
}
$python = $pythonCmd.Source
$origin = 'https://github.com/PAPACREATOR/cerebro-parvo-.git'
$workspace = [IO.Path]::GetFullPath($WorkspaceRoot)
$repoPath = Join-Path (Join-Path $workspace 'revisions') $ExpectedHead
$reportPath = Join-Path (Join-Path $workspace 'reports') $ExpectedHead
if (Test-Path -LiteralPath $repoPath) {
    throw ('NEXUS_TEST_ALREADY_EXISTS: no overwrite permitted at ' + $repoPath)
}
if (Test-Path -LiteralPath $reportPath) {
    throw ('NEXUS_TEST_REPORT_ALREADY_EXISTS: no overwrite permitted at ' + $reportPath)
}
$null = New-Item -ItemType Directory -Force -Path $reportPath
$null = New-Item -ItemType Directory -Force -Path (Split-Path $repoPath -Parent)
$report = [ordered]@{
    schema='nexus.windows-acceptance.v1'
    status='RUNNING'
    head=$ExpectedHead
    repository_origin=$origin
    elevated=$elevated
    ci_elevation_exception=[bool]$CiRunnerElevationException
    workspace=$workspace
    source=$repoPath
    started_utc=[DateTime]::UtcNow.ToString('o')
    finished_utc=$null
    checks=[ordered]@{}
    limits=@('Isolated user-space checkout and synthetic tests only.',
             'No system-wide install, no global permissions, no external tools or models provisioned.',
             'Writer/LibreOffice, physical PC and real OpenNotebook require separate acceptance.')
    error=$null
}
$stateFile = Join-Path $reportPath 'acceptance.json'
function Save-Report {
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $stateFile -Encoding UTF8
}
function Invoke-Logged {
    param([string]$Name, [string]$Executable, [string[]]$Arguments)
    $log = Join-Path $reportPath ($Name + '.log')
    # Windows PowerShell 5.1 exposes a native command's stderr as an ErrorRecord.
    # Git fetch writes harmless provenance to stderr even when its exit code is 0.
    # Capture both streams, then judge only the actual native process exit code.
    $previousPreference = $ErrorActionPreference
    $code = 1
    try {
        $ErrorActionPreference = 'Continue'
        & $Executable @Arguments *> $log
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousPreference
    }
    if ($code -ne 0) {
        $report.checks[$Name] = 'FAIL'
        Save-Report
        throw ('NEXUS_TEST_STEP_FAILED: ' + $Name + ' exit=' + $code + ' log=' + $log)
    }
    $report.checks[$Name] = 'PASS'
    Save-Report
}
$exitCode = 1
$previous = Get-Location
try {
    Save-Report
    Invoke-Logged 'git-init' $git @('init',$repoPath)
    Invoke-Logged 'git-origin' $git @('-C',$repoPath,'remote','add','origin',$origin)
    Invoke-Logged 'git-fetch-head' $git @('-C',$repoPath,'fetch','--no-tags','--depth','1','origin',$ExpectedHead)
    Invoke-Logged 'git-checkout' $git @('-C',$repoPath,'checkout','--detach',$ExpectedHead)
    $actual = (& $git -C $repoPath rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $actual -cne $ExpectedHead) { throw 'NEXUS_TEST_HEAD_MISMATCH' }
    $remote = (& $git -C $repoPath config --get remote.origin.url).Trim()
    if ($LASTEXITCODE -ne 0 -or $remote -cne $origin) { throw 'NEXUS_TEST_ORIGIN_MISMATCH' }
    $dirty = @(& $git -C $repoPath status --porcelain=v1 --untracked-files=all)
    $dirtyExit = $LASTEXITCODE
    if ($dirtyExit -ne 0 -or ($dirty -join '').Trim()) {
        # Diagnostic-only: retain bounded path/status evidence; never waive
        # the clean-source precondition or install from a dirty checkout.
        $report.checks['git-pin-and-clean'] = 'FAIL'
        $report['dirty_git_status'] = @($dirty | Select-Object -First 30)
        $report['dirty_git_exit_code'] = $dirtyExit
        Save-Report
        throw 'NEXUS_TEST_SOURCE_DIRTY'
    }
    $report.checks['git-pin-and-clean'] = 'PASS'
    Save-Report

    Set-Location -LiteralPath $repoPath
    $venv = Join-Path $repoPath '.venv'
    $venvArguments = @() + $pythonArgs + @('-m','venv',$venv)
    Invoke-Logged 'venv-python312' $python $venvArguments
    $venvPython = Join-Path $venv 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $venvPython)) { throw 'NEXUS_TEST_VENV_MISSING' }
    Invoke-Logged 'python-version' $venvPython @('-c','import sys; assert sys.version_info[:2] == (3,12)')
    Invoke-Logged 'install-minimal-requirements' $venvPython @(
        '-m','pip','install','--disable-pip-version-check','-r','nexus/requirements.txt','pytest==9.1.1'
    )
    Invoke-Logged 'verify-source-integrity' $venvPython @(
        '-c',"from nexus.host import verify_integrity; verify_integrity(); print('INTEGRITY=PASS')"
    )
    $junit = Join-Path $reportPath 'windows-tests.xml'
    Invoke-Logged 'windows-acceptance-tests' $venvPython @(
        '-m','pytest','-q','-p','no:cacheprovider','-o','pythonpath=.',
        'nexus/tests/test_final_candidate_guards.py',
        'nexus/tests/test_frontdoor_preexecution_gate.py',
        'nexus/tests/test_frontdoor_refusals.py',
        'nexus/tests/test_frontdoor_boundaries.py',
        'nexus/tests/test_frontdoor_host_boundary.py',
        'nexus/tests/test_store.py',
        'nexus/tests/test_reverse_flow.py',
        'nexus/tests/test_kernel_crash_contract.py',
        ('--junitxml=' + $junit)
    )
    $report.checks['real-windows-verify-route'] = 'PASS_IN_TESTS'
    $report.status = 'PASS_TESTABLE_CORE'
    $exitCode = 0
} catch {
    $report.status = 'FAIL'
    $report.error = $_.Exception.Message
} finally {
    Set-Location $previous
    $report.finished_utc = [DateTime]::UtcNow.ToString('o')
    Save-Report
    Write-Host ('NEXUS WINDOWS TEST INSTALL: ' + $report.status)
    Write-Host ('Expected HEAD: ' + $ExpectedHead)
    Write-Host ('Source: ' + $repoPath)
    Write-Host ('Report: ' + $stateFile)
    Write-Host 'Production release, Writer and external services: NOT APPROVED.'
}
exit $exitCode
