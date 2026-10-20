[CmdletBinding()]
param(
    [string]$ToolsRoot = 'C:\Nexus-Tools'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function First-CommandPath {
    param([string[]]$Names)
    foreach ($name in $Names) {
        $cmd = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($cmd) { return $cmd.Source }
    }
    return $null
}

function First-ExistingPath {
    param([string[]]$Paths)
    foreach ($path in $Paths) {
        if ($path -and (Test-Path -LiteralPath $path)) {
            return (Resolve-Path -LiteralPath $path).Path
        }
    }
    return $null
}

$ToolsRoot = if (Test-Path -LiteralPath $ToolsRoot) {
    (Resolve-Path -LiteralPath $ToolsRoot).Path
} else {
    $ToolsRoot
}

$java = First-CommandPath @('java.exe')
$soffice = First-CommandPath @('soffice.com','soffice.exe')
$ffmpeg = First-CommandPath @('ffmpeg.exe')
$git = First-CommandPath @('git.exe')
$python = First-CommandPath @('py.exe','python.exe')

$programFilesX86 = [Environment]::GetFolderPath('ProgramFilesX86')
$zotero = First-ExistingPath @(
    (Join-Path $env:ProgramFiles 'Zotero\zotero.exe'),
    (Join-Path $programFilesX86 'Zotero\zotero.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Zotero\zotero.exe')
)

$openNotebook = First-ExistingPath @(
    (Join-Path $ToolsRoot 'OpenNotebook'),
    (Join-Path $env:USERPROFILE 'OpenNotebook'),
    (Join-Path $env:USERPROFILE 'open-notebook')
)

$languageTool = First-ExistingPath @(
    (Join-Path $ToolsRoot 'LanguageTool'),
    (Join-Path $env:USERPROFILE 'LanguageTool')
)

$ace = First-ExistingPath @(
    (Join-Path $ToolsRoot 'ACE-Step-1.5')
)

$forge = First-ExistingPath @(
    (Join-Path $ToolsRoot 'Forge')
)

$items = [ordered]@{
    git = [ordered]@{ status = if ($git) { 'FOUND' } else { 'MISSING' }; path = $git }
    python = [ordered]@{ status = if ($python) { 'FOUND' } else { 'MISSING' }; path = $python }
    java = [ordered]@{ status = if ($java) { 'FOUND' } else { 'MISSING' }; path = $java }
    libreoffice = [ordered]@{ status = if ($soffice) { 'FOUND' } else { 'MISSING' }; path = $soffice }
    zotero = [ordered]@{ status = if ($zotero) { 'FOUND' } else { 'MISSING' }; path = $zotero }
    ffmpeg = [ordered]@{ status = if ($ffmpeg) { 'FOUND' } else { 'MISSING' }; path = $ffmpeg }
    open_notebook = [ordered]@{ status = if ($openNotebook) { 'FOUND_PATH' } else { 'MISSING_OR_EXTERNAL' }; path = $openNotebook }
    languagetool = [ordered]@{ status = if ($languageTool) { 'FOUND_PATH' } else { 'MISSING_OR_EXTERNAL' }; path = $languageTool }
    ace_step = [ordered]@{ status = if ($ace) { 'FOUND_PATH' } else { 'MISSING_BLOCKED_BY_POLICY' }; path = $ace }
    forge = [ordered]@{ status = if ($forge) { 'FOUND_PATH' } else { 'MISSING_BLOCKED_BY_POLICY' }; path = $forge }
}

$report = [ordered]@{
    schema = 'nexus.external-inventory.v1'
    checked_utc = [DateTime]::UtcNow.ToString('o')
    tools_root = $ToolsRoot
    items = $items
    guarded_provisioning = [ordered]@{
        ace_step = 'BLOCKED_BY_POLICY'
        forge = 'BLOCKED_BY_POLICY'
        avatar_models = 'BLOCKED_BY_POLICY'
        isolation_account = 'BLOCKED_BY_POLICY'
    }
}

$missing = @($items.GetEnumerator() | Where-Object { $_.Value.status -like 'MISSING*' } | ForEach-Object { $_.Key })
$report['missing'] = $missing

if (-not (Test-Path -LiteralPath $ToolsRoot)) {
    $null = New-Item -ItemType Directory -Force -Path $ToolsRoot
}
$reportPath = Join-Path $ToolsRoot 'external-tools-inventory.json'
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8

Write-Host 'NEXUS EXTERNAL INVENTORY = PASS'
Write-Host ('REPORT: ' + $reportPath)
Write-Host ('MISSING: ' + ($missing -join ', '))
Write-Host 'Guarded provisioning was not executed.'
