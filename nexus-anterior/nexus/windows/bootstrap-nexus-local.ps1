[CmdletBinding()]
param(
    [string]$RepoRoot = '',
    [string]$ToolsRoot = 'C:\Nexus-Tools',
    [string]$Branch = '',
    [string]$ExpectedHead = '',
    [switch]$AuthorizePrepare
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if (-not $AuthorizePrepare) { throw 'NEXUS_PREPARE_AUTHORIZATION_REQUIRED' }
if ($ExpectedHead -cnotmatch '^[0-9a-f]{40}$') { throw 'NEXUS_EXPECTED_HEAD_REQUIRED' }

function Invoke-PowerShellChecked {
    param(
        [Parameter(Mandatory=$true)][string]$ScriptPath,
        [Parameter(Mandatory=$false)][string[]]$Arguments = @()
    )
    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        throw ('NEXUS_SCRIPT_NOT_FOUND: ' + $ScriptPath)
    }
    & powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $ScriptPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw ('NEXUS_STEP_FAILED: ' + (Split-Path $ScriptPath -Leaf))
    }
}

$repoFromScript = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$sync = Join-Path $PSScriptRoot 'sync-nexus-code.ps1'

$syncArgs = @('-ExpectedHead',$ExpectedHead)
if ($Branch) { $syncArgs += @('-Branch',$Branch) }
if ($RepoRoot) {
    $syncArgs += @('-RepoRoot',$RepoRoot)
}
Invoke-PowerShellChecked -ScriptPath $sync -Arguments $syncArgs

# After sync, resolve the authoritative checkout. If -RepoRoot was omitted,
# the script's own checkout is the only location this wrapper is allowed to use.
if ($RepoRoot) {
    $RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
} else {
    $RepoRoot = (Resolve-Path -LiteralPath $repoFromScript).Path
}

$prepare = Join-Path $RepoRoot 'nexus\windows\prepare-nexus-core.ps1'
Invoke-PowerShellChecked -ScriptPath $prepare -Arguments @('-RepoRoot',$RepoRoot,'-ToolsRoot',$ToolsRoot)

$inventory = Join-Path $RepoRoot 'nexus\windows\inventory-external-tools.ps1'
Invoke-PowerShellChecked -ScriptPath $inventory -Arguments @('-ToolsRoot',$ToolsRoot)

$plan = Join-Path $RepoRoot 'nexus\windows\plan-external-provisioning.ps1'
Invoke-PowerShellChecked -ScriptPath $plan -Arguments @('-ToolsRoot',$ToolsRoot)

$git = (Get-Command git.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$head = (& $git -C $RepoRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw 'NEXUS_HEAD_READ_FAILED' }

$inventoryReport = Join-Path $ToolsRoot 'external-tools-inventory.json'
if (-not (Test-Path -LiteralPath $inventoryReport)) {
    throw 'NEXUS_EXTERNAL_INVENTORY_MISSING'
}

$planReport = Join-Path $ToolsRoot 'external-provision-plan.json'
if (-not (Test-Path -LiteralPath $planReport)) {
    throw 'NEXUS_EXTERNAL_PLAN_MISSING'
}

$coreReport = Join-Path $ToolsRoot 'pc-core-report.json'
if (-not (Test-Path -LiteralPath $coreReport)) {
    throw 'NEXUS_CORE_REPORT_MISSING'
}
$core = Get-Content -LiteralPath $coreReport -Raw | ConvertFrom-Json
if ($core.status -ne 'PASS' -or $core.head -ne $head -or $head -ne $ExpectedHead) {
    throw 'NEXUS_CORE_REPORT_MISMATCH'
}
$dirty = & $git -C $RepoRoot status --porcelain --untracked-files=all
if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'NEXUS_DIRTY_TREE' }

# Reuse the existing thin launcher. The accepted HEAD is outside the checkout;
# a legitimate update renews it only through another authorized bootstrap.
$bin = Join-Path $ToolsRoot 'bin'
$null = New-Item -ItemType Directory -Force -Path $bin
$launcher = Join-Path $bin 'nexus-launcher.py'
Copy-Item -LiteralPath (Join-Path $RepoRoot 'nexus\windows\nexus-launcher.py') -Destination $launcher -Force
$python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
$pythonw = Join-Path $RepoRoot '.venv\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $python) -or -not (Test-Path -LiteralPath $pythonw)) {
    throw 'NEXUS_PREPARED_PYTHON_MISSING'
}
$launcherConfig = [ordered]@{
    repo_root = $RepoRoot
    python = $python
    git = $git
    data_root = (Join-Path $RepoRoot 'nexus\runtime')
    expected_origin = 'https://github.com/PAPACREATOR/cerebro-parvo-.git'
    expected_head = $ExpectedHead
}
$configPath = Join-Path $bin 'nexus-launcher.json'
$launcherConfig | ConvertTo-Json | Set-Content -LiteralPath $configPath -Encoding UTF8
$shortcutPath = Join-Path $ToolsRoot 'Nexus.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = '"' + $launcher + '"'
$shortcut.WorkingDirectory = $bin
$shortcut.Save()

$report = [ordered]@{
    schema = 'nexus.local-bootstrap.v1'
    status = 'PASS'
    checked_utc = [DateTime]::UtcNow.ToString('o')
    repository = $RepoRoot
    branch = $Branch
    head = $head
    core_report = $coreReport
    external_inventory = $inventoryReport
    external_plan = $planReport
    external_provisioning = 'BLOCKED_BY_POLICY'
    launcher = $shortcutPath
    launcher_binding = $configPath
    note = 'Code synchronized and Nexus core prepared/tested. Protected external provisioning was not bypassed.'
}
$reportPath = Join-Path $ToolsRoot 'local-bootstrap-report.json'
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8

Write-Host 'NEXUS LOCAL BOOTSTRAP = PASS'
Write-Host ('HEAD: ' + $head)
Write-Host ('REPORT: ' + $reportPath)
Write-Host 'External provisioning remains BLOCKED_BY_POLICY.'
