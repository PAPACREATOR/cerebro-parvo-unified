Set-StrictMode -Version Latest

function ConvertTo-FolhaSqlText {
    param([AllowEmptyString()][string]$Value)
    # Hex literals keep document text out of SQL syntax and sqlite CLI dot commands.
    $hex = [BitConverter]::ToString([Text.Encoding]::UTF8.GetBytes($Value)).Replace('-','')
    return "CAST(X'$hex' AS TEXT)"
}

function Invoke-FolhaSql {
    param([string]$SqliteExe, [string]$Database, [string]$Sql)
    if (-not (Test-Path -LiteralPath $SqliteExe -PathType Leaf)) { throw 'O SQLite local não está disponível.' }
    $databasePath = [IO.Path]::GetFullPath($Database)
    if ($databasePath.Contains('"')) { throw 'Caminho de índice inválido.' }
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $SqliteExe
    $info.Arguments = '-batch -bail -json "' + $databasePath + '"'
    $info.UseShellExecute = $false; $info.CreateNoWindow = $true
    $info.RedirectStandardInput = $true; $info.RedirectStandardOutput = $true; $info.RedirectStandardError = $true
    $info.StandardOutputEncoding = [Text.Encoding]::UTF8
    $info.StandardErrorEncoding = [Text.Encoding]::UTF8
    $process = [Diagnostics.Process]::new(); $process.StartInfo = $info
    try {
        $null = $process.Start()
        $outTask = $process.StandardOutput.ReadToEndAsync()
        $errTask = $process.StandardError.ReadToEndAsync()
        $process.StandardInput.WriteLine(".timeout 5000`n" + $Sql)
        $process.StandardInput.Close()
        if (-not $process.WaitForExit(30000)) { $process.Kill(); throw 'O índice demorou demasiado tempo a responder.' }
        $output = $outTask.Result; $errorText = $errTask.Result
        if ($process.ExitCode -ne 0) { throw ('Falhou a pesquisa local: ' + $errorText.Trim()) }
        if ($output.Trim()) { return ($output | ConvertFrom-Json) }
    } finally { $process.Dispose() }
}

function Get-FolhaIndexFiles {
    param([string]$Root, [string[]]$Extensions)
    $rootItem = Get-Item -LiteralPath $Root -ErrorAction Stop
    if (-not $rootItem.PSIsContainer -or ($rootItem.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'A pasta indexada deve ser uma pasta local, sem redirecionamento.' }
    $pending = [Collections.Generic.Stack[string]]::new(); $pending.Push($rootItem.FullName)
    while ($pending.Count) {
        foreach ($item in Get-ChildItem -LiteralPath $pending.Pop() -ErrorAction Stop) {
            if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { continue }
            if ($item.PSIsContainer) { $pending.Push($item.FullName) }
            elseif ($item.Extension.ToLowerInvariant() -in $Extensions) { $item }
        }
    }
}

function Sync-FolhaIndex {
    param([string]$SqliteExe, [string]$Database, [string]$TemplateDirectory, [string]$LibraryDirectory)
    $schema = @'
CREATE VIRTUAL TABLE IF NOT EXISTS templates_fts USING fts5(
  relative_path UNINDEXED, title, keywords, body, sha256 UNINDEXED,
  pattern UNINDEXED, needs_attachment UNINDEXED, extensions UNINDEXED,
  tokenize='unicode61 remove_diacritics 2');
CREATE VIRTUAL TABLE IF NOT EXISTS biblioteca_fts USING fts5(
  relative_path UNINDEXED, title, body, sha256 UNINDEXED,
  tokenize='unicode61 remove_diacritics 2');
SELECT 'templates_fts' AS collection,relative_path,sha256 FROM templates_fts
UNION ALL SELECT 'biblioteca_fts',relative_path,sha256 FROM biblioteca_fts;
'@
    $previous = @{}
    foreach ($row in @(Invoke-FolhaSql $SqliteExe $Database $schema)) {
        $previous[$row.collection + '|' + $row.relative_path] = $row.sha256
    }
    $sql = [Text.StringBuilder]::new(); $null = $sql.AppendLine('BEGIN IMMEDIATE;')
    $strictUtf8 = [Text.UTF8Encoding]::new($false,$true)
    foreach ($collection in @('templates_fts','biblioteca_fts')) {
        $root = if ($collection -eq 'templates_fts') { $TemplateDirectory } else { $LibraryDirectory }
        $root = [IO.Path]::GetFullPath($root).TrimEnd('\')
        $extensions = if ($collection -eq 'templates_fts') { @('.yaml','.yml') } else { @('.md','.markdown','.txt') }
        $paths = [Collections.Generic.List[string]]::new()
        foreach ($file in @(Get-FolhaIndexFiles $root $extensions | Sort-Object FullName)) {
            if ($file.Length -gt 2097152) { throw ('O ficheiro excede o limite de indexação de 2 MB: ' + $file.Name) }
            $relative = $file.FullName.Substring($root.Length + 1).Replace('\','/')
            $pathSql = ConvertTo-FolhaSqlText $relative; $paths.Add($pathSql)
            $bytes = [IO.File]::ReadAllBytes($file.FullName)
            $sha = [Security.Cryptography.SHA256]::Create()
            try { $hash = [BitConverter]::ToString($sha.ComputeHash($bytes)).Replace('-','').ToLowerInvariant() } finally { $sha.Dispose() }
            if ($previous[$collection + '|' + $relative] -eq $hash) { continue }
            try { $body = $strictUtf8.GetString($bytes).TrimStart([char]0xFEFF) }
            catch { throw ('Guarda este ficheiro como texto UTF-8 antes de o indexar: ' + $file.Name) }
            $title = $file.BaseName; $keywords = ''; $pattern = ''; $requiresAttachment = 'false'; $allowed = ''
            if ($collection -eq 'templates_fts') {
                # These single-line YAML comments are catalogue metadata, not executable code.
                $metadata = @{}
                foreach ($match in [regex]::Matches($body,'(?m)^# nexus-([a-z]+):[ \t]*(.*)\r?$')) {
                    if ($metadata.ContainsKey($match.Groups[1].Value)) { throw ('Campo repetido no template: ' + $relative) }
                    $metadata[$match.Groups[1].Value] = $match.Groups[2].Value.Trim()
                }
                if ($metadata.ContainsKey('match')) {
                    foreach ($field in @('title','terms','attachment')) { if (-not $metadata.ContainsKey($field)) { throw ('Catálogo incompleto: ' + $relative) } }
                    $title = $metadata['title']; $keywords = $metadata['terms']; $pattern = $metadata['match']
                    $requiresAttachment = $metadata['attachment']; $allowed = [string]$metadata['extensions']
                    if ($relative -notmatch '^[a-z0-9][a-z0-9-]*\.yaml$' -or $requiresAttachment -notin @('true','false') -or -not $pattern.StartsWith('^') -or -not $pattern.EndsWith('$')) { throw ('Metadados inválidos: ' + $relative) }
                    $null = [regex]::new($pattern,[Text.RegularExpressions.RegexOptions]::IgnoreCase,[TimeSpan]::FromMilliseconds(200))
                }
            } else {
                $firstLine = @($body -split '\r?\n' | Where-Object { $_.Trim() } | Select-Object -First 1)
                if ($firstLine.Count) { $title = ($firstLine[0] -replace '^#+\s*','').Trim(); if ($title.Length -gt 120) { $title = $title.Substring(0,120) } }
            }
            $null = $sql.AppendLine("DELETE FROM $collection WHERE relative_path=$pathSql;")
            $values = @($relative,$title,$body,$hash)
            if ($collection -eq 'templates_fts') { $values = @($relative,$title,$keywords,$body,$hash,$pattern,$requiresAttachment,$allowed) }
            $encoded = @($values | ForEach-Object { ConvertTo-FolhaSqlText ([string]$_) }) -join ','
            $null = $sql.AppendLine("INSERT INTO $collection VALUES($encoded);")
        }
        # Index reconciliation only deletes index rows, never source files.
        if ($paths.Count) { $null = $sql.AppendLine("DELETE FROM $collection WHERE relative_path NOT IN (" + ($paths -join ',') + ');') }
        else { $null = $sql.AppendLine("DELETE FROM $collection;") }
    }
    $null = $sql.AppendLine('COMMIT; SELECT (SELECT count(*) FROM templates_fts) AS templates, (SELECT count(*) FROM biblioteca_fts) AS documents;')
    return (Invoke-FolhaSql $SqliteExe $Database $sql.ToString())
}

function Get-FolhaFtsQuery {
    param([string]$Text, [switch]$Any)
    $tokens = @([regex]::Matches($Text,'[\p{L}\p{N}]+') | ForEach-Object { $_.Value.ToLowerInvariant() } | Select-Object -Unique)
    if ($Any) { $tokens = @($tokens | Select-Object -First 40) }
    elseif ($tokens.Count -gt 40) { throw 'A pesquisa aceita até 40 palavras diferentes. Especifica um tema mais preciso; nenhuma fonte foi cortada.' }
    if (-not $tokens.Count) { return '' }
    $joiner = if ($Any) { ' OR ' } else { ' AND ' }
    return (@($tokens | ForEach-Object { '"' + $_ + '"' }) -join $joiner)
}

function Search-FolhaLibrary {
    param([string]$SqliteExe, [string]$Database, [string]$Query)
    $fts = Get-FolhaFtsQuery $Query
    if (-not $fts) { throw 'Indica as palavras que queres procurar na biblioteca.' }
    $querySql = ConvertTo-FolhaSqlText $fts
    return (Invoke-FolhaSql $SqliteExe $Database "SELECT relative_path,title,body,sha256 FROM biblioteca_fts WHERE biblioteca_fts MATCH $querySql ORDER BY rank,relative_path LIMIT 20;")
}

function Publish-FolhaWiki {
    param($Request)
    if ([string]$Request.run_id -notmatch '^[a-f0-9]{32}$') { throw 'Identificador de trabalho inválido.' }
    $content = [IO.File]::ReadAllText((Join-Path (Get-Location).Path 'content.md'),[Text.Encoding]::UTF8)
    $destination = Join-Path (Join-Path $Request.library_directory 'wikis') ($Request.run_id + '.md')
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $contentHash = [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($content))).Replace('-','').ToLowerInvariant()
        $inputHash = [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes([string]$Request.text))).Replace('-','').ToLowerInvariant()
    } finally { $sha.Dispose() }
    $trace = @{
        run_id = $Request.run_id; process_id = $Request.process_id; template_sha256 = $Request.template_sha256
        created_at = $Request.created_at; saved_at = [DateTime]::UtcNow.ToString('o')
        authority = 'candidate'; human_approval = $false; content_sha256 = $contentHash; input_sha256 = $inputHash
        run_directory = (Get-Location).Path; source = 'request.json'; result = 'content.md'
    } | ConvertTo-Json -Depth 10
    # Completion of a tool never promotes a result to Canonical.
    [IO.File]::WriteAllText(($destination + '.provenance.json'),$trace,[Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText($destination,$content,[Text.UTF8Encoding]::new($false))
    $sourcesFile = Join-Path (Get-Location).Path 'sources.json'
    if (Test-Path -LiteralPath $sourcesFile) {
        $sources = Get-Content -LiteralPath $sourcesFile -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($source in $sources) {
            if ($source.file -notmatch '^fonte-[0-9]{2,4}\.txt$') { throw 'Referência de fonte inválida.' }
            $sourcePath = Join-Path (Get-Location).Path $source.file
            $libraryPath = Join-Path (Join-Path $Request.library_directory 'fontes') ($Request.run_id + '-' + $source.file)
            [IO.File]::WriteAllBytes($libraryPath,[IO.File]::ReadAllBytes($sourcePath))
            [IO.File]::WriteAllText(($libraryPath + '.provenance.json'),($source | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
        }
    }
}
