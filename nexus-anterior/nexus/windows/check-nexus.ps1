[CmdletBinding()]
param(
    [string]$PythonPath,
    [ValidateSet('core','blocks','all','practical')]
    [string]$Suite = 'all',
    [string]$ReportDirectory = (Join-Path $env:TEMP ('nexus-check-' + [guid]::NewGuid().ToString('N')))
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$report = [ordered]@{
    status = 'RUNNING'; stage = 'START'; started_utc = [DateTime]::UtcNow.ToString('o')
    finished_utc = $null; commit = $null; error = $null; suite = $Suite
    scope = 'Repository/Lab tests; practical suite only covers currently automated real-Windows contracts'
}
$exitCode = 1
$locationPushed = $false
# Refuse to overwrite a previous report.
if (Test-Path -LiteralPath $ReportDirectory) { throw 'Report directory already exists. Choose a new path.' }
$null = New-Item -ItemType Directory -Path $ReportDirectory
$ReportDirectory = (Resolve-Path -LiteralPath $ReportDirectory).Path
$reportPath = Join-Path $ReportDirectory 'state.json'
function Save-State {
    $report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $reportPath -Encoding UTF8
}
function Invoke-PythonStep {
    param([string]$Stage, [string[]]$Arguments)
    $report.stage = $Stage
    Save-State
    & $script:PythonPath @Arguments > (Join-Path $ReportDirectory ($Stage + '.stdout.txt')) 2> (Join-Path $ReportDirectory ($Stage + '.stderr.txt'))
    if ($LASTEXITCODE -ne 0) { throw "$Stage failed (exit $LASTEXITCODE). See report files." }
}
try {
    Save-State
    Push-Location -LiteralPath $repoRoot
    $locationPushed = $true
    $report.stage = 'PREREQUISITES'
    if (-not (Test-Path -LiteralPath 'nexus/requirements-test.txt')) { throw 'Nexus repository not found.' }
    $commit = & git rev-parse HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Cannot identify Git commit.' }
    $report.commit = "$commit".Trim()
    if (-not $PythonPath) {
        $report.stage = 'CREATE_ENVIRONMENT'
        Save-State
        $venv = Join-Path $ReportDirectory 'venv'
        & py -3.12 -m venv $venv > (Join-Path $ReportDirectory 'venv.stdout.txt') 2> (Join-Path $ReportDirectory 'venv.stderr.txt')
        if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 environment creation failed.' }
        $PythonPath = Join-Path $venv 'Scripts/python.exe'
        Invoke-PythonStep -Stage 'DEPENDENCIES' -Arguments @('-m', 'pip', 'install', '-r', 'nexus/requirements-test.txt')
    }
    $PythonPath = (Get-Command $PythonPath -CommandType Application -ErrorAction Stop).Source
    Invoke-PythonStep -Stage 'PYTHON_VERSION' -Arguments @('-c', 'import sys; assert sys.version_info[:2] == (3, 12), sys.version; print(sys.version)')
    Invoke-PythonStep -Stage 'INTEGRITY' -Arguments @('-c', "from nexus.host import verify_integrity; verify_integrity(); print('INTEGRITY=PASS')")

    $targets = switch ($Suite) {
        'core' { @(
            'nexus/tests/test_store.py',
            'nexus/tests/test_host.py',
            'nexus/tests/test_startup.py',
            'nexus/tests/test_kernel_crash_contract.py',
            'nexus/tests/test_kernel_review.py',
            'nexus/tests/test_reverse_flow.py',
            'nexus/tests/test_vaults.py',
            'nexus/tests/test_schema_consistency.py',
            'nexus/tests/test_adversarial.py'
        ) }
        'blocks' { @(
            'nexus/tests/test_workflows.py',
            'nexus/tests/test_windows_hash_environment.py',
            'nexus/tests/test_languagetool.py',
            'nexus/tests/test_office.py',
            'nexus/tests/test_notebook.py',
            'nexus/tests/test_multimedia.py'
        ) }
        'practical' { @(
            'nexus/tests/test_workflows.py::test_real_redundant_workflow',
            'nexus/tests/test_windows_hash_environment.py',
            'nexus/tests/test_reverse_flow.py::test_real_windows_result_back_to_original_and_folha_after_restart',
            'nexus/tests/test_multimedia.py::test_python_reader_reads_family',
            'nexus/tests/test_lab_practical_boundaries.py',
            'nexus/tests/test_open_notebook_kernel_e2e.py',
            'nexus/tests/test_media_tools.py',
            'nexus/tests/test_media_tools_mcp.py',
            'nexus/tests/test_media_tools_checker.py',
            'nexus/tests/test_pc_sync.py',
            'nexus/tests/test_code_sync.py',
            'nexus/tests/test_code_sync_functional.py',
            'nexus/tests/test_prepare_nexus_core.py',
            'nexus/tests/test_bootstrap_nexus_local.py',
            'nexus/tests/test_external_inventory.py',
            'nexus/tests/test_external_provision_plan.py',
            'nexus/tests/test_external_inventory_functional.py',
            'nexus/tests/test_repository_syntax_audit.py'
        ) }
        default { @('nexus/tests') }
    }
    $pytestArgs = @('-m', 'pytest') + $targets + @(
        '-q', '--color=no', '-p', 'no:cacheprovider', '-o', 'pythonpath=.',
        ('--junitxml=' + (Join-Path $ReportDirectory 'tests.xml'))
    )
    $testStage = if ($Suite -eq 'all') { 'TESTS' } else { 'TESTS-' + $Suite.ToUpperInvariant() }
    Invoke-PythonStep -Stage $testStage -Arguments $pytestArgs
    $report.status = 'PASS'
    $report.stage = 'COMPLETE'
    $exitCode = 0
} catch {
    $report.status = 'FAIL'
    $report.error = $_.Exception.Message
} finally {
    $report.finished_utc = [DateTime]::UtcNow.ToString('o')
    Save-State
    if ($locationPushed) { Pop-Location }
    Write-Host ("NEXUS " + $report.status + " | " + $report.stage)
    Write-Host ("Report: " + $reportPath)
}
exit $exitCode
