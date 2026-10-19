param(
    [string]$InstallDirectory = (Join-Path $env:LOCALAPPDATA 'Programs\FolhaDagu'),
    [string]$DataDirectory = (Join-Path $env:LOCALAPPDATA 'FolhaDagu'),
    [string]$SqliteExe = (Join-Path $PSScriptRoot 'bin\sqlite3.exe'),
    [int]$Port = 8091
)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $InstallDirectory) { throw 'Já existe uma instalação da Folha neste destino. Inspeciona-a antes de atualizar.' }
$daguExe = Join-Path $env:LOCALAPPDATA 'Programs\Dagu\dagu.exe'
if (-not (Test-Path -LiteralPath $daguExe)) { throw 'Instala primeiro o Dagu.' }
if (-not (Test-Path -LiteralPath $SqliteExe -PathType Leaf)) { throw 'Indica o executável SQLite oficial em -SqliteExe.' }
New-Item -ItemType Directory -Path $InstallDirectory,$DataDirectory,(Join-Path $DataDirectory 'logs') -Force | Out-Null
foreach ($file in @('Start-Folha.ps1','Submit-Folha.ps1','Index-Folha.ps1','README.md')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $file) -Destination (Join-Path $InstallDirectory $file)
}
New-Item -ItemType Directory -Path (Join-Path $InstallDirectory 'bin') -Force | Out-Null
Copy-Item -LiteralPath $SqliteExe -Destination (Join-Path $InstallDirectory 'bin\sqlite3.exe')
foreach ($rule in Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'defaults\regras') -File) {
    $destination = Join-Path $DataDirectory ('biblioteca\regras\' + $rule.Name)
    New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force | Out-Null
    if (-not (Test-Path -LiteralPath $destination)) { Copy-Item -LiteralPath $rule.FullName -Destination $destination }
}
foreach ($folder in @('ui','templates')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $folder) -Destination (Join-Path $InstallDirectory $folder) -Recurse
}
$launcher = @'
$ErrorActionPreference = 'Stop'
$data = __DATA__
$origin = 'http://127.0.0.1:__PORT__'
$ready = $false
try {
    $health = Invoke-RestMethod -Uri ($origin + '/health') -TimeoutSec 2
    $ready = $health.service -eq 'FolhaDagu'
} catch { }
if (-not $ready) {
    $script = Join-Path $PSScriptRoot 'Start-Folha.ps1'
    Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"' + $script + '"'),'-Port','__PORT__','-DataDirectory',('"' + $data + '"')) -WindowStyle Hidden -WorkingDirectory $PSScriptRoot -RedirectStandardOutput (Join-Path $data 'logs\server.out.log') -RedirectStandardError (Join-Path $data 'logs\server.err.log') | Out-Null
    for ($attempt=0; $attempt -lt 40; $attempt++) {
        Start-Sleep -Milliseconds 250
        try { $health = Invoke-RestMethod -Uri ($origin + '/health') -TimeoutSec 2; if ($health.service -eq 'FolhaDagu') { $ready = $true; break } } catch { }
    }
}
if (-not $ready) { throw 'A Folha não conseguiu arrancar. Consulta os registos na pasta de dados.' }
$url = [IO.File]::ReadAllText((Join-Path $data 'launch-url.txt')).Trim()
if (-not $url.StartsWith($origin + '/#session=')) { throw 'Endereço de arranque inesperado.' }
Start-Process $url
'@
$launcher = $launcher.Replace('__DATA__', ("'" + $DataDirectory.Replace("'","''") + "'")).Replace('__PORT__',[string]$Port)
$launcherPath = Join-Path $InstallDirectory 'Abrir-Folha.ps1'
[IO.File]::WriteAllText($launcherPath,$launcher,[Text.UTF8Encoding]::new($true))
$shortcutPath = Join-Path ([Environment]::GetFolderPath('Programs')) 'Folha.lnk'
if (Test-Path -LiteralPath $shortcutPath) { $shortcutPath = Join-Path ([Environment]::GetFolderPath('Programs')) 'Folha Dagu.lnk' }
if (Test-Path -LiteralPath $shortcutPath) { throw 'Já existe um atalho Folha Dagu; não foi substituído.' }
$shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut($shortcutPath)
$shortcut.TargetPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "' + $launcherPath + '"'
$shortcut.WorkingDirectory = $InstallDirectory
$shortcut.Description = 'Folha local com workflows Dagu'
$shortcut.Save()
Write-Output ('Instalada em ' + $InstallDirectory)
Write-Output ('Atalho: ' + $shortcutPath)
