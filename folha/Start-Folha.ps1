param(
    [int]$Port = 8091,
    [string]$DataDirectory = (Join-Path $env:LOCALAPPDATA 'FolhaDagu'),
    [string]$DaguExe = (Join-Path $env:LOCALAPPDATA 'Programs\Dagu\dagu.exe'),
    [string]$DaguHome = (Join-Path $env:LOCALAPPDATA 'Dagu'),
    [string]$SqliteExe = (Join-Path $PSScriptRoot 'bin\sqlite3.exe'),
    [string]$LibraryDirectory = '',
    [switch]$OpenBrowser
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Submit-Folha.ps1')
if ($Port -lt 1024 -or $Port -gt 65535) { throw 'Porta inválida.' }
$DataDirectory = [IO.Path]::GetFullPath($DataDirectory)
$runs = Join-Path $DataDirectory 'runs'
New-Item -ItemType Directory -Path $DataDirectory,$runs -Force | Out-Null
if (-not $LibraryDirectory) { $LibraryDirectory = Join-Path $DataDirectory 'biblioteca' }
$LibraryDirectory = [IO.Path]::GetFullPath($LibraryDirectory)
New-Item -ItemType Directory -Path $LibraryDirectory,(Join-Path $LibraryDirectory 'wikis'),(Join-Path $LibraryDirectory 'regras'),(Join-Path $LibraryDirectory 'fontes') -Force | Out-Null
$null = Sync-FolhaIndex $SqliteExe (Join-Path $DataDirectory 'indice.sqlite3') (Join-Path $PSScriptRoot 'templates') $LibraryDirectory
$jobs = @{}
$session = [Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N')
$origin = 'http://127.0.0.1:' + $Port
$listener = [Net.HttpListener]::new()
$listener.Prefixes.Add($origin + '/')
$listener.Start()
# Preserve an interrupted request without ever launching it a second time.
foreach ($oldFile in Get-ChildItem -LiteralPath $runs -Filter state.json -Recurse -File) {
    $oldState = Get-Content -LiteralPath $oldFile.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($oldState.status -eq 'RUNNING') {
        $oldState.status = 'UNKNOWN'
        $oldState.message = 'A Folha reiniciou durante este trabalho. Consulta os registos antes de repetir.'
        Write-FolhaJson $oldFile.FullName $oldState
    }
}
[IO.File]::WriteAllText((Join-Path $DataDirectory 'launch-url.txt'), ($origin + '/#session=' + $session))
Write-FolhaJson (Join-Path $DataDirectory 'server.json') @{ pid = $PID; url = $origin; data_directory = $DataDirectory }
if ($OpenBrowser) { Start-Process ($origin + '/#session=' + $session) }
Write-Output ('Folha disponível em ' + $origin)

function Send-FolhaResponse {
    param($Context, [int]$Code, $Body, [string]$ContentType = 'application/json; charset=utf-8')
    $response = $Context.Response
    $response.StatusCode = $Code
    $response.ContentType = $ContentType
    $response.Headers['Cache-Control'] = 'no-store'
    $response.Headers['X-Content-Type-Options'] = 'nosniff'
    $response.Headers['Referrer-Policy'] = 'no-referrer'
    $response.Headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    if ($Body -is [byte[]]) { $bytes = $Body }
    elseif ($ContentType.StartsWith('application/json')) { $bytes = [Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject $Body -Depth 15 -Compress)) }
    else { $bytes = [Text.Encoding]::UTF8.GetBytes([string]$Body) }
    $response.ContentLength64 = $bytes.Length
    $response.OutputStream.Write($bytes,0,$bytes.Length)
    $response.Close()
}

try {
    $pending = $listener.GetContextAsync()
    while ($listener.IsListening) {
        foreach ($job in @($jobs.Values)) { Update-FolhaRun $job }
        if (-not $pending.Wait(100)) { continue }
        $context = $pending.Result
        $pending = $listener.GetContextAsync()
        try {
            $request = $context.Request
            $path = $request.Url.AbsolutePath
            if (-not [Net.IPAddress]::IsLoopback($request.RemoteEndPoint.Address) -or
                $request.Headers['Host'] -cne ('127.0.0.1:' + $Port) -or
                ($request.Headers['Origin'] -and $request.Headers['Origin'] -cne $origin)) {
                Send-FolhaResponse $context 403 @{ error = 'Abre a Folha pelo atalho local.' }; continue
            }
            if ($request.HttpMethod -eq 'GET' -and $path -in @('/','/app.js','/style.css')) {
                $file = switch ($path) { '/' {'index.html'} '/app.js' {'app.js'} '/style.css' {'style.css'} }
                $mime = switch ($path) { '/' {'text/html; charset=utf-8'} '/app.js' {'text/javascript; charset=utf-8'} '/style.css' {'text/css; charset=utf-8'} }
                Send-FolhaResponse $context 200 ([IO.File]::ReadAllBytes((Join-Path (Join-Path $PSScriptRoot 'ui') $file))) $mime
                continue
            }
            if ($request.HttpMethod -eq 'GET' -and $path -eq '/health') {
                Send-FolhaResponse $context 200 @{ status = 'ok'; service = 'FolhaDagu' }; continue
            }
            if ($request.Headers['X-Nexus-Session'] -cne $session) {
                Send-FolhaResponse $context 403 @{ error = 'Abre a Folha pelo atalho local para recuperar a sessão.' }; continue
            }
            $payload = $null
            if ($request.HttpMethod -eq 'POST') {
                if ($request.ContentLength64 -le 0 -or $request.ContentLength64 -gt 4000000 -or
                    $request.ContentType -notmatch '^application/json(?:;|$)' -or $request.Headers['Transfer-Encoding']) {
                    Send-FolhaResponse $context 400 @{ error = 'Pedido inválido ou demasiado grande.' }; continue
                }
                $reader = [IO.StreamReader]::new($request.InputStream,[Text.Encoding]::UTF8)
                try { $payload = $reader.ReadToEnd() | ConvertFrom-Json } finally { $reader.Dispose() }
            }
            if ($request.HttpMethod -eq 'POST' -and $path -eq '/api/run') {
                $active = @($jobs.Values | Where-Object { $_.State.status -eq 'RUNNING' })
                if ($active.Count -gt 0) { Send-FolhaResponse $context 409 @{ error = 'Aguarda a conclusão do trabalho em curso.' }; continue }
                $job = Start-FolhaRun $payload $DataDirectory $DaguExe $DaguHome (Join-Path $PSScriptRoot 'templates') $SqliteExe $LibraryDirectory
                $jobs[$job.State.id] = $job
                Send-FolhaResponse $context 202 @{ run_id = $job.State.id }
            } elseif ($request.HttpMethod -eq 'GET' -and $path -eq '/api/runs') {
                $items = @(Get-ChildItem -LiteralPath $runs -Filter state.json -Recurse -File | ForEach-Object { Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json } | Sort-Object created_at -Descending | Select-Object -First 100)
                Send-FolhaResponse $context 200 $items
            } elseif ($request.HttpMethod -eq 'GET' -and $path -match '^/api/(runs|pdf)/([a-f0-9]{32})$') {
                $kind = $Matches[1]; $id = $Matches[2]
                $directory = Join-Path $runs $id
                $stateFile = Join-Path $directory 'state.json'
                if (-not (Test-Path -LiteralPath $stateFile)) { Send-FolhaResponse $context 404 @{ error = 'Trabalho não encontrado.' }; continue }
                $state = Get-Content -LiteralPath $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json
                if ($kind -eq 'runs') { Send-FolhaResponse $context 200 $state }
                elseif ($state.status -eq 'DONE' -and $state.has_pdf) {
                    Send-FolhaResponse $context 200 ([IO.File]::ReadAllBytes((Join-Path $directory 'resultado.pdf'))) 'application/pdf'
                } else { Send-FolhaResponse $context 404 @{ error = 'Este trabalho não tem um PDF concluído.' } }
            } elseif ($request.HttpMethod -eq 'GET' -and $path -eq '/api/draft') {
                $draft = Join-Path $DataDirectory 'draft.json'
                $value = if (Test-Path -LiteralPath $draft) { Get-Content -LiteralPath $draft -Raw -Encoding UTF8 | ConvertFrom-Json } else { @{ text = ''; filename = ''; attachment = ''; revision = 0 } }
                Send-FolhaResponse $context 200 $value
            } elseif ($request.HttpMethod -eq 'POST' -and $path -eq '/api/draft') {
                $draft = Join-Path $DataDirectory 'draft.json'
                $old = if (Test-Path -LiteralPath $draft) { Get-Content -LiteralPath $draft -Raw -Encoding UTF8 | ConvertFrom-Json } else { @{ revision = 0 } }
                if ($payload.revision -ne $old.revision) { Send-FolhaResponse $context 409 @{ error = 'O rascunho mudou noutra janela. O texto visível foi conservado.' }; continue }
                if ($payload.text -isnot [string] -or $payload.text.Length -gt 100000 -or ([string]$payload.attachment).Length -gt 2796204) { throw 'Rascunho demasiado grande.' }
                $value = @{ text = $payload.text; filename = [string]$payload.filename; attachment = [string]$payload.attachment; revision = $old.revision + 1 }
                Write-FolhaJson $draft $value
                Send-FolhaResponse $context 200 @{ revision = $value.revision }
            } else { Send-FolhaResponse $context 404 @{ error = 'Operação não disponível.' } }
        } catch {
            try { Send-FolhaResponse $context 400 @{ error = $_.Exception.Message } } catch { $context.Response.Abort() }
        }
    }
} finally { $listener.Close() }
