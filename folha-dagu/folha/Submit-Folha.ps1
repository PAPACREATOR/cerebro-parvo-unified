Set-StrictMode -Version Latest

. (Join-Path $PSScriptRoot 'Index-Folha.ps1')

function Write-FolhaJson {
    param([string]$Path, $Value)
    $temporary = $Path + '.' + [Guid]::NewGuid().ToString('N') + '.tmp'
    [IO.File]::WriteAllText($temporary, (ConvertTo-Json -InputObject $Value -Depth 15), [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temporary -Destination $Path -Force
}

function Select-FolhaTemplate {
    param([string]$Text, [string]$SqliteExe, [string]$Database)
    if ([string]::IsNullOrWhiteSpace($Text) -or $Text.Length -gt 100000) { throw 'Escreve um pedido até 100000 caracteres.' }
    $lookup = if ($Text -match '^\s*@@') { 'guardar texto' } else { $Text }
    $fts = Get-FolhaFtsQuery $lookup -Any
    if (-not $fts) { throw 'Escreve o que queres fazer.' }
    $query = ConvertTo-FolhaSqlText ('{title keywords} : (' + $fts + ')')
    $candidates = @(Invoke-FolhaSql $SqliteExe $Database "SELECT * FROM templates_fts WHERE templates_fts MATCH $query ORDER BY relative_path;")
    $matches = @()
    foreach ($candidate in $candidates) {
        if (-not $candidate.pattern) { continue }
        $regex = [regex]::new($candidate.pattern,[Text.RegularExpressions.RegexOptions]::IgnoreCase,[TimeSpan]::FromMilliseconds(200))
        $match = $regex.Match($Text)
        if ($match.Success) {
            $matches += @{
                template = [IO.Path]::GetFileNameWithoutExtension($candidate.relative_path)
                title = $candidate.title; attachment = $candidate.needs_attachment -eq 'true'
                body = $match.Groups['body'].Value; extensions = $candidate.extensions
                yaml = $candidate.body; sha256 = $candidate.sha256
            }
        }
    }
    if ($matches.Count -eq 1) { return $matches[0] }
    if ($matches.Count -gt 1) { throw 'O pedido corresponde a mais de uma receita. Indica uma operação de cada vez.' }
    throw 'Ainda não há uma receita para esse pedido. Podes converter para PDF, verificar integridade de ficheiro, guardar texto: seguido do texto, ou procurar na biblioteca: seguido do tema.'
}

function Start-FolhaRun {
    param($Payload, [string]$DataDirectory, [string]$DaguExe, [string]$DaguHome, [string]$TemplateDirectory, [string]$SqliteExe, [string]$LibraryDirectory)
    if ($Payload.text -isnot [string]) { throw 'O pedido deve ser texto.' }
    $database = Join-Path $DataDirectory 'indice.sqlite3'
    $null = Sync-FolhaIndex $SqliteExe $database $TemplateDirectory $LibraryDirectory
    $route = Select-FolhaTemplate $Payload.text $SqliteExe $database
    $filename = [string]$Payload.filename
    $attachment = [string]$Payload.attachment
    if ($filename.Length -gt 255 -or $filename -match '[\\/:\x00-\x1f]') { throw 'O nome do anexo não é válido.' }
    if ($attachment.Length -gt 2796204) { throw 'Escolhe um ficheiro até 2 MB.' }
    if ($route.attachment -and [string]::IsNullOrWhiteSpace($filename)) { throw 'Junta o ficheiro a este pedido.' }
    if (-not $route.attachment -and ($filename -or $attachment)) { throw 'Esta receita recebe apenas texto. Retira o anexo para continuar.' }
    $bytes = [Convert]::FromBase64String($attachment)
    if ($bytes.Length -gt 2097152) { throw 'Escolhe um ficheiro até 2 MB.' }
    $extension = [IO.Path]::GetExtension($filename).ToLowerInvariant()
    if ($route.extensions -and $extension -notin ($route.extensions -split ',')) { throw ('Este ficheiro não é aceite pela receita. Formatos: ' + $route.extensions) }
    if (-not (Test-Path -LiteralPath $DaguExe -PathType Leaf)) { throw 'O Dagu não está disponível.' }
    if ($route.template -eq 'converter-pdf' -and -not (Test-Path -LiteralPath 'C:\Program Files\LibreOffice\program\soffice.com')) { throw 'O LibreOffice não está instalado.' }
    $id = [Guid]::NewGuid().ToString('N')
    $directory = Join-Path (Join-Path $DataDirectory 'runs') $id
    New-Item -ItemType Directory -Path $directory | Out-Null
    $inputFile = Join-Path $directory ('entrada' + $extension)
    if ($route.attachment) { [IO.File]::WriteAllBytes($inputFile, $bytes) }
    $scripts = @{}
    foreach ($name in @('Index-Folha.ps1','Tools-Folha.ps1')) {
        $copy = Join-Path $directory $name
        Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination $copy
        $scripts[$name] = (Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $toolsFile = Join-Path $directory 'ferramentas.json'
    $toolsConfig = Join-Path $DataDirectory 'ferramentas.json'
    if (Test-Path -LiteralPath $toolsConfig -PathType Leaf) { Copy-Item -LiteralPath $toolsConfig -Destination $toolsFile }
    Write-FolhaJson (Join-Path $directory 'request.json') @{
        text = $Payload.text; filename = $filename; input_file = $inputFile; body = $route.body
        run_id = $id; template_sha256 = $route.sha256; library_directory = $LibraryDirectory
        process_id = $route.template; created_at = [DateTime]::UtcNow.ToString('o')
        tools_file = $toolsFile; tools_script = (Join-Path $directory 'Tools-Folha.ps1'); script_sha256 = $scripts
        database_file = $database; sqlite_exe = $SqliteExe; index_script = (Join-Path $directory 'Index-Folha.ps1')
    }
    # Only generated paths and IDs enter the YAML. Human text stays in JSON data.
    $yaml = $route.yaml.Replace('__WORK_DIR_JSON__', (ConvertTo-Json -InputObject $directory -Compress))
    $workflow = Join-Path $directory ('folha-' + $id + '.yaml')
    [IO.File]::WriteAllText($workflow, $yaml, [Text.UTF8Encoding]::new($false))
    # Windows PowerShell 5 treats native stderr warnings as ErrorRecords.
    # The process exit code, not the output stream, determines validation.
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $validation = & $DaguExe validate --dagu-home $DaguHome $workflow 2>&1
        $validationExit = $LASTEXITCODE
    } finally { $ErrorActionPreference = $previousPreference }
    if ($validationExit -ne 0) { throw ('O template não passou a validação do Dagu: ' + ($validation -join ' ')) }
    $state = @{
        id = $id; run_id = $id; title = $route.title; process_id = $route.template
        status = 'RUNNING'; created_at = [DateTime]::UtcNow.ToString('o'); filename = $filename
        message = 'A executar o pedido.'; content = ''; has_pdf = $false
    }
    Write-FolhaJson (Join-Path $directory 'state.json') $state
    try {
        $process = Start-Process -FilePath $DaguExe -ArgumentList @('start','--dagu-home',('"' + $DaguHome + '"'),'--run-id',$id,('"' + $workflow + '"')) -WorkingDirectory $directory -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $directory 'dagu.stdout.log') -RedirectStandardError (Join-Path $directory 'dagu.stderr.log')
        $null = $process.Handle
        return @{ State = $state; Process = $process; Directory = $directory }
    } catch {
        $state.status = 'FAIL'; $state.message = 'Não foi possível iniciar o Dagu.'
        Write-FolhaJson (Join-Path $directory 'state.json') $state
        throw
    }
}

function Update-FolhaRun {
    param($Job)
    if ($Job.State.status -ne 'RUNNING') { return }
    $Job.Process.Refresh()
    if (-not $Job.Process.HasExited) {
        $progress = Join-Path $Job.Directory 'progress.json'
        if (Test-Path -LiteralPath $progress) {
            try {
                $message = (Get-Content -LiteralPath $progress -Raw -Encoding UTF8 | ConvertFrom-Json).message
                if ($message -is [string] -and $message -cne $Job.State.message) {
                    $Job.State.message = $message
                    Write-FolhaJson (Join-Path $Job.Directory 'state.json') $Job.State
                }
            } catch { } # A concurrently written progress message is retried on the next poll.
        }
        return
    }
    $Job.Process.WaitForExit()
    $contentPath = Join-Path $Job.Directory 'content.md'
    if ($Job.Process.ExitCode -eq 0 -and (Test-Path -LiteralPath $contentPath)) {
        try {
            $manifest = Join-Path $Job.Directory 'artifacts.json'
            if (Test-Path -LiteralPath $manifest) {
                $artifacts = Get-Content -LiteralPath $manifest -Raw -Encoding UTF8 | ConvertFrom-Json
                foreach ($artifact in $artifacts) {
                    if ($artifact.name -notmatch '^resultado\.(mp3|wav|mp4|png|odt|docx)$') { throw 'O resultado anunciado tem um nome inválido.' }
                    $artifactFile = Get-Item -LiteralPath (Join-Path $Job.Directory $artifact.name) -ErrorAction Stop
                    if ($artifactFile.PSIsContainer -or ($artifactFile.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $artifactFile.Length -le 0) { throw 'O resultado anunciado não é um ficheiro regular com conteúdo.' }
                    if ($artifact.sha256 -notmatch '^[a-fA-F0-9]{64}$' -or (Get-FileHash -LiteralPath $artifactFile.FullName -Algorithm SHA256).Hash -ine $artifact.sha256) { throw 'O resultado não corresponde à verificação de integridade.' }
                }
                $Job.State.artifacts = @($artifacts)
            }
            $Job.State.content = [IO.File]::ReadAllText($contentPath, [Text.Encoding]::UTF8)
            $Job.State.has_pdf = Test-Path -LiteralPath (Join-Path $Job.Directory 'resultado.pdf')
            $Job.State.status = 'DONE'
            $Job.State.message = 'Trabalho concluído.'
        } catch {
            $Job.State.status = 'FAIL'
            $Job.State.message = 'A entrega não passou a verificação. Os ficheiros e registos foram conservados.'
            $Job.State.content = $_.Exception.Message
            $Job.State.artifacts = @()
        }
    } else {
        $Job.State.status = 'FAIL'
        $Job.State.message = 'O workflow não terminou com sucesso. O pedido e os registos foram conservados.'
        $log = Join-Path $Job.Directory 'dagu.stderr.log'
        if (Test-Path -LiteralPath $log) {
            $Job.State.content = (Get-Content -LiteralPath $log -Encoding UTF8 -Tail 12) -join "`n"
        }
    }
    $Job.State.finished_at = [DateTime]::UtcNow.ToString('o')
    Write-FolhaJson (Join-Path $Job.Directory 'state.json') $Job.State
}
