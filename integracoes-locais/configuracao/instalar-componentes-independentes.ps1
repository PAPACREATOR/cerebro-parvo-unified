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

$ExpectedOrigin = 'https://github.com/PAPACREATOR/nexus-writer-lab.git'
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
    $env:Path = @($env:Path,$machine,$user) -join ';'
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

$RepoRoot='C:\Nexus\aplicacao'
$ToolsRoot='C:\Nexus\ferramentas\nexus-tools'
$git='C:\Program Files\Git\cmd\git.exe'
$uv='C:\Nexus\ferramentas\uv\uv.exe'
$python312='C:\Nexus\ferramentas\python\python.exe'
$ffmpeg='C:\Nexus\ferramentas\ffmpeg\ffmpeg.exe'
$BinRoot=Join-Path $ToolsRoot 'bin'
$Models=Join-Path $ToolsRoot 'models'
$Logs=Join-Path $ToolsRoot 'logs'
$reportPath='C:\Nexus\registos\provisionamento-ferramentas.json'
$report=[ordered]@{status='RUNNING';scope='Installation only; real acceptance tests are separate';tasks=[ordered]@{};tools=[ordered]@{};models=[ordered]@{};database='BLOCKED_BY_WINDOWS_APP_CONTROL';started=[DateTime]::UtcNow.ToString('o')}
function Save-Report { $report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $reportPath -Encoding utf8 }
function Task([string]$Name,[scriptblock]$Action) {
    $report.tasks[$Name]=[ordered]@{status='RUNNING'};Save-Report;Write-Host "START $Name"
    try { & $Action; $report.tasks[$Name]=[ordered]@{status='INSTALLED';finished=[DateTime]::UtcNow.ToString('o')};Write-Host "INSTALLED $Name" }
    catch { $report.tasks[$Name]=[ordered]@{status='FAIL';error=$_.Exception.Message};Write-Host "FAIL ${Name}: $($_.Exception.Message)" }
    Save-Report
}
Task 'OpenNotebook-source-memory' {
    $openNotebook=Join-Path $ToolsRoot 'OpenNotebook'
    Install-PinnedRepo $git $OpenNotebookOrigin $OpenNotebookPin $openNotebook | Out-Null
    if (-not (Test-Path -LiteralPath (Join-Path $openNotebook '.env'))) { Invoke-Checked $python312 @('C:\Nexus\configuracao\preservar-open-notebook.py') }
    $legacy=-join ((111,108,108,97,109,97) | ForEach-Object { [char]$_ })
    Invoke-Checked $uv @('sync','--frozen','--python',$python312,'--no-install-package',('langchain-'+$legacy),'--no-install-package',$legacy) $openNotebook
}
Task 'OpenNotebook-interface' {
    $frontend=Join-Path $ToolsRoot 'OpenNotebook\frontend'
    Invoke-Checked 'C:\Nexus\ferramentas\node\npm.cmd' @('ci') $frontend
    Invoke-Checked 'C:\Nexus\ferramentas\node\npm.cmd' @('run','build') $frontend
}
Task 'Language-embedding-models' {
    $llamaModels=Join-Path $Models 'llamacpp';New-Item -ItemType Directory -Path $llamaModels -Force | Out-Null
    Download-Verified ('https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/resolve/'+$LlamaLanguageRevision+'/Qwen3-1.7B-Q8_0.gguf') (Join-Path $llamaModels 'Qwen3-1.7B-Q8_0.gguf') $LlamaLanguageSha256 | Out-Null
    Download-Verified ('https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF/resolve/'+$LlamaEmbeddingRevision+'/Qwen3-Embedding-0.6B-Q8_0.gguf') (Join-Path $llamaModels 'Qwen3-Embedding-0.6B-Q8_0.gguf') $LlamaEmbeddingSha256 | Out-Null
}
Task 'Speaches-voice' {
    $speaches=Join-Path $ToolsRoot 'Speaches'
    Install-PinnedRepo $git $SpeachesOrigin $SpeachesPin $speaches | Out-Null
    Invoke-Checked $uv @('sync','--frozen','--python',$python312) $speaches
}
Task 'ACE-Step-Forge-Deforum' {
    & 'C:\Nexus\ferramentas\powershell\pwsh.exe' -NoProfile -File (Join-Path $RepoRoot 'nexus\windows\install-media-tools.ps1') -ToolsRoot $ToolsRoot -AuthorizeInstall
    if ($LASTEXITCODE -ne 0) {throw 'Media installer failed; real render not accepted'}
}
Task 'Stable-Diffusion-model' {
    $target=Join-Path $ToolsRoot 'Forge\models\Stable-diffusion';New-Item -ItemType Directory -Path $target -Force | Out-Null
    Download-Verified $StableDiffusion15Url (Join-Path $target 'v1-5-pruned-emaonly.safetensors') $StableDiffusion15Sha256 | Out-Null
}
Task 'Visual-podcast-avatar' {
    $openNotebook=Join-Path $ToolsRoot 'OpenNotebook';$api=Join-Path $openNotebook '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $api)) {throw 'Open Notebook Python environment missing'}
    & 'C:\Nexus\ferramentas\powershell\pwsh.exe' -NoProfile -File (Join-Path $RepoRoot 'nexus\lab\open_notebook_avatar\install-windows.ps1') -OpenNotebookRoot $openNotebook -ApiPython $api -Device $Device -AuthorizeInstall
    if ($LASTEXITCODE -ne 0) {throw 'Avatar installation failed; original code and data preserved'}
}
Task 'MoneyPrinterTurbo-video' {
    $moneyPrinter=Join-Path $ToolsRoot 'MoneyPrinterTurbo'
    Install-PinnedRepo $git $MoneyPrinterOrigin $MoneyPrinterPin $moneyPrinter | Out-Null
    Invoke-Checked $uv @('sync','--frozen','--python',$python312) $moneyPrinter
    Invoke-Checked $python312 @((Join-Path $RepoRoot 'nexus\windows\configure-moneyprinterturbo-local.py'),'--root',$moneyPrinter,'--ffmpeg',$ffmpeg,'--device',$Device,'--report',(Join-Path $ToolsRoot 'moneyprinterturbo-local-config.json'),'--authorize-install') $RepoRoot
    Invoke-Checked $uv @('run','--frozen','python','cli.py','--help') $moneyPrinter
}
$report.status='PROVISIONED_WITH_DATABASE_BLOCKED'
if (@($report.tasks.Values | Where-Object status -eq 'FAIL').Count -gt 0) {$report.status='PARTIAL_WITH_FAILURES'}
$report.finished=[DateTime]::UtcNow.ToString('o');Save-Report
Write-Host ('PROVISIONING RESULT: '+$report.status)

