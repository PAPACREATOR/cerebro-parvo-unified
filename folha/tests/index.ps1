param([Parameter(Mandatory=$true)][string]$TestDirectory)
$ErrorActionPreference = 'Stop'
$app = Split-Path $PSScriptRoot -Parent
. (Join-Path $app 'Submit-Folha.ps1')
$sqlite = Join-Path $app 'bin\sqlite3.exe'
$root = Join-Path $TestDirectory ([Guid]::NewGuid().ToString('N'))
$templates = Join-Path $root 'templates'; $library = Join-Path $root 'biblioteca'; $database = Join-Path $root 'index.sqlite3'
New-Item -ItemType Directory -Path $templates,$library -Force | Out-Null
Get-ChildItem -LiteralPath (Join-Path $app 'templates') -Filter *.yaml | Copy-Item -Destination $templates
$null = Sync-FolhaIndex $sqlite $database $templates $library
$route = Select-FolhaTemplate 'Quero converter este documento para PDF' $sqlite $database
if ($route.template -ne 'converter-pdf') { throw 'Natural Portuguese request was routed incorrectly.' }
try { $null = Select-FolhaTemplate 'não converter para PDF' $sqlite $database; throw 'Negative request accepted.' }
catch { if ($_.Exception.Message -eq 'Negative request accepted.') { throw } }

# Catalogue definitions, not a hardcoded switch, determine which workflows match.
$duplicate = Join-Path $templates 'outra-conversao.yaml'
Copy-Item -LiteralPath (Join-Path $templates 'converter-pdf.yaml') -Destination $duplicate
$null = Sync-FolhaIndex $sqlite $database $templates $library
$ambiguous = $false
try { $null = Select-FolhaTemplate 'converter para PDF' $sqlite $database }
catch { $ambiguous = $_.Exception.Message.Contains('mais de uma receita') }
if (-not $ambiguous) { throw 'Ambiguous catalogue did not stop selection.' }
Remove-Item -LiteralPath $duplicate
$null = Sync-FolhaIndex $sqlite $database $templates $library
if ((Select-FolhaTemplate 'converter para PDF' $sqlite $database).template -ne 'converter-pdf') { throw 'Removed catalogue entry remained active.' }

$fixture = Join-Path $library 'fonte.txt'
[IO.File]::WriteAllText($fixture,'Coração original e música.',[Text.UTF8Encoding]::new($false))
$null = Sync-FolhaIndex $sqlite $database $templates $library
if (@(Search-FolhaLibrary $sqlite $database 'coracao musica').Count -ne 1) { throw 'Accent-insensitive search failed.' }
try { $null = Sync-FolhaIndex $sqlite $database $templates (Join-Path $root 'missing'); throw 'Missing source directory accepted.' }
catch { if ($_.Exception.Message -eq 'Missing source directory accepted.') { throw } }
if (@(Search-FolhaLibrary $sqlite $database 'coracao').Count -ne 1) { throw 'An incomplete scan removed existing index rows.' }
$tooLong = (1..41 | ForEach-Object { 'palavra' + $_ }) -join ' '
try { $null = Search-FolhaLibrary $sqlite $database $tooLong; throw 'Search words were silently truncated.' }
catch { if ($_.Exception.Message -eq 'Search words were silently truncated.') { throw } }
$null = Invoke-FolhaSql $sqlite $database "INSERT INTO templates_fts(templates_fts) VALUES('integrity-check'); INSERT INTO biblioteca_fts(biblioteca_fts) VALUES('integrity-check');"
Write-Output 'PASS: template selection, ambiguity, catalogue removal, accents, failed-scan preservation and FTS5 integrity.'
