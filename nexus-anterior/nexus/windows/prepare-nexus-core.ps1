[CmdletBinding()]
param(
    [string]$RepoRoot = '',
    [string]$ToolsRoot = 'C:\Nexus-Tools'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-Checked {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [Parameter(Mandatory=$false)][string[]]$Arguments = @(),
        [Parameter(Mandatory=$false)][string]$WorkingDirectory
    )
    $old = Get-Location
    try {
        if ($WorkingDirectory) { Set-Location -LiteralPath $WorkingDirectory }
        & $FilePath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "$FilePath exited with code $LASTEXITCODE"
        }
    }
    finally {
        Set-Location $old
    }
}

if (-not $RepoRoot) {
    $RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
}
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.git'))) {
    throw 'NEXUS_REPOSITORY_NOT_FOUND'
}

$git = (Get-Command git.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$origin = (& $git -C $RepoRoot config --get remote.origin.url).Trim()
if ($LASTEXITCODE -ne 0 -or $origin -ne 'https://github.com/PAPACREATOR/cerebro-parvo-.git') {
    throw 'NEXUS_WRONG_ORIGIN'
}
$dirty = & $git -C $RepoRoot status --porcelain
if ($LASTEXITCODE -ne 0) { throw 'NEXUS_GIT_STATUS_FAILED' }
if ($dirty) { throw 'NEXUS_DIRTY_TREE' }

$py = Get-Command py.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
$pythonCmd = $null
if ($py) {
    & $py.Source -3.12 -c "import sys; assert sys.version_info[:2] == (3,12)"
    if ($LASTEXITCODE -eq 0) { $pythonCmd = @($py.Source, '-3.12') }
}
if (-not $pythonCmd) {
    $python = Get-Command python.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($python) {
        & $python.Source -c "import sys; assert sys.version_info[:2] == (3,12)"
        if ($LASTEXITCODE -eq 0) { $pythonCmd = @($python.Source) }
    }
}
if (-not $pythonCmd) {
    throw 'NEXUS_PYTHON_312_REQUIRED: instala Python 3.12 antes de continuar.'
}

$venv = Join-Path $RepoRoot '.venv'
$venvPython = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    if ($pythonCmd.Count -eq 2) {
        Invoke-Checked $pythonCmd[0] @($pythonCmd[1], '-m', 'venv', $venv) $RepoRoot
    } else {
        Invoke-Checked $pythonCmd[0] @('-m', 'venv', $venv) $RepoRoot
    }
}
Invoke-Checked $venvPython @('-c', 'import sys; assert sys.version_info[:2] == (3,12)') $RepoRoot
Invoke-Checked $venvPython @('-m','pip','install','--disable-pip-version-check','-r','nexus/requirements-test.txt') $RepoRoot

$null = New-Item -ItemType Directory -Force -Path $ToolsRoot
$ToolsRoot = (Resolve-Path -LiteralPath $ToolsRoot).Path
$reports = Join-Path $ToolsRoot 'reports'
$null = New-Item -ItemType Directory -Force -Path $reports
$stamp = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')
$reportRoot = Join-Path $reports ("pc-core-" + $stamp)
$null = New-Item -ItemType Directory -Force -Path $reportRoot

$check = Join-Path $RepoRoot 'nexus\windows\check-nexus.ps1'
$suites = @('core','blocks','practical','all')
$results = [ordered]@{}
foreach ($suite in $suites) {
    $suiteReport = Join-Path $reportRoot $suite
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $check -PythonPath $venvPython -Suite $suite -ReportDirectory $suiteReport
    $code = $LASTEXITCODE
    $statePath = Join-Path $suiteReport 'state.json'
    $state = if (Test-Path -LiteralPath $statePath) { Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json } else { $null }
    $results[$suite] = [ordered]@{
        exit_code = $code
        status = if ($state) { $state.status } else { 'MISSING_REPORT' }
        report = $suiteReport
    }
    if ($code -ne 0 -or -not $state -or $state.status -ne 'PASS') {
        throw ("NEXUS_SUITE_FAILED: " + $suite)
    }
}

$security = @(
    'nexus/security_tests/test_authority_10000.py',
    'nexus/security_tests/test_state_concurrency.py',
    'nexus/security_tests/test_install_gate.py',
    'nexus/security_tests/test_native_boundary.py',
    'nexus/security_tests/test_windows_hash.py',
    'nexus/security_tests/test_confinement_gate.py',
    'nexus/tests/test_reverse_flow.py',
    'nexus/tests/test_open_notebook_kernel_e2e.py'
)
$securityLog = Join-Path $reportRoot 'security.stdout.txt'
$securityErr = Join-Path $reportRoot 'security.stderr.txt'
$securityArgs = @('-m','pytest') + $security + @('-q','-o','pythonpath=.')
$proc = Start-Process -FilePath $venvPython -ArgumentList $securityArgs -WorkingDirectory $RepoRoot -RedirectStandardOutput $securityLog -RedirectStandardError $securityErr -PassThru -Wait -NoNewWindow
if ($proc.ExitCode -ne 0) {
    throw 'NEXUS_SECURITY_GATE_FAILED'
}

$guarded = @(
    'nexus\windows\sync-nexus-pc.ps1',
    'nexus\windows\install-media-tools.ps1',
    'nexus\lab\open_notebook_avatar\install-windows.ps1',
    'nexus\windows\setup-isolation.ps1'
)
$guardStatus = [ordered]@{}
foreach ($relative in $guarded) {
    $path = Join-Path $RepoRoot $relative
    $text = Get-Content -LiteralPath $path -Raw
    $guardStatus[$relative] = if ($text -match 'NEXUS_PROTECTED_PROVISIONING_PENDING') { 'BLOCKED_BY_POLICY' } else { 'REVIEW_REQUIRED' }
}

$external = [ordered]@{
    ace_step = if (Test-Path -LiteralPath (Join-Path $ToolsRoot 'ACE-Step-1.5')) { 'PRESENT_NOT_STARTED' } else { 'MISSING_BLOCKED_BY_POLICY' }
    forge = if (Test-Path -LiteralPath (Join-Path $ToolsRoot 'Forge')) { 'PRESENT_NOT_STARTED' } else { 'MISSING_BLOCKED_BY_POLICY' }
    open_notebook = 'VERIFY_SEPARATELY'
    libreoffice = if (Get-Command soffice.exe -CommandType Application -ErrorAction SilentlyContinue) { 'FOUND_IN_PATH' } else { 'VERIFY_SEPARATELY' }
    zotero = 'VERIFY_SEPARATELY'
}

$head = (& $git -C $RepoRoot rev-parse HEAD).Trim()
$report = [ordered]@{
    schema = 'nexus.pc-core.v1'
    status = 'PASS'
    checked_utc = [DateTime]::UtcNow.ToString('o')
    repository = $RepoRoot
    head = $head
    python = $venvPython
    suites = $results
    security = [ordered]@{ status = 'PASS'; stdout = $securityLog; stderr = $securityErr }
    provisioning = $guardStatus
    external_tools = $external
    note = 'Nexus core prepared and tested. Guarded external provisioning was not bypassed.'
}
$reportPath = Join-Path $ToolsRoot 'pc-core-report.json'
$report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportPath -Encoding UTF8

Write-Host 'NEXUS PC CORE = PASS'
Write-Host ('HEAD: ' + $head)
Write-Host ('REPORT: ' + $reportPath)
Write-Host 'External provisioning remains BLOCKED_BY_POLICY where the guard is present.'
