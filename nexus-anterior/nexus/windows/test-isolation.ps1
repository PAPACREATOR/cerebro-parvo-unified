# Repeat only the synthetic access test; never reset account, password or ACL.
$ErrorActionPreference = 'Stop'
$root = 'C:\ProgramData\NexusMinimal'
$password = $null
try {
    $user = Get-LocalUser -Name Nexus
    if (-not (Test-Path -LiteralPath "$root\evidence")) { throw 'Area de ensaio ausente.' }
    'TEST_STARTED' | Set-Content -LiteralPath "$root\evidence\probe-stage.txt"
    Write-Host 'Repetir teste da conta Nexus existente. Nao altera a palavra-passe.'
    Write-Host 'Introduz a palavra-passe escolhida anteriormente para Nexus.'
    $password = Read-Host 'Palavra-passe de Nexus' -AsSecureString
    'CREDENTIAL_ENTERED' | Set-Content -LiteralPath "$root\evidence\probe-stage.txt"
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
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($child))
    $credential = [Management.Automation.PSCredential]::new("$env:COMPUTERNAME\Nexus",$password)
    $process = Start-Process -FilePath "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -ArgumentList @('-NoProfile','-NonInteractive','-EncodedCommand',$encoded) -Credential $credential -WorkingDirectory "$root\work" -WindowStyle Hidden -PassThru
    if (-not $process.WaitForExit(30000)) { Stop-Process -Id $process.Id -Force; throw 'Timeout do teste.' }
    $probe = Get-Content -LiteralPath "$root\work\probe-result.json" -Raw | ConvertFrom-Json
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
    $diagnostic | ConvertTo-Json | Set-Content -LiteralPath "$root\evidence\probe-error.json" -Encoding UTF8
    Write-Host 'Teste nao concluido. Diagnostico guardado para revisao.' -ForegroundColor Red
} finally {
    if ($null -ne $password) { $password.Dispose() }
}
Read-Host 'Carrega Enter para fechar'
