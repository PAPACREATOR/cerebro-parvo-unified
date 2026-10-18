# Windows runner: user text must remain an argument, never PowerShell code.
param(
    [Parameter(Mandatory=$true)][string]$process,
    [Parameter(Mandatory=$true)][string]$text,
    [Parameter(Mandatory=$true)][string]$run_dir
)
$lock = Join-Path $run_dir ".lock"
$log = Join-Path $run_dir "runner.log"
if (-not (Test-Path -LiteralPath $run_dir)) {
    New-Item -ItemType Directory -Path $run_dir | Out-Null
}
if (Test-Path -LiteralPath $lock) {
    "Run already in progress (lock exists): $lock" | Out-File -LiteralPath $log -Append
    exit 1
}
Set-Content -LiteralPath $lock -Value $PID
$requestTextFile = $null
try {
    "runner start: $(Get-Date -Format o)" | Out-File -LiteralPath $log -Append
    "process: $process" | Out-File -LiteralPath $log -Append

    # Resolve an application, not a user-defined function or PowerShell expression.
    $python = Get-Command python.exe -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $python) {
        "runner: FAIL (python.exe not found)" | Out-File -LiteralPath $log -Append
        exit 1
    }

    # Windows PowerShell 5.1 does not preserve embedded quotes in native argv.
    # Transfer the literal input as UTF-8 in a temporary data file, not a command.
    $requestTextFile = Join-Path $run_dir ("request-" + [guid]::NewGuid().ToString('N') + '.utf8')
    [System.IO.File]::WriteAllText($requestTextFile, $text, (New-Object System.Text.UTF8Encoding($false)))
    # Unicode-safe stdout even when Windows PowerShell inherits a legacy code page.
    $env:PYTHONIOENCODING = 'utf-8'
    & $python.Source -m nexus.run_job --process $process --text-file $requestTextFile --run-dir $run_dir 2>&1 |
        Tee-Object -FilePath $log -Append
    $rc = $LASTEXITCODE
    if ($null -eq $rc) { $rc = 1 }

    if ($rc -eq 0) {
        "runner: OK" | Out-File -LiteralPath $log -Append
        exit 0
    } elseif ($rc -eq 2) {
        "runner: UNKNOWN" | Out-File -LiteralPath $log -Append
        exit 2
    } else {
        "runner: FAIL ($rc)" | Out-File -LiteralPath $log -Append
        exit $rc
    }
} finally {
    if ($requestTextFile) { Remove-Item -LiteralPath $requestTextFile -ErrorAction SilentlyContinue }
    Remove-Item -LiteralPath $lock -ErrorAction SilentlyContinue
}
