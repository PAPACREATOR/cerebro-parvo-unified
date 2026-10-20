param([Parameter(Mandatory=$true)][string]$TestDirectory)
$ErrorActionPreference='Stop'
. (Join-Path (Split-Path $PSScriptRoot -Parent) 'Submit-Folha.ps1')
$root=Join-Path $TestDirectory ([Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root -Force | Out-Null
foreach($case in @('valid','tampered','missing','invalid-name')) {
    $directory=Join-Path $root $case
    New-Item -ItemType Directory -Path $directory | Out-Null
    [IO.File]::WriteAllText((Join-Path $directory 'content.md'),'Candidate test result.')
    $file=Join-Path $directory 'resultado.mp3'
    [IO.File]::WriteAllBytes($file,[byte[]](1,2,3,4))
    $hash=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
    $name='resultado.mp3'
    if($case -eq 'tampered'){[IO.File]::WriteAllBytes($file,[byte[]](4,3,2,1))}
    if($case -eq 'missing'){$name='resultado.wav'}
    if($case -eq 'invalid-name'){$name='../resultado.mp3'}
    Write-FolhaJson (Join-Path $directory 'artifacts.json') @(@{name=$name;sha256=$hash;label='Test'})
    $process=Start-Process -FilePath (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') -ArgumentList @('-NoProfile','-NonInteractive','-Command','exit 0') -WindowStyle Hidden -PassThru
    $null=$process.Handle
    $process.WaitForExit()
    $job=@{Directory=$directory;Process=$process;State=@{status='RUNNING';content='';message='';has_pdf=$false}}
    Update-FolhaRun $job
    $expected=if($case -eq 'valid'){'DONE'}else{'FAIL'}
    if($job.State.status -ne $expected){throw "Wrong status for $case"}
    if(-not (Test-Path -LiteralPath (Join-Path $directory 'state.json'))){throw 'State not persisted.'}
    $process.Dispose()
}
'PASS: artifact integrity checked; tampered, missing and invalid files fail without crashing the server loop.'
