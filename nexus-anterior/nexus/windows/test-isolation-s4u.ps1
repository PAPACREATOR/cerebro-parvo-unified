# Repeat only the synthetic access test; never reset account, password or ACL.
$ErrorActionPreference = 'Stop'
$root = 'C:\ProgramData\NexusMinimal'
$taskName = 'Nexus-Isolation-Probe-' + [guid]::NewGuid().ToString('N')
$registered = $false
try {
    $user = Get-LocalUser -Name Nexus
    if (-not (Test-Path -LiteralPath "$root\evidence")) { throw 'Area de ensaio ausente.' }
    'TEST_STARTED' | Set-Content -LiteralPath "$root\evidence\probe-stage.txt"
    $child = @'
$ErrorActionPreference = 'Stop'
$root = 'C:\ProgramData\NexusMinimal'
$result = [ordered]@{sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value;tests=[ordered]@{}}
function Probe($name,$action) {
    try { & $action | Out-Null; $result.tests[$name]='ALLOWED' }
    catch [UnauthorizedAccessException] { $result.tests[$name]='DENIED' }
    catch { $result.tests[$name]='ERROR' }
}
Probe 'work_write' { [IO.File]::WriteAllText("$root\work\probe.txt",'synthetic-output') }
Probe 'canonical_read' { [IO.File]::ReadAllText("$root\vaults\canonical\sentinel.txt") }
Probe 'canonical_write' { [IO.File]::WriteAllText("$root\vaults\canonical\sentinel.txt",'changed') }
Probe 'creative_read' { [IO.File]::ReadAllText("$root\vaults\creative\sentinel.txt") }
Probe 'creative_write' { [IO.File]::WriteAllText("$root\vaults\creative\sentinel.txt",'changed') }
Probe 'law_read' { [IO.File]::ReadAllText("$root\laws\sentinel.txt") }
Probe 'law_write' { [IO.File]::WriteAllText("$root\laws\sentinel.txt",'changed') }
Probe 'tool_write' { [IO.File]::WriteAllText("$root\tools\sentinel.txt",'changed') }
$result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath "$root\work\probe-result.json" -Encoding UTF8
'@
    $probeFile = 'probe-' + [guid]::NewGuid().ToString('N') + '.json'
    $child = $child.Replace('probe-result.json', $probeFile)
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($child))
    $action = New-ScheduledTaskAction -Execute "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -Argument "-NoProfile -NonInteractive -EncodedCommand $encoded" -WorkingDirectory "$root\work"
    $principal = New-ScheduledTaskPrincipal -UserId "$env:COMPUTERNAME\Nexus" -LogonType S4U -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Seconds 45) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    Register-ScheduledTask -TaskName $taskName -Action $action -Principal $principal -Settings $settings | Out-Null
    $registered = $true
    Start-ScheduledTask -TaskName $taskName
    $deadline = (Get-Date).AddSeconds(45)
    do { Start-Sleep -Milliseconds 500; $state = (Get-ScheduledTask -TaskName $taskName).State } while ($state -in @('Running','Queued') -and (Get-Date) -lt $deadline)
    $info = Get-ScheduledTaskInfo -TaskName $taskName
    if ($info.LastTaskResult -ne 0) { throw ('Scheduled task result: '+$info.LastTaskResult) }
    $probe = Get-Content -LiteralPath "$root\work\$probeFile" -Raw | ConvertFrom-Json
    $expected = @{work_write='ALLOWED';canonical_read='DENIED';canonical_write='DENIED';creative_read='DENIED';creative_write='DENIED';law_read='ALLOWED';law_write='DENIED';tool_write='DENIED'}
    $passed = $probe.sid -eq $user.SID.Value
    foreach ($key in $expected.Keys) { if ($probe.tests.$key -ne $expected[$key]) { $passed=$false } }
    $adminMember = @(Get-LocalGroupMember -SID 'S-1-5-32-544' | Where-Object {$_.SID -eq $user.SID}).Count -gt 0
    if ($adminMember) { $passed=$false }
    foreach ($folder in @('vaults\canonical','vaults\creative','laws','tools')) { if ((Get-Content -LiteralPath "$root\$folder\sentinel.txt" -Raw).Trim() -ne 'synthetic') { $passed=$false } }
    $report = [ordered]@{status=$(if($passed){'PASS'}else{'FAIL'});identity_verified=($probe.sid -eq $user.SID.Value);administrator=$adminMember;tests=$probe.tests;scope='Synthetic NTFS test only. Host integration, network and per-run isolation pending.';timestamp=(Get-Date).ToUniversalTime().ToString('o')}
    $report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$root\evidence\isolation-result.json" -Encoding UTF8
    $report | ConvertTo-Json -Depth 5 | Write-Host
} catch {
    $diagnostic = [ordered]@{status='FAIL';exception_type=$_.Exception.GetType().FullName;message=$_.Exception.Message;error_id=$_.FullyQualifiedErrorId;line=$_.InvocationInfo.ScriptLineNumber;timestamp=(Get-Date).ToUniversalTime().ToString('o')}
    $diagnostic | ConvertTo-Json | Set-Content -LiteralPath "$root\evidence\s4u-probe-error.json" -Encoding UTF8
    Write-Host 'Teste nao concluido. Diagnostico guardado para revisao.' -ForegroundColor Red
} finally {
    if ($registered) { Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue; Unregister-ScheduledTask -TaskName $taskName -Confirm:$false }
}

