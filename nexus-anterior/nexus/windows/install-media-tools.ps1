[CmdletBinding()]
param(
    [string]$ToolsRoot = 'C:\Nexus-Tools',
    [switch]$SkipAceStep,
    [switch]$SkipForge,
    [switch]$AuthorizeInstall
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

# Explicit human-authorized installation gate. Accidental/direct invocation remains fail-closed.
if (-not $AuthorizeInstall) {
    throw 'NEXUS_INSTALL_AUTHORIZATION_REQUIRED: rerun with -AuthorizeInstall only after explicit human approval.'
}


$AceRepo = 'https://github.com/ace-step/ACE-Step-1.5.git'
$AceCommit = 'ca1e85fe9430179831e6bc6be790c332190a3866'
$AceLicense = 'MIT'
$ForgeRepo = 'https://github.com/lllyasviel/stable-diffusion-webui-forge.git'
$ForgeCommit = 'dfdcbab685e57677014f05a3309b48cc87383167'
$ForgeLicense = 'AGPL-3.0'
$DeforumRepo = 'https://github.com/deforum/sd-forge-deforum.git'
$DeforumCommit = 'd9426c121eddadc76648be20034bc087acd0240c'
$DeforumLicense = 'AGPL-3.0'
$AcePort = 8001
$ForgePort = 7861

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

function Ensure-Command {
    param(
        [Parameter(Mandatory=$true)][string]$Name,
        [Parameter(Mandatory=$true)][string]$WingetId
    )
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if (-not $winget) {
        throw "$Name is required and winget.exe is unavailable."
    }
    Invoke-Checked $winget.Source @('install','--id',$WingetId,'-e','--accept-package-agreements','--accept-source-agreements')
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) {
        # winget may update PATH only for a new process.
        if ($Name -eq 'uv') {
            $known = @(
                (Join-Path $env:USERPROFILE '.local\bin\uv.exe'),
                (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\uv.exe')
            )
            $found = $known | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
            if ($found) { return $found }
        }
        throw "$Name was installed but is not visible in this PowerShell session."
    }
    return $cmd.Source
}

function Install-PinnedRepo {
    param(
        [Parameter(Mandatory=$true)][string]$Git,
        [Parameter(Mandatory=$true)][string]$Url,
        [Parameter(Mandatory=$true)][string]$Commit,
        [Parameter(Mandatory=$true)][string]$Destination
    )
    if (Test-Path -LiteralPath $Destination) {
        if (-not (Test-Path -LiteralPath (Join-Path $Destination '.git'))) {
            throw "Existing path is not a Git checkout: $Destination"
        }
        $dirty = (& $Git -C $Destination status --porcelain)
        if ($LASTEXITCODE -ne 0) { throw "Cannot inspect $Destination" }
        if ($dirty) { throw "Refusing to overwrite local changes in $Destination" }
    }
    else {
        Invoke-Checked $Git @('clone','--filter=blob:none',$Url,$Destination)
    }

    Invoke-Checked $Git @('-C',$Destination,'fetch','--depth','1','origin',$Commit)
    Invoke-Checked $Git @('-C',$Destination,'checkout','--detach',$Commit)
    $actual = (& $Git -C $Destination rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $actual -ne $Commit) {
        throw "Pinned checkout mismatch for $Destination"
    }
    return $actual
}

if ($env:OS -ne 'Windows_NT') {
    throw 'This installer is intentionally Windows-only.'
}
if (-not [Environment]::Is64BitOperatingSystem) {
    throw '64-bit Windows is required.'
}

$null = New-Item -ItemType Directory -Force -Path $ToolsRoot
$ToolsRoot = (Resolve-Path -LiteralPath $ToolsRoot).Path
$BinRoot = Join-Path $ToolsRoot 'bin'
$ModelRoot = Join-Path $ToolsRoot 'models'
$null = New-Item -ItemType Directory -Force -Path $BinRoot,$ModelRoot

$git = Ensure-Command -Name 'git' -WingetId 'Git.Git'
$uv = Ensure-Command -Name 'uv' -WingetId 'astral-sh.uv'

$report = [ordered]@{
    schema = 'nexus.external-tools.v1'
    generated_utc = [DateTime]::UtcNow.ToString('o')
    tools_root = $ToolsRoot
    architecture = 'Kernel is the brain; ACE-Step and Forge are external tools.'
    ace_step = $null
    forge = $null
    deforum = $null
    health_check_launcher = $null
}

if (-not $SkipAceStep) {
    $ace = Join-Path $ToolsRoot 'ACE-Step-1.5'
    $aceSha = Install-PinnedRepo -Git $git -Url $AceRepo -Commit $AceCommit -Destination $ace
    if (-not (Test-Path -LiteralPath (Join-Path $ace 'LICENSE'))) {
        throw 'ACE-Step license file is missing.'
    }

    # One shared model directory avoids duplicated weights across future ACE-Step checkouts.
    $aceModels = Join-Path $ModelRoot 'ace-step'
    $null = New-Item -ItemType Directory -Force -Path $aceModels

    # RTX 2080 / 8 GB: keep the external ACE language model disabled by default.
    # The Nexus Kernel remains authoritative; ACE-Step is used as a bounded music tool.
    $envText = @"
ACESTEP_CONFIG_PATH=acestep-v15-turbo
ACESTEP_DEVICE=cuda
ACESTEP_INIT_LLM=false
ACESTEP_LM_BACKEND=pt
ACESTEP_NO_INIT=true
ACESTEP_CHECKPOINTS_DIR=$aceModels
ACESTEP_API_HOST=127.0.0.1
ACESTEP_API_PORT=$AcePort
CHECK_UPDATE=false
"@
    Set-Content -LiteralPath (Join-Path $ace '.env') -Value $envText -Encoding UTF8

    Invoke-Checked $uv @('sync','--frozen') $ace
    Invoke-Checked $uv @('run','--no-sync','python','-c','import acestep; import acestep.api_server; print("ACESTEP_IMPORT=PASS")') $ace

    $aceLauncher = @"
@echo off
setlocal
cd /d "$ace"
set "ACESTEP_CONFIG_PATH=acestep-v15-turbo"
set "ACESTEP_DEVICE=cuda"
set "ACESTEP_INIT_LLM=false"
set "ACESTEP_LM_BACKEND=pt"
set "ACESTEP_NO_INIT=true"
set "ACESTEP_CHECKPOINTS_DIR=$aceModels"
"$uv" run --no-sync acestep-api --host 127.0.0.1 --port $AcePort --no-init
endlocal
"@
    $aceLauncherPath = Join-Path $BinRoot 'Start-ACE-Step-Nexus.cmd'
    Set-Content -LiteralPath $aceLauncherPath -Value $aceLauncher -Encoding ASCII

    $report.ace_step = [ordered]@{
        status = 'INSTALLED_TESTED'
        path = $ace
        commit = $aceSha
        license = $AceLicense
        model_license = 'MIT for ACE-Step/Ace-Step1.5 main model; generated-output rights still require normal copyright review.'
        endpoint = "http://127.0.0.1:$AcePort"
        launcher = $aceLauncherPath
        models = $aceModels
        note = 'Models are downloaded by ACE-Step when first needed; no duplicate model checkout is created by Nexus.'
    }
}

if (-not $SkipForge) {
    $forge = Join-Path $ToolsRoot 'Forge'
    $forgeSha = Install-PinnedRepo -Git $git -Url $ForgeRepo -Commit $ForgeCommit -Destination $forge
    if (-not (Test-Path -LiteralPath (Join-Path $forge 'LICENSE.txt'))) {
        throw 'Forge license file is missing.'
    }

    # Forge upstream is built around Python 3.10. uv keeps this interpreter external to Nexus.
    Invoke-Checked $uv @('python','install','3.10')
    $forgePython = (& $uv python find 3.10).Trim()
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $forgePython)) {
        throw 'Python 3.10 for Forge could not be resolved.'
    }

    $forgeSettings = @"
@echo off
set "PYTHON=$forgePython"
set "VENV_DIR=$forge\venv"
set "COMMANDLINE_ARGS=--api --port $ForgePort --skip-version-check"
"@
    Set-Content -LiteralPath (Join-Path $forge 'webui.settings.bat') -Value $forgeSettings -Encoding ASCII

    # Upstream --exit performs dependency/bootstrap work and exits before serving.
    Invoke-Checked (Join-Path $env:SystemRoot 'System32\cmd.exe') @('/d','/c','webui.bat --exit') $forge

    $forgeVenvPython = Join-Path $forge 'venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $forgeVenvPython)) {
        throw 'Forge virtual environment was not created.'
    }
    Invoke-Checked $forgeVenvPython @('-c','import torch; print("FORGE_TORCH=" + torch.__version__); print("CUDA=" + str(torch.cuda.is_available()))')

    # Official Deforum-for-Forge extension, pinned independently from Forge.
    # Installation is allowed here because the caller already crossed the explicit
    # human authorization gate; the extension remains an external AGPL component.
    $extensions = Join-Path $forge 'extensions'
    $null = New-Item -ItemType Directory -Force -Path $extensions
    $deforum = Join-Path $extensions 'sd-forge-deforum'
    $deforumSha = Install-PinnedRepo -Git $git -Url $DeforumRepo -Commit $DeforumCommit -Destination $deforum
    if (-not (Test-Path -LiteralPath (Join-Path $deforum 'LICENSE'))) {
        throw 'Deforum license file is missing.'
    }
    Invoke-Checked $forgeVenvPython @('-m','pip','install','--disable-pip-version-check','-r',(Join-Path $deforum 'requirements.txt')) $forge
    Invoke-Checked $forgeVenvPython @('-m','compileall','-q',(Join-Path $deforum 'scripts')) $forge
    Invoke-Checked $forgeVenvPython @('-m','pip','check') $forge

    $report.deforum = [ordered]@{
        status = 'INSTALLED_DEPENDENCIES_TESTED'
        path = $deforum
        commit = $deforumSha
        license = $DeforumLicense
        host = 'Forge'
        functional_status = 'REQUIRES_REAL_RENDER_ACCEPTANCE'
        note = 'Official Deforum Forge extension is experimental upstream. Installation/requirements/syntax are checked here; a real animation is a later acceptance gate.'
    }

    $forgeLauncher = @"
@echo off
setlocal
cd /d "$forge"
call webui.bat
endlocal
"@
    $forgeLauncherPath = Join-Path $BinRoot 'Start-Forge-Nexus.cmd'
    Set-Content -LiteralPath $forgeLauncherPath -Value $forgeLauncher -Encoding ASCII

    $report.forge = [ordered]@{
        status = 'INSTALLED_TESTED'
        path = $forge
        commit = $forgeSha
        license = $ForgeLicense
        endpoint = "http://127.0.0.1:$ForgePort"
        launcher = $forgeLauncherPath
        model = 'NOT_INSTALLED'
        note = 'Forge is an external AGPL program. Nexus does not vendor it. No Stable Diffusion checkpoint is downloaded automatically because each model has its own license.'
    }
}

$healthScript = Join-Path $PSScriptRoot 'check-media-tools.ps1'
if (-not (Test-Path -LiteralPath $healthScript)) {
    throw 'Nexus media health checker is missing.'
}
$healthLauncherPath = Join-Path $BinRoot 'Check-Nexus-Media-Tools.cmd'
$healthLauncher = @"
@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$healthScript" -ToolsRoot "$ToolsRoot"
"@
Set-Content -LiteralPath $healthLauncherPath -Value $healthLauncher -Encoding ASCII
$report.health_check_launcher = $healthLauncherPath

$reportPath = Join-Path $ToolsRoot 'nexus-media-tools.json'
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8
Write-Host 'NEXUS MEDIA TOOLS = PASS'
Write-Host "Report: $reportPath"
if ($report.ace_step) { Write-Host "ACE-Step launcher: $($report.ace_step.launcher)" }
if ($report.forge) { Write-Host "Forge launcher: $($report.forge.launcher)" }
if ($report.deforum) { Write-Host "Deforum: $($report.deforum.status) @ $($report.deforum.commit)" }
Write-Host "Health checker: $healthLauncherPath"
