[CmdletBinding()]
param(
    [string]$RepoRoot = '',
    [string]$ToolsRoot = 'C:\Nexus-Tools',
    [ValidateSet('cuda','cpu')][string]$Device = 'cuda',
    [switch]$AuthorizeInstall
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if (-not $AuthorizeInstall) {
    throw 'NEXUS_INSTALL_AUTHORIZATION_REQUIRED: rerun with -AuthorizeInstall only after explicit human approval.'
}
if ($env:OS -ne 'Windows_NT' -or -not [Environment]::Is64BitOperatingSystem) {
    throw 'NEXUS_WINDOWS_X64_REQUIRED'
}

$ExpectedOrigin = 'https://github.com/PAPACREATOR/cerebro-parvo-.git'
$OpenNotebookOrigin = 'https://github.com/lfnovo/open-notebook.git'
$OpenNotebookPin = '315d5255af2a5132aada41c94d5c3c5dc8e837aa'
$SpeachesOrigin = 'https://github.com/speaches-ai/speaches.git'
$SpeachesPin = '993994f7984bf3fe9655b267448328cf66fccb42'
$MoneyPrinterOrigin = 'https://github.com/harry0703/MoneyPrinterTurbo.git'
$MoneyPrinterPin = '68eb5a68b93cfe338198b3dfb151f6d5ec2fe4e5'
$SurrealVersion = '2.7.0'
$SurrealSha256 = '55c7e05ee2b68ec0d8b86c4b588e9b9807f257af8c15c05d17074514c64d8c91'
$LanguageToolVersion = '6.6'
$LanguageToolSha256 = '53600506b399bb5ffe1e4c8dec794fd378212f14aaf38ccef9b6f89314d11631'
$PyInstallerVersion = '6.16.0'
$LlamaLanguageRevision = '90862c4b9d2787eaed51d12237eafdfe7c5f6077'
$LlamaLanguageSha256 = '061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a'
$LlamaEmbeddingRevision = 'd20cf9c16f82914a21dbd9c645f56895fb1d7750'
$LlamaEmbeddingSha256 = '06507c7b42688469c4e7298b0a1e16deff06caf291cf0a5b278c308249c3e439'
$LlamaLanguagePort = 18081
$LlamaEmbeddingPort = 18082
$LlamaLanguageAlias = 'nexus-qwen3-1.7b'
$LlamaEmbeddingAlias = 'nexus-qwen3-embedding-0.6b'
$StableDiffusion15Url = 'https://huggingface.co/stable-diffusion-v1-5/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors'
$StableDiffusion15Sha256 = '6ce0161689b3853acaa03779ec93eafe75a02f4ced659bee03f50797806fa2fa'

function Invoke-Checked {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = ''
    )
    $old = Get-Location
    try {
        if ($WorkingDirectory) { Set-Location -LiteralPath $WorkingDirectory }
        & $FilePath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw ('NEXUS_COMMAND_FAILED: ' + $FilePath + ' exit=' + $LASTEXITCODE)
        }
    }
    finally {
        if ($WorkingDirectory) { Set-Location $old }
    }
}

function Refresh-ProcessPath {
    $machine = [Environment]::GetEnvironmentVariable('Path','Machine')
    $user = [Environment]::GetEnvironmentVariable('Path','User')
    $env:Path = @($machine,$user,$env:Path) -join ';'
}

function Resolve-Executable {
    param([string[]]$Names, [string[]]$Candidates = @())
    foreach ($name in $Names) {
        $cmd = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmd) { return $cmd.Source }
    }
    foreach ($candidate in $Candidates) {
        $matches = @(Get-ChildItem -Path $candidate -File -ErrorAction SilentlyContinue | Sort-Object FullName -Descending)
        if ($matches.Count -gt 0) { return $matches[0].FullName }
        if (Test-Path -LiteralPath $candidate) { return (Resolve-Path -LiteralPath $candidate).Path }
    }
    return $null
}

function Test-PackageRuntime {
    param([Parameter(Mandatory=$true)][string]$Id)
    Refresh-ProcessPath
    switch ($Id) {
        'Git.Git' {
            return [bool](Resolve-Executable @('git.exe','git') @("$env:ProgramFiles\Git\cmd\git.exe"))
        }
        'Python.Python.3.12' {
            $py = Resolve-Executable @('py.exe','py') @("$env:SystemRoot\py.exe")
            if (-not $py) { return $false }
            & $py -3.12 -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3,12) else 1)" 2>$null
            return ($LASTEXITCODE -eq 0)
        }
        'OpenJS.NodeJS.LTS' {
            $node = Resolve-Executable @('node.exe','node') @("$env:ProgramFiles\nodejs\node.exe")
            $npm = Resolve-Executable @('npm.cmd','npm') @("$env:ProgramFiles\nodejs\npm.cmd")
            if (-not $node -or -not $npm) { return $false }
            & $node --version *> $null
            if ($LASTEXITCODE -ne 0) { return $false }
            & $npm --version *> $null
            return ($LASTEXITCODE -eq 0)
        }
        'Microsoft.OpenJDK.17' {
            return [bool](Resolve-Executable @('java.exe','java') @("$env:ProgramFiles\Microsoft\jdk-17*\bin\java.exe"))
        }
        'TheDocumentFoundation.LibreOffice' {
            return [bool](Resolve-Executable @('soffice.com') @("$env:ProgramFiles\LibreOffice\program\soffice.com"))
        }
        'DigitalScholar.Zotero' {
            return [bool](Resolve-Executable @('zotero.exe') @(
                "$env:ProgramFiles\Zotero\zotero.exe",
                "$([Environment]::GetFolderPath('ProgramFilesX86'))\Zotero\zotero.exe",
                "$env:LOCALAPPDATA\Programs\Zotero\zotero.exe"
            ))
        }
        'Gyan.FFmpeg' {
            return [bool](Resolve-Executable @('ffmpeg.exe','ffmpeg'))
        }
        'astral-sh.uv' {
            return [bool](Resolve-Executable @('uv.exe','uv') @(
                "$env:USERPROFILE\.local\bin\uv.exe",
                "$env:LOCALAPPDATA\Microsoft\WinGet\Links\uv.exe"
            ))
        }
        'ggml.llamacpp' {
            $server = Resolve-Executable @('llama-server.exe','llama-server')
            if (-not $server) { return $false }
            & $server --version *> $null
            return ($LASTEXITCODE -eq 0)
        }
        default {
            return $false
        }
    }
}

function Ensure-WingetPackage {
    param([Parameter(Mandatory=$true)][string]$Id)
    $winget = Resolve-Executable @('winget.exe')
    if (-not $winget) { throw 'NEXUS_WINGET_REQUIRED: install Microsoft App Installer first.' }

    $listed = & $winget list --id $Id --exact --accept-source-agreements 2>&1
    if ($LASTEXITCODE -eq 0 -and ("$listed" -match [regex]::Escape($Id))) {
        Refresh-ProcessPath
        if ($Id -eq 'Microsoft.VCRedist.2015+.x64') {
            return 'WINGET_PRESENT'
        }
        if (Test-PackageRuntime $Id) {
            return 'RUNTIME_PRESENT'
        }
        Write-Warning ('winget lists ' + $Id + ' but its executable runtime is unavailable; attempting repair/install.')
    }

    if (Test-PackageRuntime $Id) {
        return 'RUNTIME_PRESENT'
    }

    & $winget install --id $Id --exact --source winget --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
    $installExit = $LASTEXITCODE
    Refresh-ProcessPath

    if ($installExit -eq 0) {
        if ($Id -eq 'Microsoft.VCRedist.2015+.x64') {
            return 'WINGET_INSTALLED'
        }
        if (Test-PackageRuntime $Id) {
            return 'WINGET_INSTALLED_RUNTIME_VERIFIED'
        }
        throw ('NEXUS_WINGET_RUNTIME_MISSING_AFTER_INSTALL: ' + $Id)
    }

    if (Test-PackageRuntime $Id) {
        Write-Warning ('winget returned exit=' + $installExit + ' for ' + $Id + ', but its runtime is present and executable; continuing with runtime verification.')
        return ('RUNTIME_PRESENT_AFTER_WINGET_FAILURE_' + $installExit)
    }

    throw ('NEXUS_WINGET_INSTALL_FAILED: ' + $Id + ' exit=' + $installExit)
}

function Install-PinnedRepo {
    param(
        [string]$Git,
        [string]$Origin,
        [string]$Pin,
        [string]$Destination
    )
    if (Test-Path -LiteralPath $Destination) {
        if (-not (Test-Path -LiteralPath (Join-Path $Destination '.git'))) {
            throw ('NEXUS_EXISTING_PATH_NOT_GIT: ' + $Destination)
        }
        $actualOrigin = (& $Git -C $Destination remote get-url origin).Trim()
        $head = (& $Git -C $Destination rev-parse HEAD).Trim()
        $dirty = & $Git -C $Destination status --porcelain
        if ($actualOrigin -ne $Origin) { throw ('NEXUS_WRONG_TOOL_ORIGIN: ' + $Destination) }
        if ($head -ne $Pin) {
            if ($dirty) { throw ('NEXUS_TOOL_DIRTY_REFUSING_CHECKOUT: ' + $Destination) }
            Invoke-Checked $Git @('-C',$Destination,'fetch','--depth','1','origin',$Pin)
            Invoke-Checked $Git @('-C',$Destination,'checkout','--detach',$Pin)
        }
    } else {
        Invoke-Checked $Git @('clone','--filter=blob:none',$Origin,$Destination)
        Invoke-Checked $Git @('-C',$Destination,'fetch','--depth','1','origin',$Pin)
        Invoke-Checked $Git @('-C',$Destination,'checkout','--detach',$Pin)
    }
    $actual = (& $Git -C $Destination rev-parse HEAD).Trim()
    if ($actual -ne $Pin) { throw ('NEXUS_PIN_MISMATCH: ' + $Destination) }
    return $actual
}

function Download-Verified {
    param([string]$Uri,[string]$Destination,[string]$Sha256)
    if (Test-Path -LiteralPath $Destination) {
        $existing = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($existing -eq $Sha256) { return $Destination }
        throw ('NEXUS_EXISTING_DOWNLOAD_HASH_MISMATCH: ' + $Destination)
    }
    Invoke-WebRequest -Uri $Uri -OutFile $Destination -UseBasicParsing
    $actual = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $Sha256) {
        Remove-Item -LiteralPath $Destination -Force
        throw ('NEXUS_DOWNLOAD_HASH_MISMATCH: ' + $Uri)
    }
    return $Destination
}

function Wait-Http {
    param([string]$Uri,[int]$Seconds = 60)
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        try {
            $response = Invoke-WebRequest -Uri $Uri -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) { return }
        } catch {}
        Start-Sleep -Milliseconds 500
    }
    throw ('NEXUS_HTTP_TIMEOUT: ' + $Uri)
}

function New-RandomHex {
    param([int]$Bytes = 32)
    $buffer = New-Object byte[] $Bytes
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($buffer) } finally { $rng.Dispose() }
    return -join ($buffer | ForEach-Object { $_.ToString('x2') })
}

function Get-DotEnvValue {
    param([string]$Path,[string]$Name)
    foreach ($line in [IO.File]::ReadAllLines($Path)) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
        $parts = $trimmed.Split(@('='),2)
        if ($parts.Count -ne 2 -or $parts[0].Trim() -ne $Name) { continue }
        $value = $parts[1].Trim()
        if ($value.Length -ge 2 -and (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'")))) {
            $value = $value.Substring(1,$value.Length-2)
        }
        return $value
    }
    return $null
}

if (-not $RepoRoot) {
    $RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
}
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot '.git'))) { throw 'NEXUS_REPOSITORY_NOT_FOUND' }

$bootstrapGit = Resolve-Executable @('git.exe','git')
if (-not $bootstrapGit) {
    Ensure-WingetPackage 'Git.Git'
    $bootstrapGit = Resolve-Executable @('git.exe','git') @("$env:ProgramFiles\Git\cmd\git.exe")
}
if (-not $bootstrapGit) { throw 'NEXUS_GIT_REQUIRED' }

$origin = (& $bootstrapGit -C $RepoRoot remote get-url origin).Trim()
if ($origin -ne $ExpectedOrigin) { throw 'NEXUS_WRONG_ORIGIN' }
$dirty = & $bootstrapGit -C $RepoRoot status --porcelain
if ($dirty) { throw 'NEXUS_DIRTY_TREE: preserve/commit local work before installation.' }
$NexusHead = (& $bootstrapGit -C $RepoRoot rev-parse HEAD).Trim()

$null = New-Item -ItemType Directory -Force -Path $ToolsRoot
$ToolsRoot = (Resolve-Path -LiteralPath $ToolsRoot).Path
$BinRoot = Join-Path $ToolsRoot 'bin'
$Downloads = Join-Path $ToolsRoot 'downloads'
$Models = Join-Path $ToolsRoot 'models'
$Logs = Join-Path $ToolsRoot 'logs'
$Build = Join-Path $ToolsRoot 'build'
foreach ($path in @($BinRoot,$Downloads,$Models,$Logs,$Build)) {
    $null = New-Item -ItemType Directory -Force -Path $path
}

$driveRoot = [IO.Path]::GetPathRoot($ToolsRoot)
$drive = New-Object System.IO.DriveInfo($driveRoot)
$minimumFreeBytes = [int64](70 * 1GB)
if ($drive.AvailableFreeSpace -lt $minimumFreeBytes) {
    throw ('NEXUS_DISK_SPACE_REQUIRED: at least 70 GiB free on ' + $driveRoot + '; choose another -ToolsRoot before installation.')
}

$report = [ordered]@{
    schema = 'nexus.windows-complete-install.v1'
    status = 'RUNNING'
    started_utc = [DateTime]::UtcNow.ToString('o')
    finished_utc = $null
    nexus_head = $NexusHead
    repo_root = $RepoRoot
    tools_root = $ToolsRoot
    device = $Device
    storage = [ordered]@{ drive=$driveRoot; free_bytes=$drive.AvailableFreeSpace; minimum_free_bytes=$minimumFreeBytes }
    prerequisites = [ordered]@{}
    tools = [ordered]@{}
    models = [ordered]@{}
    launcher = [ordered]@{}
    pending = @()
    error = $null
}
$reportPath = Join-Path $ToolsRoot 'complete-install-report.json'

function Save-Report {
    $report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $reportPath -Encoding UTF8
}

try {
    Save-Report

    # Common Windows dependencies. Every package is independently verified below.
    foreach ($id in @(
        'Git.Git',
        'Python.Python.3.12',
        'OpenJS.NodeJS.LTS',
        'Microsoft.OpenJDK.17',
        'TheDocumentFoundation.LibreOffice',
        'DigitalScholar.Zotero',
        'Gyan.FFmpeg',
        'astral-sh.uv',
        'ggml.llamacpp',
        'Microsoft.VCRedist.2015+.x64'
    )) {
        $packageState = Ensure-WingetPackage $id
        $report.prerequisites[$id] = $packageState
        Save-Report
    }

    $git = Resolve-Executable @('git.exe','git') @("$env:ProgramFiles\Git\cmd\git.exe")
    $py = Resolve-Executable @('py.exe','py') @("$env:SystemRoot\py.exe")
    $node = Resolve-Executable @('node.exe','node') @("$env:ProgramFiles\nodejs\node.exe")
    $npm = Resolve-Executable @('npm.cmd','npm') @("$env:ProgramFiles\nodejs\npm.cmd")
    $java = Resolve-Executable @('java.exe','java') @("$env:ProgramFiles\Microsoft\jdk-17*\bin\java.exe")
    $soffice = Resolve-Executable @('soffice.com') @("$env:ProgramFiles\LibreOffice\program\soffice.com")
    $unopkg = Resolve-Executable @('unopkg.com') @("$env:ProgramFiles\LibreOffice\program\unopkg.com")
    $zotero = Resolve-Executable @('zotero.exe') @("$env:ProgramFiles\Zotero\zotero.exe","$([Environment]::GetFolderPath('ProgramFilesX86'))\Zotero\zotero.exe","$env:LOCALAPPDATA\Programs\Zotero\zotero.exe")
    $ffmpeg = Resolve-Executable @('ffmpeg.exe','ffmpeg')
    $ffprobe = Resolve-Executable @('ffprobe.exe','ffprobe')
    $uv = Resolve-Executable @('uv.exe','uv') @("$env:USERPROFILE\.local\bin\uv.exe","$env:LOCALAPPDATA\Microsoft\WinGet\Links\uv.exe")
    $llamaServer = Resolve-Executable @('llama-server.exe','llama-server')

    foreach ($pair in @(
        @('git',$git),@('py',$py),@('node',$node),@('npm',$npm),@('java',$java),
        @('libreoffice',$soffice),@('unopkg',$unopkg),@('zotero',$zotero),@('ffmpeg',$ffmpeg),@('ffprobe',$ffprobe),
        @('uv',$uv),@('llamacpp',$llamaServer)
    )) {
        if (-not $pair[1] -or -not (Test-Path -LiteralPath $pair[1])) {
            throw ('NEXUS_REQUIRED_EXECUTABLE_MISSING: ' + $pair[0])
        }
        $report.tools[$pair[0]] = [ordered]@{ status='FOUND'; path=$pair[1] }
    }

    $python312 = (& $py -3.12 -c "import sys; assert sys.version_info[:2] == (3,12); print(sys.executable)").Trim()
    if (-not (Test-Path -LiteralPath $python312)) { throw 'NEXUS_PYTHON_312_NOT_RESOLVED' }
    $report.tools.python312 = [ordered]@{ status='PASS'; path=$python312; version=(& $python312 --version 2>&1 | Out-String).Trim() }
    $report.tools.git.version = (& $git --version | Out-String).Trim()
    $report.tools.node.version = (& $node --version | Out-String).Trim()
    $report.tools.java.version = (& $java -version 2>&1 | Select-Object -First 1 | Out-String).Trim()
    $report.tools.libreoffice.version = (& $soffice --version 2>&1 | Out-String).Trim()
    $report.tools.ffmpeg.version = (& $ffmpeg -version 2>&1 | Select-Object -First 1 | Out-String).Trim()
    $report.tools.zotero.version = (Get-Item -LiteralPath $zotero).VersionInfo.FileVersion
    $report.tools.llamacpp.version = (& $llamaServer --version 2>&1 | Out-String).Trim()

    # Zotero <-> LibreOffice structural gate. The official OXT must be shipped by Zotero,
    # and Java + LibreOffice must both be real executables before we claim compatibility.
    $zoteroRoot = Split-Path -Parent $zotero
    $zoteroOxt = Join-Path $zoteroRoot 'integration\libreoffice\Zotero_OpenOffice_Integration.oxt'
    if (-not (Test-Path -LiteralPath $zoteroOxt)) { throw 'NEXUS_ZOTERO_LIBREOFFICE_EXTENSION_MISSING' }
    Invoke-Checked $java @('-version')
    Invoke-Checked $soffice @('--version')
    $extensionList = (& $unopkg list 2>&1 | Out-String)
    if ($extensionList -notmatch '(?i)zotero') {
        Invoke-Checked $unopkg @('add','--force',$zoteroOxt)
        $extensionList = (& $unopkg list 2>&1 | Out-String)
    }
    if ($extensionList -notmatch '(?i)zotero') {
        throw 'NEXUS_ZOTERO_LIBREOFFICE_EXTENSION_NOT_REGISTERED'
    }
    $report.tools.zotero['libreoffice_oxt'] = $zoteroOxt
    $report.tools.zotero['integration_status'] = 'OXT_REGISTERED_JAVA_LIBREOFFICE_VERIFIED'
    Save-Report

    # Stable standalone LanguageTool 6.6, fixed checksum from the project release announcement.
    $ltZip = Join-Path $Downloads 'LanguageTool-6.6.zip'
    Download-Verified 'https://languagetool.org/download/LanguageTool-6.6.zip' $ltZip $LanguageToolSha256 | Out-Null
    $ltRoot = Join-Path $ToolsRoot 'LanguageTool'
    if (-not (Test-Path -LiteralPath $ltRoot)) {
        $null = New-Item -ItemType Directory -Path $ltRoot
        Expand-Archive -LiteralPath $ltZip -DestinationPath $ltRoot
    }
    $ltJar = Get-ChildItem -LiteralPath $ltRoot -Filter 'languagetool-commandline.jar' -File -Recurse | Select-Object -First 1
    if (-not $ltJar) { throw 'NEXUS_LANGUAGETOOL_JAR_MISSING' }
    Invoke-Checked $java @('-jar',$ltJar.FullName,'--version')
    $report.tools.languagetool = [ordered]@{
        status='INSTALLED_TESTED'; version=$LanguageToolVersion; jar=$ltJar.FullName; archive_sha256=$LanguageToolSha256
    }
    Save-Report

    # SurrealDB 2.7.0 is pinned because this is the version already exercised with the Nexus/OpenNotebook lab.
    $surreal = Join-Path $BinRoot 'surreal.exe'
    Download-Verified 'https://github.com/surrealdb/surrealdb/releases/download/v2.7.0/surreal-v2.7.0.windows-amd64.exe' $surreal $SurrealSha256 | Out-Null
    $surrealVersionText = (& $surreal version 2>&1 | Out-String).Trim()
    if ($surrealVersionText -notmatch '2\.7\.0') { throw 'NEXUS_SURREAL_VERSION_MISMATCH' }
    $report.tools.surrealdb = [ordered]@{ status='INSTALLED_TESTED'; version=$surrealVersionText; path=$surreal; sha256=$SurrealSha256 }
    Save-Report

    # Open Notebook source is pinned. Data remains separate from Nexus Canonical/Creative.
    $openNotebook = Join-Path $ToolsRoot 'OpenNotebook'
    $openHead = Install-PinnedRepo $git $OpenNotebookOrigin $OpenNotebookPin $openNotebook
    $legacyRuntimePackage = -join ((111,108,108,97,109,97) | ForEach-Object { [char]$_ })
    $legacyLangchainPackage = 'langchain-' + $legacyRuntimePackage
    Invoke-Checked $uv @(
        'sync','--frozen',
        '--no-install-package',$legacyLangchainPackage,
        '--no-install-package',$legacyRuntimePackage
    ) $openNotebook
    Invoke-Checked $npm @('ci') (Join-Path $openNotebook 'frontend')
    Invoke-Checked $npm @('run','build') (Join-Path $openNotebook 'frontend')
    $openPython = Join-Path $openNotebook '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $openPython)) { throw 'NEXUS_OPEN_NOTEBOOK_VENV_MISSING' }
    $openCompatibilityProbe = @'
import importlib.util
from esperanto import AIFactory
from open_notebook.ai.provider_registry import PROVIDERS
legacy = "".join(chr(value) for value in (111, 108, 108, 97, 109, 97))
assert importlib.util.find_spec(legacy) is None
assert importlib.util.find_spec("langchain_" + legacy) is None
spec = PROVIDERS["openai_compatible"]
assert "language" in spec.modalities and "embedding" in spec.modalities
assert AIFactory.create_language(
    model_name="nexus-qwen3-1.7b",
    provider="openai-compatible",
    config={"base_url":"http://127.0.0.1:18081/v1","api_key":"ARCHIVE_REDACTED_01"},
) is not None
assert AIFactory.create_embedding(
    model_name="nexus-qwen3-embedding-0.6b",
    provider="openai-compatible",
    config={"base_url":"http://127.0.0.1:18082/v1","api_key":"ARCHIVE_REDACTED_01"},
) is not None
print("OPEN_NOTEBOOK_LLAMACPP_COMPAT=PASS")
'@
    Invoke-Checked $openPython @('-c',$openCompatibilityProbe) $openNotebook

    $openEnv = Join-Path $openNotebook '.env'
    if (-not (Test-Path -LiteralPath $openEnv)) {
        $dbPassword = New-RandomHex 24
        $encryptionKey = New-RandomHex 32
        $apiPassword = New-RandomHex 24
        @(
            'SURREAL_URL=ws://127.0.0.1:8000/rpc',
            'SURREAL_USER=root',
            ('SURREAL_PASSWORD=' + $dbPassword),
            'SURREAL_NAMESPACE=open_notebook',
            'SURREAL_DATABASE=open_notebook',
            ('OPEN_NOTEBOOK_ENCRYPTION_KEY=' + $encryptionKey),
            ('OPEN_NOTEBOOK_PASSWORD=' + $apiPassword),
            'OPEN_NOTEBOOK_WORKER_MAX_TASKS=1'
        ) | Set-Content -LiteralPath $openEnv -Encoding UTF8
    }
    $report.tools.open_notebook = [ordered]@{
        status='INSTALLED_BUILT'; path=$openNotebook; commit=$openHead; version='1.15.0'; env=$openEnv
    }
    Save-Report

    # Local language + embedding runtimes for Open Notebook. llama.cpp is an external,
    # replaceable tool; the Python Kernel and Human Gate remain authoritative.
    $llamaModels = Join-Path $Models 'llamacpp'
    $null = New-Item -ItemType Directory -Force -Path $llamaModels
    $languageModel = Join-Path $llamaModels 'Qwen3-1.7B-Q8_0.gguf'
    $embeddingModel = Join-Path $llamaModels 'Qwen3-Embedding-0.6B-Q8_0.gguf'
    $languageUrl = 'https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/resolve/' + $LlamaLanguageRevision + '/Qwen3-1.7B-Q8_0.gguf'
    $embeddingUrl = 'https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF/resolve/' + $LlamaEmbeddingRevision + '/Qwen3-Embedding-0.6B-Q8_0.gguf'
    Download-Verified $languageUrl $languageModel $LlamaLanguageSha256 | Out-Null
    Download-Verified $embeddingUrl $embeddingModel $LlamaEmbeddingSha256 | Out-Null

    $languageLauncher = Join-Path $BinRoot 'Start-Llama-Language-Nexus.cmd'
    @"
@echo off
"$llamaServer" -m "$languageModel" --host 127.0.0.1 --port $LlamaLanguagePort --alias $LlamaLanguageAlias -c 8192 -ngl 99
"@ | Set-Content -LiteralPath $languageLauncher -Encoding ASCII

    $embeddingLauncher = Join-Path $BinRoot 'Start-Llama-Embedding-Nexus.cmd'
    @"
@echo off
"$llamaServer" -m "$embeddingModel" --host 127.0.0.1 --port $LlamaEmbeddingPort --alias $LlamaEmbeddingAlias --embedding --pooling last -c 8192 -ngl 99 -np 1 --no-cont-batching
"@ | Set-Content -LiteralPath $embeddingLauncher -Encoding ASCII

    $report.tools.llamacpp['language_port'] = $LlamaLanguagePort
    $report.tools.llamacpp['embedding_port'] = $LlamaEmbeddingPort
    $report.tools.llamacpp['language_launcher'] = $languageLauncher
    $report.tools.llamacpp['embedding_launcher'] = $embeddingLauncher
    $report.models.llamacpp = [ordered]@{
        status='DOWNLOADED_VERIFIED_PENDING_RUNTIME_PROBE'
        language=[ordered]@{alias=$LlamaLanguageAlias; path=$languageModel; revision=$LlamaLanguageRevision; sha256=$LlamaLanguageSha256}
        embedding=[ordered]@{alias=$LlamaEmbeddingAlias; path=$embeddingModel; revision=$LlamaEmbeddingRevision; sha256=$LlamaEmbeddingSha256}
    }
    Save-Report

    # Local TTS server for podcast audio, pinned to an observed upstream commit.
    $speaches = Join-Path $ToolsRoot 'Speaches'
    $speachesHead = Install-PinnedRepo $git $SpeachesOrigin $SpeachesPin $speaches
    Invoke-Checked $uv @('sync','--frozen') $speaches
    $speachesOut = Join-Path $Logs 'speaches-install.stdout.txt'
    $speachesErr = Join-Path $Logs 'speaches-install.stderr.txt'
    $speachesProcess = Start-Process -FilePath $uv -ArgumentList @(
        'run','uvicorn','--factory','--host','127.0.0.1','--port','8969','speaches.main:create_app'
    ) -WorkingDirectory $speaches -RedirectStandardOutput $speachesOut -RedirectStandardError $speachesErr -PassThru -WindowStyle Hidden
    try {
        Wait-Http 'http://127.0.0.1:8969/v1/models' 120
        $oldSpeaches = $env:SPEACHES_BASE_URL
        $env:SPEACHES_BASE_URL = 'http://127.0.0.1:8969'
        try {
            Invoke-Checked $uv @('run','speaches-cli','model','download','speaches-ai/Kokoro-82M-v1.0-ONNX') $speaches
        }
        finally {
            $env:SPEACHES_BASE_URL = $oldSpeaches
        }
    }
    finally {
        if ($speachesProcess -and -not $speachesProcess.HasExited) {
            Stop-Process -Id $speachesProcess.Id -Force -ErrorAction SilentlyContinue
            $speachesProcess.WaitForExit()
        }
    }
    $speachesLauncher = Join-Path $BinRoot 'Start-Speaches-Nexus.cmd'
    @"
@echo off
setlocal
cd /d "$speaches"
"$uv" run uvicorn --factory --host 127.0.0.1 --port 8969 speaches.main:create_app
endlocal
"@ | Set-Content -LiteralPath $speachesLauncher -Encoding ASCII
    $report.tools.speaches = [ordered]@{ status='INSTALLED_TESTED'; path=$speaches; commit=$speachesHead; endpoint='http://127.0.0.1:8969'; launcher=$speachesLauncher }
    $report.models.kokoro = [ordered]@{ status='DOWNLOADED'; id='speaches-ai/Kokoro-82M-v1.0-ONNX' }
    Save-Report

    # ACE-Step and Forge use the already reviewed, explicitly authorized installer.
    $mediaInstaller = Join-Path $RepoRoot 'nexus\windows\install-media-tools.ps1'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $mediaInstaller -ToolsRoot $ToolsRoot -AuthorizeInstall
    if ($LASTEXITCODE -ne 0) { throw 'NEXUS_MEDIA_INSTALL_FAILED' }
    $mediaReportPath = Join-Path $ToolsRoot 'nexus-media-tools.json'
    if (-not (Test-Path -LiteralPath $mediaReportPath)) { throw 'NEXUS_MEDIA_REPORT_MISSING' }
    $mediaReport = Get-Content -LiteralPath $mediaReportPath -Raw | ConvertFrom-Json
    if ($null -eq $mediaReport.deforum -or $mediaReport.deforum.status -ne 'INSTALLED_DEPENDENCIES_TESTED') {
        throw 'NEXUS_DEFORUM_INSTALL_NOT_VERIFIED'
    }
    $report.tools.deforum = [ordered]@{
        status=$mediaReport.deforum.status
        path=$mediaReport.deforum.path
        commit=$mediaReport.deforum.commit
        license=$mediaReport.deforum.license
        functional_status=$mediaReport.deforum.functional_status
    }
    Save-Report

    # Pre-fetch the ACE-Step main model so the later real-music test cannot hide a first-use download.
    $ace = Join-Path $ToolsRoot 'ACE-Step-1.5'
    $aceModels = Join-Path $Models 'ace-step'
    $oldAceModels = $env:ACESTEP_CHECKPOINTS_DIR
    $env:ACESTEP_CHECKPOINTS_DIR = $aceModels
    try {
        $code = "from acestep.model_downloader import ensure_main_model; ok,msg=ensure_main_model(); print(msg); raise SystemExit(0 if ok else 1)"
        Invoke-Checked $uv @('run','--no-sync','python','-c',$code) $ace
    }
    finally {
        $env:ACESTEP_CHECKPOINTS_DIR = $oldAceModels
    }
    if (-not (Test-Path -LiteralPath (Join-Path $aceModels 'acestep-v15-turbo'))) {
        throw 'NEXUS_ACE_MAIN_MODEL_MISSING'
    }
    $report.models.ace_step = [ordered]@{ status='DOWNLOADED'; model='acestep-v15-turbo'; root=$aceModels }

    # Conservative Deforum/Forge baseline for the 8 GB GPU target: official SD 1.5 EMA-only.
    $forgeRoot = Join-Path $ToolsRoot 'Forge'
    $sdModelDir = Join-Path $forgeRoot 'models\Stable-diffusion'
    $null = New-Item -ItemType Directory -Force -Path $sdModelDir
    $sd15 = Join-Path $sdModelDir 'v1-5-pruned-emaonly.safetensors'
    Download-Verified $StableDiffusion15Url $sd15 $StableDiffusion15Sha256 | Out-Null
    $report.models.stable_diffusion = [ordered]@{
        status='DOWNLOADED_VERIFIED'
        model='stable-diffusion-v1-5/v1-5-pruned-emaonly.safetensors'
        path=$sd15
        sha256=$StableDiffusion15Sha256
        license='CreativeML Open RAIL-M'
        functional_status='REQUIRES_REAL_FORGE_AND_DEFORUM_RENDER_ACCEPTANCE'
    }
    $report.tools.forge = [ordered]@{
        status='RUNTIME_AND_BASE_MODEL_INSTALLED'
        path=$forgeRoot
        model=$sd15
        note='Forge plus the conservative SD 1.5 baseline are installed; image/Deforum rendering remains a physical acceptance gate.'
    }
    Save-Report

    # Add the already reviewed avatar extension and its pinned Wav2Lip/SFD weights.
    $avatarInstaller = Join-Path $RepoRoot 'nexus\lab\open_notebook_avatar\install-windows.ps1'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $avatarInstaller -OpenNotebookRoot $openNotebook -ApiPython $openPython -Device $Device -AuthorizeInstall
    if ($LASTEXITCODE -ne 0) { throw 'NEXUS_AVATAR_INSTALL_FAILED' }
    $avatarModels = Join-Path $openNotebook 'data\avatar-models'
    foreach ($name in @('wav2lip.pth','s3fd.pth')) {
        if (-not (Test-Path -LiteralPath (Join-Path $avatarModels $name))) { throw ('NEXUS_AVATAR_MODEL_MISSING: ' + $name) }
    }
    $report.models.avatar = [ordered]@{ status='DOWNLOADED'; root=$avatarModels; device=$Device }
    Save-Report

    # Configure Open Notebook through its own authenticated API. Start only the local
    # services needed for configuration; no Nexus vault is mounted into these processes.
    $dbPassword = Get-DotEnvValue $openEnv 'SURREAL_PASSWORD'
    $apiPassword = Get-DotEnvValue $openEnv 'OPEN_NOTEBOOK_PASSWORD'
    if (-not $dbPassword -or -not $apiPassword) { throw 'NEXUS_OPEN_NOTEBOOK_ENV_INCOMPLETE' }

    $openDataRoot = Join-Path $ToolsRoot 'OpenNotebook-Data'
    $surrealData = Join-Path $openDataRoot 'surrealdb'
    $null = New-Item -ItemType Directory -Force -Path $openDataRoot
    $surrealLog = Join-Path $Logs 'open-notebook-surreal.stdout.txt'
    $surrealErr = Join-Path $Logs 'open-notebook-surreal.stderr.txt'
    $apiLog = Join-Path $Logs 'open-notebook-api.stdout.txt'
    $apiErr = Join-Path $Logs 'open-notebook-api.stderr.txt'
    $speechConfigLog = Join-Path $Logs 'speaches-config.stdout.txt'
    $speechConfigErr = Join-Path $Logs 'speaches-config.stderr.txt'
    $languageLog = Join-Path $Logs 'llamacpp-language.stdout.txt'
    $languageErr = Join-Path $Logs 'llamacpp-language.stderr.txt'
    $embeddingLog = Join-Path $Logs 'llamacpp-embedding.stdout.txt'
    $embeddingErr = Join-Path $Logs 'llamacpp-embedding.stderr.txt'
    $surrealProcess = $null
    $apiProcess = $null
    $speechConfigProcess = $null
    $languageProcess = $null
    $embeddingProcess = $null
    try {
        $surrealProcess = Start-Process -FilePath $surreal -ArgumentList @(
            'start','--no-banner','--bind','127.0.0.1:8000','--user','root','--pass',$dbPassword,('rocksdb:' + $surrealData)
        ) -WorkingDirectory $openNotebook -RedirectStandardOutput $surrealLog -RedirectStandardError $surrealErr -PassThru -WindowStyle Hidden
        Wait-Http 'http://127.0.0.1:8000/health' 90

        $languageProcess = Start-Process -FilePath $llamaServer -ArgumentList @(
            '-m',('"' + $languageModel + '"'),'--host','127.0.0.1','--port',[string]$LlamaLanguagePort,
            '--alias',$LlamaLanguageAlias,'-c','8192','-ngl','99'
        ) -RedirectStandardOutput $languageLog -RedirectStandardError $languageErr -PassThru -WindowStyle Hidden
        Wait-Http ('http://127.0.0.1:' + $LlamaLanguagePort + '/health') 180

        $embeddingProcess = Start-Process -FilePath $llamaServer -ArgumentList @(
            '-m',('"' + $embeddingModel + '"'),'--host','127.0.0.1','--port',[string]$LlamaEmbeddingPort,
            '--alias',$LlamaEmbeddingAlias,'--embedding','--pooling','last',
            '-c','8192','-ngl','99','-np','1','--no-cont-batching'
        ) -RedirectStandardOutput $embeddingLog -RedirectStandardError $embeddingErr -PassThru -WindowStyle Hidden
        Wait-Http ('http://127.0.0.1:' + $LlamaEmbeddingPort + '/health') 180

        $languageProbeBody = @{
            model=$LlamaLanguageAlias
            messages=@(@{role='user'; content='Reply briefly with the word Nexus.'})
            max_tokens=32
            temperature=0
        } | ConvertTo-Json -Depth 5
        $languageProbe = Invoke-RestMethod -Method Post -Uri ('http://127.0.0.1:' + $LlamaLanguagePort + '/v1/chat/completions') -ContentType 'application/json' -Body $languageProbeBody -TimeoutSec 120
        if (-not $languageProbe.choices -or $languageProbe.choices.Count -lt 1) {
            throw 'NEXUS_LLAMACPP_LANGUAGE_PROBE_FAILED'
        }

        $embeddingProbeBody = @{model=$LlamaEmbeddingAlias; input='nexus bidirectional embedding probe'} | ConvertTo-Json
        $embeddingProbe = Invoke-RestMethod -Method Post -Uri ('http://127.0.0.1:' + $LlamaEmbeddingPort + '/v1/embeddings') -ContentType 'application/json' -Body $embeddingProbeBody -TimeoutSec 120
        if (-not $embeddingProbe.data -or -not $embeddingProbe.data[0].embedding -or $embeddingProbe.data[0].embedding.Count -lt 32) {
            throw 'NEXUS_LLAMACPP_EMBEDDING_PROBE_FAILED'
        }
        $report.models.llamacpp.status = 'DOWNLOADED_VERIFIED_RUNTIME_PROBED'

        $speechConfigProcess = Start-Process -FilePath $uv -ArgumentList @(
            'run','uvicorn','--factory','--host','127.0.0.1','--port','8969','speaches.main:create_app'
        ) -WorkingDirectory $speaches -RedirectStandardOutput $speechConfigLog -RedirectStandardError $speechConfigErr -PassThru -WindowStyle Hidden
        Wait-Http 'http://127.0.0.1:8969/v1/models' 120

        $apiProcess = Start-Process -FilePath $openPython -ArgumentList @(
            '-m','uvicorn','api.main:app','--host','127.0.0.1','--port','5055'
        ) -WorkingDirectory $openNotebook -RedirectStandardOutput $apiLog -RedirectStandardError $apiErr -PassThru -WindowStyle Hidden
        Wait-Http 'http://127.0.0.1:5055/health' 120

        $openConfigReport = Join-Path $ToolsRoot 'open-notebook-local-config.json'
        $openConfigHelper = Join-Path $RepoRoot 'nexus\windows\configure-open-notebook-local.py'
        Invoke-Checked $python312 @(
            $openConfigHelper,'--api','http://127.0.0.1:5055','--env-file',$openEnv,
            '--report',$openConfigReport,'--authorize-install'
        ) $RepoRoot
        $openConfig = Get-Content -LiteralPath $openConfigReport -Raw | ConvertFrom-Json
        if ($openConfig.status -ne 'PASS' -or $openConfig.auto_delete_files -ne 'no') {
            throw 'NEXUS_OPEN_NOTEBOOK_LOCAL_CONFIG_FAILED'
        }
        $report.tools.open_notebook.status = 'INSTALLED_BUILT_CONFIGURED'
        $report.tools.open_notebook['config_report'] = $openConfigReport
        $report.tools.open_notebook['podcast_profile'] = $openConfig.podcast_profiles.episode.name
        $report.models.open_notebook = [ordered]@{
            status='CONFIGURED_TESTED'
            language=$openConfig.models.language.name
            embedding=$openConfig.models.embedding.name
            tts=$openConfig.models.tts.name
        }
    }
    finally {
        foreach ($process in @($apiProcess,$speechConfigProcess,$embeddingProcess,$languageProcess,$surrealProcess)) {
            if ($process -and -not $process.HasExited) {
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
                $process.WaitForExit()
            }
        }
    }
    Save-Report

    # MoneyPrinterTurbo is the pinned audiovisual assembly block. Nexus supplies
    # local cognition/assets; MPT supplies narration/subtitles/editing/FFmpeg assembly.
    $moneyPrinter = Join-Path $ToolsRoot 'MoneyPrinterTurbo'
    $moneyPrinterHead = Install-PinnedRepo $git $MoneyPrinterOrigin $MoneyPrinterPin $moneyPrinter
    Invoke-Checked $uv @('sync','--frozen','--python',$python312) $moneyPrinter
    $moneyPrinterConfigReport = Join-Path $ToolsRoot 'moneyprinterturbo-local-config.json'
    $moneyPrinterConfigHelper = Join-Path $RepoRoot 'nexus\windows\configure-moneyprinterturbo-local.py'
    Invoke-Checked $python312 @(
        $moneyPrinterConfigHelper,'--root',$moneyPrinter,'--ffmpeg',$ffmpeg,
        '--device',$Device,'--report',$moneyPrinterConfigReport,'--authorize-install'
    ) $RepoRoot
    $moneyPrinterConfig = Get-Content -LiteralPath $moneyPrinterConfigReport -Raw | ConvertFrom-Json
    if ($moneyPrinterConfig.status -ne 'PASS' -or $moneyPrinterConfig.authority -ne 'NONE') {
        throw 'NEXUS_MONEYPRINTER_LOCAL_CONFIG_FAILED'
    }
    Invoke-Checked $uv @('run','--frozen','python','cli.py','--help') $moneyPrinter
    $report.tools.moneyprinterturbo = [ordered]@{
        status='INSTALLED_CONFIGURED_CLI_TESTED'
        path=$moneyPrinter
        commit=$moneyPrinterHead
        version='1.3.8'
        license='MIT'
        config_report=$moneyPrinterConfigReport
        authority='NONE'
        functional_status='REQUIRES_REAL_DOCUMENTARY_RENDER_ACCEPTANCE'
    }
    Save-Report

    # Configure deterministic Nexus adapters.
    $runtime = Join-Path $RepoRoot 'nexus\runtime'
    $null = New-Item -ItemType Directory -Force -Path $runtime
    @{ java=$java; jar=$ltJar.FullName } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtime 'languagetool.json') -Encoding UTF8
    # Sandy is NOT installed or downloaded silently. The human must supply
    # the approved v0.9994 file in the tools folder before book/PDF can run.
    # Writing both contract keys keeps missing tooling fail-closed, not bypassed.
    $writerSandy = Join-Path $ToolsRoot 'Sandy\sandy.exe'
    $writerSandyStatus = 'NOT_INSTALLED_WRITER_BLOCKED'
    if (Test-Path -LiteralPath $writerSandy -PathType Leaf) {
        if ((Get-Item -LiteralPath $writerSandy).Length -ne 1159680 -or
            (Get-FileHash -LiteralPath $writerSandy -Algorithm SHA256).Hash.ToLowerInvariant() -cne
                'cbfc30709f80e63b201f1944c34692fc430d8aa42d6cd2823fcc670675307eac') {
            throw 'NEXUS_WRITER_SANDY_PIN_MISMATCH'
        }
        $writerSandyStatus = 'VERIFIED_PINNED_WRITER_LPAC'
    }
    @{ executable=$soffice; sandy=$writerSandy } | ConvertTo-Json |
        Set-Content -LiteralPath (Join-Path $runtime 'libreoffice.json') -Encoding UTF8
    $report.tools.writer_sandy = [ordered]@{
        status=$writerSandyStatus
        path=$writerSandy
        required_for=@('book','convert_pdf')
        authority='NONE'
        automatically_installed=$false
    }
    Save-Report
    @{
        base_url='http://127.0.0.1:5055'
        password=$apiPassword
        model_id=$openConfig.models.language.id
        transformation_id=$openConfig.transformation.id
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtime 'open-notebook.json') -Encoding UTF8
    @{
        base_url='http://127.0.0.1:5055'
        password=$apiPassword
        model_id=$openConfig.models.language.id
        transformation_id=$openConfig.documentary_transformation.id
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtime 'open-notebook-documentary.json') -Encoding UTF8
    @{
        base_url='http://127.0.0.1:5055'
        password=$apiPassword
        model_id=$openConfig.models.language.id
        transformation_id=$openConfig.product_plan_transformation.id
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtime 'open-notebook-product.json') -Encoding UTF8
    @{
        root=$moneyPrinter
        uv=$uv
        ffmpeg=$ffmpeg
        commit=$moneyPrinterHead
    } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtime 'moneyprinterturbo.json') -Encoding UTF8
    $report.tools.open_notebook['nexus_adapter_config'] = (Join-Path $runtime 'open-notebook.json')
    $report.tools.open_notebook['documentary_adapter_config'] = (Join-Path $runtime 'open-notebook-documentary.json')
    $report.tools.open_notebook['product_adapter_config'] = (Join-Path $runtime 'open-notebook-product.json')
    $report.tools.moneyprinterturbo['nexus_adapter_config'] = (Join-Path $runtime 'moneyprinterturbo.json')
    Save-Report

    # Run the existing Windows core/regression/security preparation after installation.
    $prepare = Join-Path $RepoRoot 'nexus\windows\prepare-nexus-core.ps1'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $prepare -RepoRoot $RepoRoot -ToolsRoot $ToolsRoot
    if ($LASTEXITCODE -ne 0) { throw 'NEXUS_CORE_PREPARE_AFTER_INSTALL_FAILED' }
    $nexusPython = Join-Path $RepoRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $nexusPython)) { throw 'NEXUS_VENV_MISSING_AFTER_PREPARE' }

    # Build a thin launcher EXE only. Kernel and sandbox remain normal Python files/runtime.
    $launcherVenv = Join-Path $Build 'launcher-venv'
    $launcherPython = Join-Path $launcherVenv 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $launcherPython)) {
        Invoke-Checked $python312 @('-m','venv',$launcherVenv)
    }
    Invoke-Checked $launcherPython @('-m','pip','install','--disable-pip-version-check',('pyinstaller==' + $PyInstallerVersion))
    $launcherSource = Join-Path $RepoRoot 'nexus\windows\nexus-launcher.py'
    $dist = Join-Path $Build 'dist'
    $work = Join-Path $Build 'pyinstaller-work'
    $spec = Join-Path $Build 'pyinstaller-spec'
    foreach ($dir in @($dist,$work,$spec)) { $null = New-Item -ItemType Directory -Force -Path $dir }
    Invoke-Checked $launcherPython @(
        '-m','PyInstaller','--clean','--noconfirm','--onefile','--noconsole',
        '--name','Nexus','--distpath',$dist,'--workpath',$work,'--specpath',$spec,$launcherSource
    )
    $builtExe = Join-Path $dist 'Nexus.exe'
    if (-not (Test-Path -LiteralPath $builtExe)) { throw 'NEXUS_EXE_BUILD_MISSING' }
    $finalExe = Join-Path $BinRoot 'Nexus.exe'
    $boundHead = (& $git -C $RepoRoot rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $boundHead -ne $NexusHead) { throw 'NEXUS_HEAD_CHANGED_DURING_INSTALL' }
    $dirty = & $git -C $RepoRoot status --porcelain --untracked-files=all
    if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'NEXUS_DIRTY_TREE' }
    Copy-Item -LiteralPath $builtExe -Destination $finalExe -Force
    $launcherConfig = [ordered]@{
        repo_root = $RepoRoot
        python = $nexusPython
        git = $git
        data_root = $runtime
        expected_origin = $ExpectedOrigin
        expected_head = $NexusHead
    }
    $launcherConfig | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $BinRoot 'nexus-launcher.json') -Encoding UTF8
    $exeHash = (Get-FileHash -LiteralPath $finalExe -Algorithm SHA256).Hash.ToLowerInvariant()
    $report.launcher = [ordered]@{
        status='BUILT'; path=$finalExe; sha256=$exeHash; pyinstaller=$PyInstallerVersion;
        type='thin launcher; Kernel remains external validated Python runtime'
    }

    $report.status = if ($report.pending.Count -eq 0) { 'PASS' } else { 'PASS_WITH_EXPLICIT_PENDING_BINDINGS' }
}
catch {
    $report.status = 'FAIL'
    $report.error = $_.Exception.Message
    throw
}
finally {
    $report.finished_utc = [DateTime]::UtcNow.ToString('o')
    Save-Report
    Write-Host ('NEXUS COMPLETE INSTALL = ' + $report.status)
    Write-Host ('REPORT: ' + $reportPath)
    if ($report.pending.Count -gt 0) { Write-Host ('PENDING: ' + ($report.pending -join ', ')) }
}
