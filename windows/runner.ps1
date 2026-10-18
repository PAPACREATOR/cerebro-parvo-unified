# PowerShell runner for Windows
param(
    [Parameter(Mandatory=$true)][string]$process,
    [Parameter(Mandatory=$true)][string]$text,
    [Parameter(Mandatory=$true)][string]$run_dir
)
$lock = Join-Path $run_dir ".lock"
$log = Join-Path $run_dir "runner.log"
if (-not (Test-Path $run_dir)) { New-Item -ItemType Directory -Path $run_dir | Out-Null }
if (Test-Path $lock) {
    "Run already in progress (lock exists): $lock" | Out-File -FilePath $log -Append
    exit 1
}
# create lock
Set-Content -Path $lock -Value $PID
try {
    "runner start: $(Get-Date -Format o)" | Out-File -FilePath $log -Append
    "process: $process" | Out-File -FilePath $log -Append
    "text: $text" | Out-File -FilePath $log -Append
    $cmd = "python -m nexus.run_job --process \"$process\" --text \"$text\" --run-dir \"$run_dir\""
    iex $cmd 2>&1 | Tee-Object -FilePath $log -Append
    $rc = $LASTEXITCODE
    if ($rc -eq 0) { "runner: OK" | Out-File -FilePath $log -Append; exit 0 }
    elseif ($rc -eq 2) { "runner: UNKNOWN" | Out-File -FilePath $log -Append; exit 2 }
    else { "runner: FAIL ($rc)" | Out-File -FilePath $log -Append; exit $rc }
}
finally {
    Remove-Item -Path $lock -ErrorAction SilentlyContinue
}
