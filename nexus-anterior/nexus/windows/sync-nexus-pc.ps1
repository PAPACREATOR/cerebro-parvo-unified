[CmdletBinding()]
param(
    [string]$Branch = 'lab-open-notebook-avatar-20261004',
    [string]$ToolsRoot = 'C:\Nexus-Tools',
    [switch]$SkipMediaInstall,
    [switch]$SkipMediaStart
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Stop before any command, prompt, directory or external operation.
throw 'NEXUS_PROTECTED_PROVISIONING_PENDING: protected provisioning is not validated; refusing changes and external processes.'

# Historical implementation retained below; unreachable while this gate is closed.

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

$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot '.git'))) {
    throw 'Executa este script dentro do checkout Git oficial do Nexus.'
}

$git = (Get-Command git.exe -CommandType Application -ErrorAction Stop).Source
$py = (Get-Command py.exe -CommandType Application -ErrorAction Stop).Source

Push-Location -LiteralPath $repoRoot
try {
    $origin = (& $git remote get-url origin).Trim()
    if ($LASTEXITCODE -ne 0 -or $origin -notmatch 'PAPACREATOR/cerebro-parvo-(\.git)?$') {
        throw 'O checkout não aponta para o repositório oficial esperado.'
    }

    $dirty = & $git status --porcelain
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível verificar o estado Git.' }
    if ($dirty) {
        throw 'A árvore Git tem alterações locais. O script recusou atualizar para não perder trabalho.'
    }

    Invoke-Checked $git @('fetch','--prune','origin',$Branch) $repoRoot

    & $git show-ref --verify --quiet "refs/heads/$Branch"
    $localExists = ($LASTEXITCODE -eq 0)
    if ($localExists) {
        Invoke-Checked $git @('switch',$Branch) $repoRoot
    }
    else {
        Invoke-Checked $git @('switch','--track','-c',$Branch,"origin/$Branch") $repoRoot
    }
    Invoke-Checked $git @('merge','--ff-only',"origin/$Branch") $repoRoot

    $head = (& $git rev-parse HEAD).Trim()
    $remote = (& $git rev-parse "origin/$Branch").Trim()
    if ($LASTEXITCODE -ne 0 -or $head -ne $remote) {
        throw 'O checkout local não ficou igual ao HEAD remoto da branch.'
    }

    $venv = Join-Path $repoRoot '.venv'
    $python = Join-Path $venv 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) {
        Invoke-Checked $py @('-3.12','-m','venv',$venv) $repoRoot
    }
    Invoke-Checked $python @('-m','pip','install','-r','nexus/requirements-test.txt') $repoRoot

    $null = New-Item -ItemType Directory -Force -Path $ToolsRoot
    $ToolsRoot = (Resolve-Path -LiteralPath $ToolsRoot).Path
    $reportsRoot = Join-Path $ToolsRoot 'reports'
    $null = New-Item -ItemType Directory -Force -Path $reportsRoot
    $stamp = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')
    $nexusReport = Join-Path $reportsRoot ("nexus-" + $stamp)

    $checkNexus = Join-Path $repoRoot 'nexus\windows\check-nexus.ps1'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $checkNexus -PythonPath $python -Suite all -ReportDirectory $nexusReport
    if ($LASTEXITCODE -ne 0) { throw 'A validação Nexus local falhou.' }

    if (-not $SkipMediaInstall) {
        $installMedia = Join-Path $repoRoot 'nexus\windows\install-media-tools.ps1'
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installMedia -ToolsRoot $ToolsRoot
        if ($LASTEXITCODE -ne 0) { throw 'A instalação ACE-Step/Forge falhou.' }
    }

    if (-not $SkipMediaStart) {
        $aceLauncher = Join-Path $ToolsRoot 'bin\Start-ACE-Step-Nexus.cmd'
        $forgeLauncher = Join-Path $ToolsRoot 'bin\Start-Forge-Nexus.cmd'
        if (-not (Test-Path -LiteralPath $aceLauncher) -or -not (Test-Path -LiteralPath $forgeLauncher)) {
            throw 'Launchers ACE-Step/Forge ausentes.'
        }
        Start-Process -FilePath $aceLauncher -WindowStyle Minimized
        Start-Sleep -Seconds 2
        Start-Process -FilePath $forgeLauncher -WindowStyle Minimized

        $health = Join-Path $repoRoot 'nexus\windows\check-media-tools.ps1'
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $health -PythonPath $python -WaitSeconds 180 -ToolsRoot $ToolsRoot
        if ($LASTEXITCODE -ne 0) { throw 'ACE-Step/Forge não passaram o health check físico.' }
    }

    $report = [ordered]@{
        status = 'PASS'
        checked_utc = [DateTime]::UtcNow.ToString('o')
        repository = $origin
        branch = $Branch
        head = $head
        single_checkout = $repoRoot
        nexus_report = $nexusReport
        media_report = (Join-Path $ToolsRoot 'media-health.json')
        note = 'Uma única árvore de trabalho; Git conserva o histórico/fallback.'
    }
    $reportPath = Join-Path $ToolsRoot 'pc-bootstrap.json'
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8
    Write-Host 'NEXUS PC = PASS'
    Write-Host ("HEAD: " + $head)
    Write-Host ("Report: " + $reportPath)
}
finally {
    Pop-Location
}
