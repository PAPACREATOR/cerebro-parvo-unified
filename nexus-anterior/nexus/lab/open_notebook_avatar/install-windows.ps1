[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$OpenNotebookRoot,
    [Parameter(Mandatory=$true)][string]$ApiPython,
    [ValidateSet('cpu','cuda')][string]$Device = 'cpu',
    [switch]$AuthorizeInstall
)
$ErrorActionPreference = 'Stop'

# Explicit human-authorized installation gate. Accidental/direct invocation remains fail-closed.
if (-not $AuthorizeInstall) {
    throw 'NEXUS_INSTALL_AUTHORIZATION_REQUIRED: rerun with -AuthorizeInstall only after explicit human approval.'
}

$root = (Resolve-Path -LiteralPath $OpenNotebookRoot).Path
$api = (Get-Command $ApiPython -CommandType Application -ErrorAction Stop).Source
$workerDir = Join-Path $root 'venv-avatar'
$worker = Join-Path $workerDir 'Scripts/python.exe'
if (-not (Test-Path -LiteralPath $worker)) {
    & $api -m venv $workerDir
    if ($LASTEXITCODE -ne 0) { throw 'Worker environment creation failed' }
}
function Run-Step {
    param([string]$Python, [string[]]$Arguments)
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) { throw 'Avatar installation step failed; do not mark PASS' }
}
$index = if ($Device -eq 'cuda') { 'https://download.pytorch.org/whl/cu124' } else { 'https://download.pytorch.org/whl/cpu' }
Run-Step $worker @('-m','pip','install','torch==2.5.1','torchvision==0.20.1','--index-url',$index)
Run-Step $worker @('-m','pip','install','--only-binary=av','-r',(Join-Path $PSScriptRoot 'requirements-worker.txt'),'gdown==6.4.1',($PSScriptRoot + '[mcp]'))
$uv = (Get-Command uv.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
& $uv pip install --python $api $PSScriptRoot
if ($LASTEXITCODE -ne 0) { throw 'Avatar API extension installation failed; do not mark PASS' }
$models = Join-Path $root 'data/avatar-models'
$portraits = Join-Path $root 'data/avatars'
$outputs = Join-Path $root 'data/avatar-videos'
foreach ($directory in @($models,$portraits,$outputs)) {
    $null = New-Item -ItemType Directory -Path $directory -Force
}
Run-Step $worker @((Join-Path $PSScriptRoot 'provision_models.py'),$models,'--authorize-install')
Run-Step $worker @('-c',"import shutil; assert shutil.which('ffmpeg') and shutil.which('ffprobe'); from lipsync import LipSync; print('DEPENDENCIES=PASS')")
Run-Step $api @((Join-Path $PSScriptRoot 'install_router.py'),$root)
# Preserve unrelated settings and secrets. Only these four capability paths are changed.
$envPath = Join-Path $root '.env'
$text = if (Test-Path -LiteralPath $envPath) { [System.IO.File]::ReadAllText($envPath) } else { '' }
$values = [ordered]@{
    OPEN_NOTEBOOK_AVATAR_ROOT = $portraits.Replace('\','/')
    OPEN_NOTEBOOK_AVATAR_OUTPUT = $outputs.Replace('\','/')
    OPEN_NOTEBOOK_AVATAR_CHECKPOINT = (Join-Path $models 'wav2lip.pth').Replace('\','/')
    OPEN_NOTEBOOK_AVATAR_PYTHON = $worker.Replace('\','/')
}
foreach ($key in $values.Keys) {
    $text = [regex]::Replace($text, '(?m)^' + [regex]::Escape($key) + '=.*\r?\n?', '')
    $text = $text.TrimEnd() + "`n" + $key + '="' + $values[$key] + '"' + "`n"
}
if (Test-Path -LiteralPath $envPath) {
    Copy-Item -LiteralPath $envPath -Destination ($envPath + '.pre-avatar-' + [guid]::NewGuid().ToString('N'))
}
$temporary = $envPath + '.tmp-' + [guid]::NewGuid().ToString('N')
[System.IO.File]::WriteAllText($temporary, $text, [System.Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $temporary -Destination $envPath -Force
Write-Output 'INSTALLATION COMPLETE. Restart Open Notebook; place your portrait in data/avatars.'
Write-Output 'Real render/Windows acceptance is a separate gate. CUDA use must pass a CUDA test.'
