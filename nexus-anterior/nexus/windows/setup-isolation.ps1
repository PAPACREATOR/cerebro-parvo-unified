# Synthetic test only. Existing accounts and folders are never reset.
$ErrorActionPreference = 'Stop'

# Stop before any command, prompt, directory or external operation.
throw 'NEXUS_PROTECTED_PROVISIONING_PENDING: legacy global account setup is retired; use the Host per-task boundary.'

# Historical implementation retained below; unreachable while this gate is closed.
$root = 'C:\ProgramData\NexusMinimal'
$password = $null
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    if (-not ([Security.Principal.WindowsPrincipal]$identity).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Requer elevacao Windows.' }
    if ((Get-LocalUser Nexus -ErrorAction SilentlyContinue) -or (Test-Path -LiteralPath $root)) { throw 'Conta ou pasta existente. Rever antes de alterar.' }
    Write-Host 'Criar conta padrao Nexus e testar ACL com dados artificiais.'
    Write-Host 'A palavra-passe fica apenas em memoria. Nao a escrevas no chat.'
    $password = Read-Host 'Palavra-passe da nova conta Nexus' -AsSecureString
    $user = New-LocalUser -Name Nexus -Password $password -Description 'Nexus: ferramentas sem autoridade sobre cofres'
    Add-LocalGroupMember -SID 'S-1-5-32-545' -Member $user
    function Protect-Folder($path, $rights) {
        $acl = [Security.AccessControl.DirectorySecurity]::new()
        $acl.SetAccessRuleProtection($true,$false)
        $acl.SetOwner($identity.User)
        foreach ($sid in @($identity.User,[Security.Principal.SecurityIdentifier]::new('S-1-5-18'),[Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))) {
            $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow'))
        }
        if ($rights) { $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($user.SID,$rights,'ContainerInherit,ObjectInherit','None','Allow')) }
        Set-Acl -LiteralPath $path -AclObject $acl
    }
    New-Item -ItemType Directory -Path $root | Out-Null
    Protect-Folder $root 'ReadAndExecute'
    foreach ($folder in @('work','tools','laws','vaults','evidence')) {
        $path = Join-Path $root $folder
        New-Item -ItemType Directory -Path $path | Out-Null
        $rights = switch($folder) { 'work' {'Modify'} 'tools' {'ReadAndExecute'} 'laws' {'ReadAndExecute'} default {$null} }
        Protect-Folder $path $rights
    }
    foreach ($folder in @('creative','canonical')) { New-Item -ItemType Directory -Path "$root\vaults\$folder" | Out-Null }
    foreach ($folder in @('vaults\canonical','vaults\creative','laws','tools')) { 'synthetic' | Set-Content -LiteralPath "$root\$folder\sentinel.txt" }
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
    Write-Host ('FAIL: '+$_.Exception.Message) -ForegroundColor Red
    Write-Host 'Se existir criacao parcial, nao repetir nem apagar: rever o estado.'
} finally {
    if ($null -ne $password) { $password.Dispose() }
}
Read-Host 'Carrega Enter para fechar'
