param([switch]$Verificar)
$ErrorActionPreference = 'Stop'
$zoteroRoot = 'C:\Nexus'
$zoteroExe = Join-Path $zoteroRoot 'ferramentas\zotero\zotero.exe'
$zoteroProfile = Join-Path $zoteroRoot 'dados\zotero\perfil'
$zoteroLibrary = Join-Path $zoteroRoot 'dados\zotero\biblioteca'

function Test-ZoteroApi {
    try {
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:23119/api/users/0/items?limit=1' -UseBasicParsing -DisableKeepAlive -UserAgent 'Nexus-Local/1.0' -TimeoutSec 3
        return ($response.StatusCode -eq 200 -and $response.Headers['Zotero-API-Version'] -eq '3' -and $response.Headers['Zotero-Server-ID'])
    } catch { return $false }
}
if (Test-ZoteroApi) { Write-Output 'Zotero disponível.'; exit 0 }
if ($Verificar) { Write-Output 'Zotero indisponível.'; exit 1 }
if (-not (Test-Path -LiteralPath $zoteroExe -PathType Leaf) -or
    -not (Test-Path -LiteralPath $zoteroProfile -PathType Container) -or
    -not (Test-Path -LiteralPath (Join-Path $zoteroLibrary 'zotero.sqlite') -PathType Leaf)) {
    throw 'Instalação, perfil ou biblioteca Nexus ausente.'
}
# Do not create a competing profile instance if Zotero is already open.
$zoteroProcesses = @(Get-CimInstance Win32_Process -Filter "Name='zotero.exe'")
if ($zoteroProcesses.Count -eq 0) {
    Start-Process -FilePath $zoteroExe -ArgumentList @('-no-remote', '-profile', ('"' + $zoteroProfile + '"')) -WorkingDirectory $zoteroRoot -WindowStyle Hidden
}
$zoteroDeadline = [DateTime]::UtcNow.AddSeconds(45)
do {
    if (Test-ZoteroApi) { Write-Output 'Zotero disponível com biblioteca Nexus.'; exit 0 }
    Start-Sleep -Milliseconds 500
} while ([DateTime]::UtcNow -lt $zoteroDeadline)
throw 'Zotero não disponibilizou a API. Verifica o perfil e a aplicação aberta.'
