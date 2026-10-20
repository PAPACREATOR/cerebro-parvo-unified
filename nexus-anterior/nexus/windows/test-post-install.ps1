[CmdletBinding()]
param(
    [string]$RepoRoot = '',
    [string]$ToolsRoot = 'C:\Nexus-Tools'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($env:OS -ne 'Windows_NT' -or -not [Environment]::Is64BitOperatingSystem) {
    throw 'NEXUS_WINDOWS_X64_REQUIRED'
}
if (-not $RepoRoot) {
    $RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
}
$RepoRoot = (Resolve-Path -LiteralPath $RepoRoot).Path
$ToolsRoot = (Resolve-Path -LiteralPath $ToolsRoot).Path
$installReportPath = Join-Path $ToolsRoot 'complete-install-report.json'
$reportPath = Join-Path $ToolsRoot 'post-install-acceptance-report.json'

$report = [ordered]@{
    schema = 'nexus.post-install-acceptance.v1'
    status = 'RUNNING'
    started_utc = [DateTime]::UtcNow.ToString('o')
    finished_utc = $null
    repo_root = $RepoRoot
    tools_root = $ToolsRoot
    nexus_head = $null
    install_head = $null
    stages = [ordered]@{}
    legacy_accounts_present = @()
    physical_limits = @(
        'This acceptance verifies installed runtimes, CUDA visibility, deterministic/security flows and real MCP calls.',
        'It does not claim a documentary/music/podcast render is artistically correct.',
        'Public Host routes that are intentionally not integrated remain BLOCKED by contract.'
    )
    error = $null
}

function Save-Report {
    $report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $reportPath -Encoding UTF8
}

function Stage-Pass([string]$Name, [object]$Value) {
    $report.stages[$Name] = [ordered]@{ status='PASS'; evidence=$Value }
    Save-Report
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory = $RepoRoot
    )
    Push-Location -LiteralPath $WorkingDirectory
    try {
        $output = & $FilePath @Arguments 2>&1 | Out-String
        if ($LASTEXITCODE -ne 0) {
            throw ('NEXUS_COMMAND_FAILED: ' + $FilePath + ' ' + ($Arguments -join ' ') + [Environment]::NewLine + $output)
        }
        return $output.Trim()
    }
    finally {
        Pop-Location
    }
}

function Wait-Http {
    param([string]$Uri,[int]$Seconds = 120)
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

function Run-Pytest {
    param([string]$Name, [string[]]$Targets, [hashtable]$Environment = @{})
    $python = Join-Path $RepoRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) { throw 'NEXUS_VENV_MISSING' }
    $saved = @{}
    foreach ($key in $Environment.Keys) {
        $saved[$key] = [Environment]::GetEnvironmentVariable($key, 'Process')
        [Environment]::SetEnvironmentVariable($key, [string]$Environment[$key], 'Process')
    }
    try {
        $args = @('-m','pytest') + $Targets + @('-q','-p','no:cacheprovider','-o','pythonpath=.')
        $out = Invoke-Checked $python $args $RepoRoot
        Stage-Pass $Name $out
    }
    finally {
        foreach ($key in $Environment.Keys) {
            [Environment]::SetEnvironmentVariable($key, $saved[$key], 'Process')
        }
    }
}

try {
    Save-Report
    if (-not (Test-Path -LiteralPath $installReportPath)) { throw 'NEXUS_INSTALL_REPORT_MISSING' }
    $install = Get-Content -LiteralPath $installReportPath -Raw | ConvertFrom-Json
    if ($install.status -ne 'PASS') { throw ('NEXUS_INSTALL_NOT_PASS: ' + $install.status) }
    $report.install_head = $install.nexus_head

    $git = $install.tools.git.path
    if (-not (Test-Path -LiteralPath $git)) { throw 'NEXUS_GIT_MISSING_AFTER_INSTALL' }
    $head = (Invoke-Checked $git @('rev-parse','HEAD') $RepoRoot).Trim()
    $report.nexus_head = $head
    if ($head -ne $install.nexus_head) { throw 'NEXUS_INSTALL_HEAD_MISMATCH: install and test must use the same exact revision.' }
    $dirty = (Invoke-Checked $git @('status','--porcelain=v1','--untracked-files=all') $RepoRoot).Trim()
    if ($dirty) { throw 'NEXUS_DIRTY_TREE: acceptance requires the exact installed source tree.' }
    Stage-Pass 'install-report' ([ordered]@{status=$install.status; head=$head})

    # Current isolation model: no reusable Nexus/NexusTool credentials.
    foreach ($name in @('Nexus','NexusTool')) {
        $account = Get-LocalUser -Name $name -ErrorAction SilentlyContinue
        if ($account) { $report.legacy_accounts_present += $name }
    }
    $sandbox = Get-Content -LiteralPath (Join-Path $RepoRoot 'nexus\windows_sandbox.py') -Raw
    foreach ($required in @('CreateAppContainerProfile','CreateJobObjectW','AssignProcessToJobObject','DeleteAppContainerProfile')) {
        if ($sandbox -notmatch [regex]::Escape($required)) { throw ('NEXUS_APPCONTAINER_CONTRACT_MISSING: ' + $required) }
    }
    foreach ($ARCHIVE_REDACTED_04 in @('LogonUser','CreateProcessAsUser','NexusTool')) {
        if ($sandbox -match [regex]::Escape($ARCHIVE_REDACTED_04)) { throw ('NEXUS_REUSABLE_TOOL_IDENTITY_FOUND: ' + $ARCHIVE_REDACTED_04) }
    }
    Stage-Pass 'windows-task-identity' ([ordered]@{mode='per-task AppContainer'; legacy_accounts=$report.legacy_accounts_present})

    $launcher = $install.launcher.path
    if (-not (Test-Path -LiteralPath $launcher)) { throw 'NEXUS_LAUNCHER_MISSING' }
    foreach ($name in @('languagetool.json','libreoffice.json','open-notebook.json','open-notebook-documentary.json','open-notebook-product.json','moneyprinterturbo.json')) {
        if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot ('nexus\runtime\' + $name)))) {
            throw ('NEXUS_RUNTIME_CONFIG_MISSING: ' + $name)
        }
    }
    Stage-Pass 'launcher-and-runtime' ([ordered]@{launcher=$launcher})

    # Structural matrix first: 300,000 deterministic bidirectional compatibility cases.
    Run-Pytest 'windows-stack-structural-300000' @('nexus/tests/test_windows_stack_structural_300k.py')

    # Installed executable/runtime smoke checks use exact installer paths.
    $versions = [ordered]@{}
    $versions.git = Invoke-Checked $install.tools.git.path @('--version')
    $versions.python = Invoke-Checked $install.tools.python312.path @('--version')
    $versions.node = Invoke-Checked $install.tools.node.path @('--version')
    $versions.java = Invoke-Checked $install.tools.java.path @('-version')
    $versions.libreoffice = Invoke-Checked $install.tools.libreoffice.path @('--version')
    $versions.ffmpeg = (Invoke-Checked $install.tools.ffmpeg.path @('-version')).Split([Environment]::NewLine)[0]
    if (-not (Test-Path -LiteralPath $install.tools.zotero.path)) { throw 'NEXUS_ZOTERO_MISSING' }
    $versions.zotero = (Get-Item -LiteralPath $install.tools.zotero.path).VersionInfo.FileVersion
    $zoteroOxt = [string]$install.tools.zotero.libreoffice_oxt
    if (-not $zoteroOxt -or -not (Test-Path -LiteralPath $zoteroOxt)) { throw 'NEXUS_ZOTERO_LIBREOFFICE_EXTENSION_MISSING' }
    $zoteroExtensions = Invoke-Checked $install.tools.unopkg.path @('list')
    if ($zoteroExtensions -notmatch '(?i)zotero') { throw 'NEXUS_ZOTERO_LIBREOFFICE_EXTENSION_NOT_REGISTERED' }
    $versions.zotero_libreoffice = 'OXT_REGISTERED_JAVA_LIBREOFFICE_VERIFIED'

    $llamaServer = [string]$install.tools.llamacpp.path
    $versions.llamacpp = Invoke-Checked $llamaServer @('--version')
    $languageModel = [string]$install.models.llamacpp.language.path
    $embeddingModel = [string]$install.models.llamacpp.embedding.path
    $languageAlias = [string]$install.models.llamacpp.language.alias
    $embeddingAlias = [string]$install.models.llamacpp.embedding.alias
    $languagePort = [int]$install.tools.llamacpp.language_port
    $embeddingPort = [int]$install.tools.llamacpp.embedding_port
    foreach ($modelPath in @($languageModel,$embeddingModel)) {
        if (-not (Test-Path -LiteralPath $modelPath)) { throw ('NEXUS_LLAMACPP_MODEL_MISSING: ' + $modelPath) }
    }

    $llamaLangOut = Join-Path $ToolsRoot 'logs\post-llamacpp-language.stdout.txt'
    $llamaLangErr = Join-Path $ToolsRoot 'logs\post-llamacpp-language.stderr.txt'
    $llamaEmbOut = Join-Path $ToolsRoot 'logs\post-llamacpp-embedding.stdout.txt'
    $llamaEmbErr = Join-Path $ToolsRoot 'logs\post-llamacpp-embedding.stderr.txt'
    $llamaLangProcess = $null
    $llamaEmbProcess = $null
    try {
        $llamaLangProcess = Start-Process -FilePath $llamaServer -ArgumentList @(
            '-m',('"' + $languageModel + '"'),'--host','127.0.0.1','--port',[string]$languagePort,
            '--alias',$languageAlias,'-c','8192','-ngl','99'
        ) -RedirectStandardOutput $llamaLangOut -RedirectStandardError $llamaLangErr -PassThru -WindowStyle Hidden
        Wait-Http ('http://127.0.0.1:' + $languagePort + '/health') 180

        $llamaEmbProcess = Start-Process -FilePath $llamaServer -ArgumentList @(
            '-m',('"' + $embeddingModel + '"'),'--host','127.0.0.1','--port',[string]$embeddingPort,
            '--alias',$embeddingAlias,'--embedding','--pooling','last',
            '-c','8192','-ngl','99','-np','1','--no-cont-batching'
        ) -RedirectStandardOutput $llamaEmbOut -RedirectStandardError $llamaEmbErr -PassThru -WindowStyle Hidden
        Wait-Http ('http://127.0.0.1:' + $embeddingPort + '/health') 180

        $languageBody = @{
            model=$languageAlias
            messages=@(@{role='user'; content='Reply briefly with the word Nexus.'})
            max_tokens=32
            temperature=0
        } | ConvertTo-Json -Depth 5
        $languageResult = Invoke-RestMethod -Method Post -Uri ('http://127.0.0.1:' + $languagePort + '/v1/chat/completions') -ContentType 'application/json' -Body $languageBody -TimeoutSec 120
        if (-not $languageResult.choices -or $languageResult.choices.Count -lt 1) { throw 'NEXUS_LLAMACPP_LANGUAGE_PROBE_FAILED' }
        Stage-Pass 'llamacpp-language-real' ([ordered]@{model=$languageAlias; port=$languagePort; choices=$languageResult.choices.Count})

        $embeddingBody = @{model=$embeddingAlias; input='nexus post install bidirectional embedding probe'} | ConvertTo-Json
        $embeddingResult = Invoke-RestMethod -Method Post -Uri ('http://127.0.0.1:' + $embeddingPort + '/v1/embeddings') -ContentType 'application/json' -Body $embeddingBody -TimeoutSec 120
        $dimensions = $embeddingResult.data[0].embedding.Count
        if (-not $embeddingResult.data -or $dimensions -lt 32) { throw 'NEXUS_LLAMACPP_EMBEDDING_PROBE_FAILED' }
        Stage-Pass 'llamacpp-embedding-real' ([ordered]@{model=$embeddingAlias; port=$embeddingPort; dimensions=$dimensions})
    }
    finally {
        foreach ($process in @($llamaEmbProcess,$llamaLangProcess)) {
            if ($process -and -not $process.HasExited) {
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
                $process.WaitForExit()
            }
        }
    }
    Stage-Pass 'installed-runtimes' $versions

    # GPU/runtime proof without claiming a real render.
    $forgePython = Join-Path $install.tools.forge.path 'venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $forgePython)) { throw 'NEXUS_FORGE_PYTHON_MISSING' }
    $forgeCuda = Invoke-Checked $forgePython @('-c','import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))') $install.tools.forge.path
    Stage-Pass 'forge-cuda' $forgeCuda

    $mediaReport = Get-Content -LiteralPath (Join-Path $ToolsRoot 'nexus-media-tools.json') -Raw | ConvertFrom-Json
    $uv = $install.tools.uv.path
    $aceImport = Invoke-Checked $uv @('run','--no-sync','python','-c','import acestep; import acestep.api_server; print("ACE_STEP_IMPORT=PASS")') $mediaReport.ace_step.path
    Stage-Pass 'ace-step-runtime' $aceImport
    $aceCuda = Invoke-Checked $uv @(
        'run','--no-sync','python','-c',
        'import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0)); print(torch.__version__)'
    ) $mediaReport.ace_step.path
    Stage-Pass 'ace-step-cuda' $aceCuda

    # Real local TTS probe using the exact Speaches/Kokoro installation.
    $speachesRoot = [string]$install.tools.speaches.path
    $speechOutLog = Join-Path $ToolsRoot 'logs\post-speaches.stdout.txt'
    $speechErrLog = Join-Path $ToolsRoot 'logs\post-speaches.stderr.txt'
    $speechProbeFile = Join-Path $ToolsRoot 'post-install-kokoro-probe.wav'
    $speechProcess = $null
    try {
        $speechProcess = Start-Process -FilePath $uv -ArgumentList @(
            'run','uvicorn','--factory','--host','127.0.0.1','--port','8969','speaches.main:create_app'
        ) -WorkingDirectory $speachesRoot -RedirectStandardOutput $speechOutLog -RedirectStandardError $speechErrLog -PassThru -WindowStyle Hidden
        Wait-Http 'http://127.0.0.1:8969/v1/models' 120
        $speechBody = @{
            input='Nexus local speech acceptance.'
            model='speaches-ai/Kokoro-82M-v1.0-ONNX'
            voice='af_heart'
            response_format='wav'
            speed=1
        } | ConvertTo-Json
        Invoke-WebRequest -Method Post -Uri 'http://127.0.0.1:8969/v1/audio/speech' -ContentType 'application/json' -Body $speechBody -OutFile $speechProbeFile -UseBasicParsing -TimeoutSec 120
        $speechBytes = (Get-Item -LiteralPath $speechProbeFile).Length
        if ($speechBytes -lt 1000) { throw 'NEXUS_KOKORO_TTS_PROBE_TOO_SMALL' }
        Stage-Pass 'speaches-kokoro-real' ([ordered]@{model='speaches-ai/Kokoro-82M-v1.0-ONNX'; voice='af_heart'; bytes=$speechBytes})
    }
    finally {
        if ($speechProcess -and -not $speechProcess.HasExited) {
            Stop-Process -Id $speechProcess.Id -Force -ErrorAction SilentlyContinue
            $speechProcess.WaitForExit()
        }
    }

    $mptRoot = $install.tools.moneyprinterturbo.path
    $mptHelp = Invoke-Checked $uv @('run','--frozen','python','cli.py','--help') $mptRoot
    Stage-Pass 'moneyprinterturbo-cli' (($mptHelp -split [Environment]::NewLine | Select-Object -First 5) -join [Environment]::NewLine)

    # Normal Nexus suites after the 300,000-case structural gate.
    foreach ($suite in @('core','blocks','practical')) {
        $dir = Join-Path $ToolsRoot ('post-install-' + $suite)
        if (Test-Path -LiteralPath $dir) { Remove-Item -LiteralPath $dir -Recurse -Force }
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $RepoRoot 'nexus\windows\check-nexus.ps1') -PythonPath (Join-Path $RepoRoot '.venv\Scripts\python.exe') -Suite $suite -ReportDirectory $dir
        if ($LASTEXITCODE -ne 0) { throw ('NEXUS_POST_INSTALL_SUITE_FAILED: ' + $suite) }
        $state = Get-Content -LiteralPath (Join-Path $dir 'state.json') -Raw | ConvertFrom-Json
        if ($state.status -ne 'PASS') { throw ('NEXUS_POST_INSTALL_SUITE_NOT_PASS: ' + $suite) }
        Stage-Pass ('suite-' + $suite) $state
    }

    # Real Writer gate: fixed .ott -> ODT -> round-trip -> PDF using installed LibreOffice.
    Run-Pytest 'writer-libreoffice-real' @('nexus/tests/test_writer_real_libreoffice.py') @{
        NEXUS_REAL_WRITER='1'
        LIBREOFFICE_EXE=$install.tools.libreoffice.path
    }

    # Product/system stress. These use temp data only and cannot promote Canonical.
    Run-Pytest 'product-flows-30000' @('nexus/tests/test_product_flows_5000.py')
    Run-Pytest 'public-routes-6x10000' @('nexus/tests/test_public_product_routes_10000.py')
    Run-Pytest 'public-routes-all-50000' @('nexus/tests/test_public_product_routes_all_50000.py')
    Run-Pytest 'product-system-50000' @('nexus/tests/test_product_system_50000.py')
    Run-Pytest 'product-themes-canonical-200000' @('nexus/tests/test_product_themes_canonical_200k.py')
    Run-Pytest 'varied-200000' @('nexus/tests/test_system_varied_200k.py')
    Run-Pytest 'authority-and-native-boundary' @(
        'nexus/security_tests/test_authority_10000.py',
        'nexus/security_tests/test_native_boundary.py',
        'nexus/security_tests/test_confinement_gate.py'
    )
    Run-Pytest 'bidirectional-50000-real-mcp' @('nexus/tests/test_bidirectional_50000.py') @{NEXUS_RUN_50K='1'}

    $report.status = 'PASS'
}
catch {
    $report.status = 'FAIL'
    $report.error = $_.Exception.Message
    throw
}
finally {
    $report.finished_utc = [DateTime]::UtcNow.ToString('o')
    Save-Report
    Write-Host ('NEXUS POST-INSTALL = ' + $report.status)
    Write-Host ('REPORT: ' + $reportPath)
    if ($report.legacy_accounts_present.Count -gt 0) {
        Write-Host ('LEGACY WINDOWS ACCOUNTS PRESENT, NOT USED: ' + ($report.legacy_accounts_present -join ', '))
    }
}
