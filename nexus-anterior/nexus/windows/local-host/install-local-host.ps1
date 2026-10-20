[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$Root = 'C:\Nexus',
    [switch]$AuthorizeInstall,
    [switch]$ValidateOnly
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Assert-PlainPath {
    param([Parameter(Mandatory = $true)][string]$Path)
    $full = [IO.Path]::GetFullPath($Path)
    $cursor = $full
    while ($cursor) {
        if (Test-Path -LiteralPath $cursor) {
            $item = Get-Item -LiteralPath $cursor -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw 'Caminho redirecionado recusado.'
            }
        }
        $parent = [IO.Path]::GetDirectoryName($cursor.TrimEnd('\'))
        if (-not $parent -or $parent -eq $cursor) { break }
        $cursor = $parent
    }
    return $full
}

function Get-ContainedPath {
    param([string]$Parent, [string]$Relative)
    if ([IO.Path]::IsPathRooted($Relative) -or $Relative.Contains(':')) {
        throw 'Caminho relativo inválido.'
    }
    $base = [IO.Path]::GetFullPath($Parent).TrimEnd('\')
    $full = [IO.Path]::GetFullPath((Join-Path $base $Relative))
    if (-not $full.StartsWith($base + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Caminho fora da área autorizada.'
    }
    return Assert-PlainPath $full
}

function Get-Sha256 {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

$packageRoot = Assert-PlainPath $PSScriptRoot
$targetRoot = Assert-PlainPath $Root
if ($targetRoot.TrimEnd('\') -ne 'C:\Nexus' -or
    -not (Test-Path -LiteralPath $targetRoot -PathType Container)) {
    throw 'Este pacote adapta a instalação existente em C:\Nexus; não cria outro ambiente.'
}
$manifestPath = Get-ContainedPath $packageRoot 'local-host-manifest.json'
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.schema -ne 'nexus.local-host-sources.v1' -or
    $manifest.destination_root -ne 'C:\Nexus') {
    throw 'Manifesto local incompatível.'
}
$allowed = @(
    'abrir-nexus.py', 'Abrir Nexus.cmd', 'abrir-zotero.ps1',
    'configuracao/servicos-ia-local.py', 'configuracao/servicos-open-notebook.py',
    'configuracao/surreal-wsl.py', 'configuracao/ponte-piper-local.py',
    'configuracao/ponte-forge-local.py'
)
$files = @($manifest.files)
if ($files.Count -ne $allowed.Count) { throw 'Manifesto incompleto.' }
$seen = @{}
$plan = @()
foreach ($entry in $files) {
    $relative = [string]$entry.destination
    if ($allowed -cnotcontains $relative -or $seen.ContainsKey($relative) -or
        [string]$entry.package_path -cne ('files/' + $relative) -or
        [string]$entry.sha256 -cnotmatch '^[0-9a-f]{64}$') {
        throw 'Entrada do manifesto não autorizada.'
    }
    $seen[$relative] = $true
    $source = Get-ContainedPath $packageRoot ([string]$entry.package_path)
    $target = Get-ContainedPath $targetRoot $relative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf) -or
        (Get-Sha256 $source) -cne [string]$entry.sha256) {
        throw 'Fonte ausente ou diferente do manifesto.'
    }
    if ((Test-Path -LiteralPath $target) -and
        -not (Test-Path -LiteralPath $target -PathType Leaf)) {
        throw 'O destino existente não é um ficheiro.'
    }
    $before = if (Test-Path -LiteralPath $target -PathType Leaf) { Get-Sha256 $target } else { $null }
    $action = if ($before -ceq [string]$entry.sha256) { 'UNCHANGED' } elseif ($before) { 'REPLACE_WITH_BACKUP' } else { 'COPY_NEW' }
    $plan += [pscustomobject]@{
        destination = $relative; source = $source; target = $target
        source_sha256 = [string]$entry.sha256; before_sha256 = $before; action = $action
    }
}
$summary = [ordered]@{
    schema = 'nexus.local-host-install.v1'; mode = 'VALIDATION'; root = $targetRoot
    files = @($plan | Select-Object destination, action, source_sha256, before_sha256)
    starts_services = $false; modifies_data_or_configuration = $false
    modifies_windows_security = $false
}
if ($ValidateOnly) { $summary | ConvertTo-Json -Depth 6; return }
if (-not $AuthorizeInstall) { throw 'NEXUS_INSTALL_AUTHORIZATION_REQUIRED: usa -AuthorizeInstall para aplicar o plano.' }
$changed = @($plan | Where-Object { $_.action -ne 'UNCHANGED' })
if ($changed.Count -eq 0) {
    $summary.mode = 'UNCHANGED'
    $summary | ConvertTo-Json -Depth 6
    return
}
if (-not $PSCmdlet.ShouldProcess($targetRoot, 'Instalar oito scripts revistos com backup verificado; sem arrancar serviços')) {
    $summary.mode = 'WHAT_IF'
    $summary | ConvertTo-Json -Depth 6
    return
}

# Validate every source/target before creating a backup or replacing any file.
foreach ($item in $changed) {
    $null = Assert-PlainPath $item.source
    $null = Assert-PlainPath $item.target
    if ((Get-Sha256 $item.source) -cne $item.source_sha256) { throw 'A fonte mudou depois da preparação.' }
    $current = if (Test-Path -LiteralPath $item.target -PathType Leaf) { Get-Sha256 $item.target } else { $null }
    if ($current -cne $item.before_sha256) { throw 'O destino mudou depois da preparação.' }
}
$backupRelative = 'backups/local-host-' + [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss') + '-' + [Guid]::NewGuid().ToString('N')
$backupRoot = Get-ContainedPath $targetRoot $backupRelative
$null = New-Item -ItemType Directory -Path $backupRoot
$backupEntries = @()
foreach ($item in $changed) {
    if ($item.before_sha256) {
        $backup = Get-ContainedPath $backupRoot $item.destination
        $null = New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($backup)) -Force
        [IO.File]::Copy($item.target, $backup, $false)
        if ((Get-Sha256 $backup) -cne $item.before_sha256 -or
            (Get-Sha256 $item.target) -cne $item.before_sha256) {
            throw 'Backup inconsistente; instalação interrompida antes de substituir scripts.'
        }
    }
    $backupEntries += [pscustomobject]@{
        destination = $item.destination; previous_sha256 = $item.before_sha256
        package_sha256 = $item.source_sha256; was_present = [bool]$item.before_sha256
    }
}
$backupManifest = Get-ContainedPath $backupRoot 'backup.json'
@{ schema = 'nexus.local-host-backup.v1'; created_at = [DateTime]::UtcNow.ToString('o'); root = $targetRoot; files = $backupEntries } |
    ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $backupManifest -Encoding UTF8

foreach ($item in $changed) {
    $null = Assert-PlainPath $item.target
    $current = if (Test-Path -LiteralPath $item.target -PathType Leaf) { Get-Sha256 $item.target } else { $null }
    if ($current -cne $item.before_sha256) { throw 'O destino mudou durante o backup; cópias preservadas.' }
    $parent = [IO.Path]::GetDirectoryName($item.target)
    $null = New-Item -ItemType Directory -Path $parent -Force
    $temporary = Get-ContainedPath $targetRoot ($item.destination + '.nexus-install-' + [Guid]::NewGuid().ToString('N') + '.tmp')
    try {
        [IO.File]::Copy($item.source, $temporary, $false)
        if ((Get-Sha256 $temporary) -cne $item.source_sha256) { throw 'Cópia temporária inconsistente.' }
        if ($item.before_sha256) { [IO.File]::Replace($temporary, $item.target, $null) }
        else { [IO.File]::Move($temporary, $item.target) }
        if ((Get-Sha256 $item.target) -cne $item.source_sha256) { throw 'Verificação final falhou; backup preservado.' }
    } finally {
        if (Test-Path -LiteralPath $temporary -PathType Leaf) {
            $null = Assert-PlainPath $temporary
            Remove-Item -LiteralPath $temporary -Force
        }
    }
}
$summary.mode = 'INSTALLED'
$summary.backup = $backupRoot
$summary.backup_restore_demonstrated = $false
$summary | ConvertTo-Json -Depth 6
