param(
    [string]$LegacyData = 'C:\Nexus\dados',
    [string]$DataDirectory = (Join-Path $env:LOCALAPPDATA 'FolhaDagu')
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Index-Folha.ps1')
$legacy = [IO.Path]::GetFullPath($LegacyData).TrimEnd('\')
$library = Join-Path ([IO.Path]::GetFullPath($DataDirectory)) 'biblioteca'
$destinationRoot = Join-Path $library 'memorias'
if ($destinationRoot.StartsWith($legacy+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'A migração precisa de um destino separado dos originais.' }
$rows = [Collections.Generic.List[object]]::new()
foreach ($vault in @('creative','canonical')) {
    $sourceRoot = Join-Path $legacy $vault
    if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) { continue }
    foreach ($file in @(Get-FolhaIndexFiles $sourceRoot @('.md','.markdown','.txt','.json','.pdf','.odt','.docx','.mp3','.wav','.mp4','.png','.jpg','.jpeg'))) {
        $relative = $file.FullName.Substring($sourceRoot.Length+1)
        $destination = Join-Path (Join-Path $destinationRoot $vault) $relative
        $resolved = [IO.Path]::GetFullPath($destination)
        if (-not $resolved.StartsWith($destinationRoot+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Destino fora da pasta de memórias.' }
        $sourceHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        if (Test-Path -LiteralPath $resolved) {
            if ((Get-FileHash -LiteralPath $resolved -Algorithm SHA256).Hash.ToLowerInvariant() -cne $sourceHash) { throw ('A memória já existe com conteúdo diferente: '+$relative) }
        } else {
            New-Item -ItemType Directory -Path (Split-Path $resolved -Parent) -Force | Out-Null
            Copy-Item -LiteralPath $file.FullName -Destination $resolved
        }
        $destinationHash = (Get-FileHash -LiteralPath $resolved -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($destinationHash -cne $sourceHash) { throw ('A cópia não coincide com o original: '+$relative) }
        $rows.Add(@{vault=$vault;source=$file.FullName;destination=$resolved;sha256=$sourceHash;bytes=$file.Length;authority_preserved=$true})
    }
}
New-Item -ItemType Directory -Path $destinationRoot -Force | Out-Null
$manifest = @{version=1;copied_at=[DateTime]::UtcNow.ToString('o');originals_deleted=$false;files=$rows.ToArray()}
[IO.File]::WriteAllText((Join-Path $destinationRoot 'migration.json'),($manifest | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
Write-Output ('PASS: '+$rows.Count+' ficheiros de memória copiados e verificados; originais conservados.')
