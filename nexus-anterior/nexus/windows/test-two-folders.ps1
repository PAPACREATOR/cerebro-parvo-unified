# Native NTFS + standard Windows identity. No policy changes or saved password.
$ErrorActionPreference = 'Stop'
$root = 'C:\ProgramData\NexusMinimal'
$password = $null
try {
    $user = Get-LocalUser Nexus
    $area = Join-Path $root ('two-folders-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $area | Out-Null
    $owner = [Security.Principal.WindowsIdentity]::GetCurrent().User
    foreach ($name in @('allowed','protected')) {
        $path = Join-Path $area $name
        New-Item -ItemType Directory -Path $path | Out-Null
        $acl = [Security.AccessControl.DirectorySecurity]::new()
        $acl.SetAccessRuleProtection($true,$false)
        $acl.SetOwner($owner)
        foreach ($sid in @($owner,[Security.Principal.SecurityIdentifier]::new('S-1-5-18'),[Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))) {
            $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow'))
        }
        if ($name -eq 'allowed') { $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($user.SID,'Modify','ContainerInherit,ObjectInherit','None','Allow')) }
        Set-Acl -LiteralPath $path -AclObject $acl
    }
    [IO.File]::WriteAllText("$area\protected\sentinel.txt",'synthetic')
    # WorkingDirectory keeps the credentialed command below the 1024-character API limit.
    $child = '$ErrorActionPreference=''Stop'';$r=@{sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value};[IO.File]::WriteAllText(''allowed\output.txt'',''ok'');foreach($op in ''read'',''write''){try{if($op -eq ''read''){[IO.File]::ReadAllText(''protected\sentinel.txt'')|Out-Null}else{[IO.File]::WriteAllText(''protected\sentinel.txt'',''changed'')};$r[$op]=''ALLOWED''}catch{$r[$op]=$_.Exception.InnerException.GetType().Name}};$r|ConvertTo-Json|Set-Content ''allowed\result.json'''
    # .NET relative file paths use process cwd; set it explicitly in the short command.
    $child = '[Environment]::CurrentDirectory=(Get-Location).Path;' + $child
    $exe = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
    $arguments = '-NoProfile -NonInteractive -Command "' + $child + '"'
    if (($exe.Length + $arguments.Length + 4) -ge 1024) { throw 'Command exceeds native credential API limit.' }
    Write-Host 'Teste corrigido: duas pastas artificiais; conta Nexus existente.'
    Write-Host 'A palavra-passe nao fica guardada. Nenhuma politica Windows sera alterada.'
    $password = Read-Host 'Palavra-passe da conta Nexus' -AsSecureString
    $credential = [Management.Automation.PSCredential]::new("$env:COMPUTERNAME\Nexus",$password)
    $process = Start-Process -FilePath $exe -ArgumentList $arguments -Credential $credential -WorkingDirectory $area -WindowStyle Hidden -PassThru
    if (-not $process.WaitForExit(30000)) { Stop-Process -Id $process.Id -Force; throw 'Timeout.' }
    $probe = Get-Content -LiteralPath "$area\allowed\result.json" -Raw | ConvertFrom-Json
    $allowed = (Get-Content -LiteralPath "$area\allowed\output.txt" -Raw) -eq 'ok'
    $unchanged = [IO.File]::ReadAllText("$area\protected\sentinel.txt") -eq 'synthetic'
    $passed = $probe.sid -eq $user.SID.Value -and $allowed -and $unchanged -and $probe.read -eq 'UnauthorizedAccessException' -and $probe.write -eq 'UnauthorizedAccessException'
    $report = [ordered]@{status=$(if($passed){'PASS'}else{'FAIL'});identity_verified=($probe.sid -eq $user.SID.Value);allowed_write=$allowed;protected_read=$probe.read;protected_write=$probe.write;original_unchanged=$unchanged;command_length=($exe.Length+$arguments.Length+4);test_area=$area;timestamp=(Get-Date).ToUniversalTime().ToString('o')}
    $report | ConvertTo-Json | Set-Content -LiteralPath "$root\evidence\two-folders-result.json" -Encoding UTF8
    $report | ConvertTo-Json | Write-Host
} catch {
    @{status='FAIL';message=$_.Exception.Message;line=$_.InvocationInfo.ScriptLineNumber;timestamp=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath "$root\evidence\two-folders-error.json" -Encoding UTF8
    Write-Host 'Falha registada no diagnostico.'
} finally {
    if ($null -ne $password) { $password.Dispose() }
}
Read-Host 'Carrega Enter para fechar'
