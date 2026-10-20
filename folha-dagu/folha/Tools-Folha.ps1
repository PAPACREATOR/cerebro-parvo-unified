Set-StrictMode -Version Latest
Add-Type -AssemblyName System.Net.Http

function Write-FolhaStep {
    param([string]$Message)
    $value = @{ message = $Message; updated_at = [DateTime]::UtcNow.ToString('o') } | ConvertTo-Json -Compress
    [IO.File]::WriteAllText((Join-Path (Get-Location).Path 'progress.json'),$value,[Text.UTF8Encoding]::new($false))
}

function Invoke-FolhaLocalApi {
    param([string]$BaseUrl, [string]$Path, [string]$Method = 'GET', $Body = $null, [string]$Password = '', [int]$WaitSeconds = 60, [string]$OutputFile = '')
    $uri = [Uri]($BaseUrl.TrimEnd('/') + $Path)
    if ($uri.Scheme -ne 'http' -or $uri.Host -ne '127.0.0.1' -or $uri.UserInfo -or $uri.Fragment) { throw 'A ferramenta deve usar o endereço local configurado.' }
    $handler = [Net.Http.HttpClientHandler]::new(); $handler.AllowAutoRedirect = $false; $handler.UseProxy = $false
    $client = [Net.Http.HttpClient]::new($handler)
    $client.Timeout = if ($WaitSeconds -eq 0) { [Threading.Timeout]::InfiniteTimeSpan } else { [TimeSpan]::FromSeconds($WaitSeconds) }
    $request = [Net.Http.HttpRequestMessage]::new([Net.Http.HttpMethod]::new($Method),$uri)
    if ($Password) { $request.Headers.Authorization = [Net.Http.Headers.AuthenticationHeaderValue]::new('Bearer',$Password) }
    if ($null -ne $Body) { $request.Content = [Net.Http.StringContent]::new((ConvertTo-Json -InputObject $Body -Depth 30 -Compress),[Text.Encoding]::UTF8,'application/json') }
    try {
        $response = $client.SendAsync($request).GetAwaiter().GetResult()
        try {
            if (-not $response.IsSuccessStatusCode) { throw ('A ferramenta local devolveu HTTP ' + [int]$response.StatusCode + ' em ' + $Path + '. Os dados foram conservados.') }
            if ($OutputFile) {
                if ($OutputFile -notmatch '^resultado\.(mp3|wav|mp4|png|odt|docx)$') { throw 'Nome de resultado inválido.' }
                $bytes = $response.Content.ReadAsByteArrayAsync().GetAwaiter().GetResult()
                [IO.File]::WriteAllBytes((Join-Path (Get-Location).Path $OutputFile),$bytes)
                return @{file=$OutputFile;bytes=$bytes.Length}
            }
            $text = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
            if ($text.Trim()) { return ($text | ConvertFrom-Json) }
        } finally { $response.Dispose() }
    } finally { $request.Dispose(); $client.Dispose() }
}

function Get-FolhaNotebookConfig {
    param($Request)
    if (-not (Test-Path -LiteralPath $Request.tools_file -PathType Leaf)) { throw 'A ligação às ferramentas locais ainda não está configurada.' }
    $config = Get-Content -LiteralPath $Request.tools_file -Raw -Encoding UTF8 | ConvertFrom-Json
    $credentials = Get-Content -LiteralPath $config.notebook.credential_file -Raw -Encoding UTF8 | ConvertFrom-Json
    return @{ api = [string]$config.notebook.api; password = [string]$credentials.password; model_name = [string]$config.notebook.model_name; model_api = [string]$config.notebook.model_api }
}

function Invoke-FolhaNotebook {
    param($Request, [string]$Instructions, [string]$InputText, [string]$Name)
    if ($Name -notmatch '^[a-z][a-z0-9-]{0,60}$' -or -not $InputText.Trim() -or -not $Instructions.Trim()) { throw 'Microprocesso de texto inválido.' }
    $config = Get-FolhaNotebookConfig $Request
    $models = @(Invoke-FolhaLocalApi $config.api '/api/models' -Password $config.password)
    $model = @($models | Where-Object { $_.type -eq 'language' -and $_.name -ceq $config.model_name })
    if ($model.Count -ne 1) { throw 'O modelo de linguagem configurado não foi encontrado de forma inequívoca no Open Notebook.' }
    # Count the complete source and instructions with the installed model's own tokenizer.
    # Reserve capacity for Open Notebook's fixed prompt and the answer; never trim a source.
    $props = Invoke-FolhaLocalApi $config.model_api '/props'
    $capacity = [int]$props.default_generation_settings.n_ctx
    $tokens = Invoke-FolhaLocalApi $config.model_api '/tokenize' 'POST' @{ content = ($Instructions + "`n" + $InputText); add_special = $true }
    if ($capacity -le 3072 -or @($tokens.tokens).Count -gt ($capacity - 3072)) { throw 'O texto completo excede a capacidade deste microprocesso. O original foi conservado; é necessário um percurso por secções.' }
    $sha = [Security.Cryptography.SHA256]::Create()
    try { $hash = [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($Instructions))).Replace('-','').ToLowerInvariant() } finally { $sha.Dispose() }
    $nameInNotebook = 'nexus-dagu-' + $Name + '-' + $hash.Substring(0,16)
    $all = @(Invoke-FolhaLocalApi $config.api '/api/transformations' -Password $config.password)
    $matching = @($all | Where-Object { $_.name -ceq $nameInNotebook })
    if ($matching.Count -gt 1) { throw 'Existe mais de uma receita com o mesmo nome no Open Notebook.' }
    if ($matching.Count -eq 1) {
        $transformation = $matching[0]
        if ($transformation.prompt -cne $Instructions) { throw 'A receita do Open Notebook foi alterada. É necessário reconciliar a sua versão.' }
    } else {
        $transformation = Invoke-FolhaLocalApi $config.api '/api/transformations' 'POST' @{ name = $nameInNotebook; title = ('Nexus: ' + $Name); description = ('Receita YAML ' + $Request.template_sha256); prompt = $Instructions; apply_default = $false; model_id = $model[0].id } -Password $config.password
    }
    $evidence = @{ tool = 'Open Notebook'; operation = 'transformation'; model_id = $model[0].id; model_name = $model[0].name; transformation_id = $transformation.id; prompt_sha256 = $hash; input_tokens = @($tokens.tokens).Count; context_capacity = $capacity; authority = 'candidate'; started_at = [DateTime]::UtcNow.ToString('o') }
    [IO.File]::WriteAllText((Join-Path (Get-Location).Path ($Name + '-input.txt')),$InputText,[Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText((Join-Path (Get-Location).Path ($Name + '-prompt.txt')),$Instructions,[Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText((Join-Path (Get-Location).Path ($Name + '-tool.json')),($evidence | ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
    # A generation is submitted once. Its actual completion determines duration.
    $response = Invoke-FolhaLocalApi $config.api '/api/transformations/execute' 'POST' @{ transformation_id = $transformation.id; model_id = $model[0].id; input_text = $InputText } -Password $config.password -WaitSeconds 0
    if ($response.output -isnot [string] -or -not $response.output.Trim()) { throw 'O Open Notebook não devolveu texto utilizável.' }
    [IO.File]::WriteAllText((Join-Path (Get-Location).Path ($Name + '-response.json')),($response | ConvertTo-Json -Depth 15),[Text.UTF8Encoding]::new($false))
    return [string]$response.output
}

function Write-FolhaData {
    param([string]$Name, $Value)
    [IO.File]::WriteAllText((Join-Path (Get-Location).Path $Name),(ConvertTo-Json -InputObject $Value -Depth 30),[Text.UTF8Encoding]::new($false))
}

function Split-FolhaNotebookInput {
    param($Request, [string]$Instructions, [string]$Text)
    $config = Get-FolhaNotebookConfig $Request
    $props = Invoke-FolhaLocalApi $config.model_api '/props'
    $budget = [int]$props.default_generation_settings.n_ctx - 3584
    if ($budget -le 0) { throw 'Capacidade insuficiente no modelo local.' }
    $pending = [Collections.Generic.Stack[string]]::new(); $pending.Push($Text)
    $sections = [Collections.Generic.List[string]]::new()
    while ($pending.Count) {
        $part = $pending.Pop()
        $tokens = Invoke-FolhaLocalApi $config.model_api '/tokenize' 'POST' @{ content = ($Instructions + "`n" + $part); add_special = $true }
        if (@($tokens.tokens).Count -le $budget) { $sections.Add($part); continue }
        if ($part.Length -lt 100) { throw 'As instruções excedem a capacidade do modelo.' }
        $middle = [int]($part.Length / 2)
        $boundary = $part.LastIndexOf("`n",$middle)
        if ($boundary -lt [int]($middle / 2)) { $boundary = $part.LastIndexOf(' ',$middle) }
        if ($boundary -lt 1) { $boundary = $middle }
        else { $boundary++ }
        if ([char]::IsLowSurrogate($part[$boundary])) { $boundary-- }
        $pending.Push($part.Substring($boundary)); $pending.Push($part.Substring(0,$boundary))
    }
    if (($sections -join '') -cne $Text) { throw 'A divisão do texto não conservou o original.' }
    return $sections.ToArray()
}

function Get-FolhaResearchSources {
    param($Request)
    $topic = [string]$Request.body
    if ($topic.Length -gt 400) { throw 'Indica um tema de pesquisa até 400 caracteres.' }
    Write-FolhaStep 'A pesquisar o tema na Wikipédia e no motor de busca.'
    $query = [Uri]::EscapeDataString($topic)
    $webHeaders = @{'User-Agent'='NexusLocal/1.0 (personal research)'}
    $wikiSearch = Invoke-RestMethod -Uri ('https://pt.wikipedia.org/w/api.php?action=query&list=search&srlimit=5&format=json&utf8=1&srsearch=' + $query) -Headers $webHeaders -TimeoutSec 60
    Write-FolhaData 'wikipedia-search.json' $wikiSearch
    $wikiHits = @($wikiSearch.query.search)
    if (-not $wikiHits.Count) { throw 'A Wikipédia não encontrou este tema. Os registos de pesquisa foram conservados.' }
    $terms = @([regex]::Matches($topic.ToLowerInvariant(),'[\p{L}\p{N}]+') | ForEach-Object {$_.Value} | Where-Object {$_ -notin @('o','a','os','as','de','da','do','das','dos','em','e','um','uma','sobre')} | Select-Object -Unique)
    $ranked = @($wikiHits | ForEach-Object {
        $hit = $_; $score = 0
        foreach ($term in $terms) { if ($hit.title.ToLowerInvariant() -match ('\b'+[regex]::Escape($term)+'\b')) {$score++} }
        [pscustomobject]@{pageid=$hit.pageid;title=$hit.title;score=$score}
    } | Sort-Object score -Descending)
    $pageId = [long]$ranked[0].pageid
    Write-FolhaData 'wikipedia-selection.json' @{topic=$topic;selected=$ranked[0];candidates=$ranked;rule='title word coverage; result remains a candidate'}
    $wiki = Invoke-RestMethod -Uri ('https://pt.wikipedia.org/w/api.php?action=query&prop=extracts|info&inprop=url&explaintext=1&format=json&utf8=1&pageids=' + $pageId) -Headers $webHeaders -TimeoutSec 60
    $page = @($wiki.query.pages.PSObject.Properties.Value)[0]
    if (-not $page.extract) { throw 'A Wikipédia não devolveu o artigo completo em texto.' }
    $wikiText = [string]$page.extract
    [IO.File]::WriteAllText((Join-Path (Get-Location).Path 'fonte-01.txt'),$wikiText,[Text.UTF8Encoding]::new($false))
    $sources = [Collections.Generic.List[object]]::new()
    $sources.Add(@{ title=[string]$page.title; url=[string]$page.fullurl; file='fonte-01.txt'; kind='encyclopedia'; retrieved_at=[DateTime]::UtcNow.ToString('o'); status='retrieved' })
    $search = Invoke-WebRequest -UseBasicParsing -Uri ('https://html.duckduckgo.com/html/?q='+$query) -Headers $webHeaders -TimeoutSec 60
    [IO.File]::WriteAllText((Join-Path (Get-Location).Path 'search.html'),$search.Content,[Text.UTF8Encoding]::new($false))
    if ($search.Content -match 'challenge-form|anomaly\.js') { throw 'O motor de pesquisa pediu uma verificação humana. A pesquisa não foi apresentada como concluída.' }
    $entries = [Collections.Generic.List[object]]::new()
    foreach ($link in $search.Links) {
        if ($link.outerHTML -notmatch 'class="result__a"') { continue }
        $href = [Net.WebUtility]::HtmlDecode([string]$link.href)
        $target = [regex]::Match($href,'[?&]uddg=([^&]+)')
        $sourceUrl = if ($target.Success) { [Uri]::UnescapeDataString($target.Groups[1].Value) } else { $href }
        $title = [Net.WebUtility]::HtmlDecode(([regex]::Replace($link.outerHTML,'<[^>]+>','')))
        $entries.Add(@{link=$sourceUrl;title=$title})
    }
    Write-FolhaData 'search-results.json' $entries.ToArray()
    $config = Get-FolhaNotebookConfig $Request
    $notebook = Invoke-FolhaLocalApi $config.api '/api/notebooks' 'POST' @{name=('Nexus pesquisa '+$Request.run_id);description=('Tema: '+$topic)} -Password $config.password
    Write-FolhaData 'notebook.json' @{id=$notebook.id; topic=$topic}
    $seenHosts = @{}
    foreach ($entry in $entries) {
        if ($sources.Count -ge 3) { break }
        $url = [Uri]([string]$entry.link)
        if ($url.Scheme -ne 'https' -or $url.UserInfo -or $url.Host -match '(^|\.)wikipedia\.org$' -or $seenHosts.ContainsKey($url.Host)) { continue }
        # A search result cannot redirect the local extractor towards private services.
        try { $addresses = @([Net.Dns]::GetHostAddresses($url.Host)) } catch { continue }
        if (-not $addresses.Count) { continue }
        $private = @($addresses | Where-Object {
            $address = if ($_.IsIPv4MappedToIPv6) { $_.MapToIPv4() } else { $_ }
            [Net.IPAddress]::IsLoopback($address) -or $address.IsIPv6LinkLocal -or $address.IsIPv6SiteLocal -or $address.IsIPv6Multicast -or
            $address.IPAddressToString -match '^(::|f[cd][0-9a-f]{2}:|0\.|10\.|127\.|169\.254\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|100\.(6[4-9]|[7-9][0-9]|1[01][0-9]|12[0-7])\.)'
        })
        if ($private.Count) { continue }
        $seenHosts[$url.Host] = $true
        $number = $sources.Count + 1
        Write-FolhaStep ('A recolher a fonte '+$number+': '+$url.Host+'.')
        $source = Invoke-FolhaLocalApi $config.api '/api/sources/json' 'POST' @{type='link';url=$url.AbsoluteUri;title=[string]$entry.title;notebooks=@($notebook.id);transformations=@();embed=$false;delete_source=$false;async_processing=$true} -Password $config.password
        Write-FolhaData ('fonte-'+$number.ToString('00')+'-job.json') $source
        while ($true) {
            $status = Invoke-FolhaLocalApi $config.api ('/api/sources/'+$source.id+'/status') -Password $config.password
            Write-FolhaData ('fonte-'+$number.ToString('00')+'-status.json') $status
            if ($status.status -eq 'completed' -or $null -eq $status.status) { break }
            if ($status.status -in @('failed','cancelled','canceled')) { throw ('Falhou a recolha de '+$url.Host+'. A referência e o estado foram conservados.') }
            Write-FolhaStep ('A aguardar a recolha de '+$url.Host+' ('+$status.status+').')
            Start-Sleep -Seconds 2
        }
        $detail = Invoke-FolhaLocalApi $config.api ('/api/sources/'+$source.id) -Password $config.password
        if (-not $detail.full_text) { throw ('A fonte '+$url.Host+' não forneceu texto extraído. Não será tratada como verificada.') }
        $name = 'fonte-'+$number.ToString('00')+'.txt'
        [IO.File]::WriteAllText((Join-Path (Get-Location).Path $name),[string]$detail.full_text,[Text.UTF8Encoding]::new($false))
        $sources.Add(@{title=[string]$detail.title;url=$url.AbsoluteUri;file=$name;source_id=$source.id;kind='web';retrieved_at=[DateTime]::UtcNow.ToString('o');status='retrieved'})
    }
    Write-FolhaData 'sources.json' $sources.ToArray()
    if ($sources.Count -lt 2) { throw 'Só foi recolhida a Wikipédia. Falta uma fonte independente para a comparação.' }
}

function Read-FolhaResearchSources {
    param($Request, [string]$Instructions)
    $sources = Get-Content -LiteralPath sources.json -Raw -Encoding UTF8 | ConvertFrom-Json
    $notes = [Collections.Generic.List[object]]::new(); $sourceNumber = 0
    foreach ($source in $sources) {
        $sourceNumber++
        $text = [IO.File]::ReadAllText((Join-Path (Get-Location).Path $source.file),[Text.Encoding]::UTF8)
        $prompt = $Instructions + "`nTema pedido: " + $Request.body
        $sections = @(Split-FolhaNotebookInput $Request $prompt $text)
        Write-FolhaData ('fonte-'+$sourceNumber.ToString('00')+'-sections.json') @{source=$source.file;sections=$sections;original_preserved=$true}
        $sectionNumber = 0
        foreach ($section in $sections) {
            $sectionNumber++
            Write-FolhaStep ('O Open Notebook está a ler a fonte '+$sourceNumber+'/'+$sources.Count+', secção '+$sectionNumber+'/'+$sections.Count+'.')
            $name = 'fonte-'+$sourceNumber.ToString('00')+'-parte-'+$sectionNumber.ToString('00')
            $paragraphs = @($section -split '(?:\r?\n){2,}' | Where-Object { $_.Trim() })
            $numbered = [Text.StringBuilder]::new()
            for ($p=0; $p -lt $paragraphs.Count; $p++) { $null = $numbered.AppendLine('[P'+($p+1)+'] '+$paragraphs[$p]) }
            $answer = Invoke-FolhaNotebook $Request $prompt $numbered.ToString() $name
            $json = $answer.Trim()
            if ($json.StartsWith('```')) { $json = $json -replace '^```(?:json)?\s*','' -replace '\s*```$','' }
            try { $analysis = $json | ConvertFrom-Json } catch { throw ('A leitura de '+$source.file+' não devolveu a estrutura pedida. O resultado foi conservado para revisão.') }
            if (-not $analysis.PSObject.Properties['observacoes'] -or -not $analysis.PSObject.Properties['duvidas']) { throw 'Faltam campos na leitura da fonte.' }
            foreach ($observation in @($analysis.observacoes)) {
                if ($observation.afirmacao -isnot [string] -or -not $observation.PSObject.Properties['paragrafos'] -or @($observation.paragrafos).Count -eq 0) { throw 'A observação não identifica o parágrafo que a suporta.' }
                $quotes = [Collections.Generic.List[string]]::new()
                foreach ($reference in @($observation.paragrafos)) {
                    if ([string]$reference -notmatch '^P([1-9][0-9]*)$') { throw 'Referência de parágrafo inválida.' }
                    $index = [int]$Matches[1] - 1
                    if ($index -ge $paragraphs.Count) { throw 'O modelo referiu um parágrafo que não existe na fonte.' }
                    $quotes.Add($paragraphs[$index])
                }
                # The shell copies evidence from the original. Generated paraphrases cannot become quotations.
                $notes.Add(@{source=$source.file;url=$source.url;claim=$observation.afirmacao;quotes=$quotes.ToArray();paragraphs=@($observation.paragrafos);section=$sectionNumber;authority='candidate'})
            }
            foreach ($doubt in @($analysis.duvidas)) { if ($doubt) { $notes.Add(@{source=$source.file;url=$source.url;uncertainty=[string]$doubt;section=$sectionNumber;authority='candidate'}) } }
        }
    }
    Write-FolhaData 'research-notes.json' $notes.ToArray()
}

function Compare-FolhaResearchSources {
    param($Request, [string]$Instructions)
    $notes = Get-Content -LiteralPath research-notes.json -Raw -Encoding UTF8 | ConvertFrom-Json
    $evidence = [Collections.Generic.List[object]]::new()
    $seen = @{}
    foreach ($note in $notes) {
        if (-not $note.PSObject.Properties['quotes']) { continue }
        for ($i=0; $i -lt @($note.quotes).Count; $i++) {
            $key = $note.source+'|'+$note.section+'|'+$note.paragraphs[$i]
            if ($seen.ContainsKey($key)) { continue }
            $seen[$key]=$true
            $evidence.Add(@{id=('E'+($evidence.Count+1));source=$note.source;url=$note.url;section=$note.section;paragraph=$note.paragraphs[$i];quote=$note.quotes[$i]})
        }
    }
    if ($evidence.Count -eq 0) { throw 'Não foram localizadas passagens para comparar.' }
    Write-FolhaData 'comparison-evidence.json' $evidence.ToArray()
    $inputText = ConvertTo-Json -InputObject $evidence.ToArray() -Depth 10
    $answer = Invoke-FolhaNotebook $Request $Instructions $inputText 'comparacao'
    $json = $answer.Trim() -replace '^```(?:json)?\s*','' -replace '\s*```$',''
    try { $analysis = $json | ConvertFrom-Json } catch { throw 'A comparação não devolveu relações verificáveis entre passagens. As fontes foram conservadas.' }
    if (-not $analysis.PSObject.Properties['relacoes']) { throw 'Faltam as relações entre as passagens.' }
    $lookup=@{}; foreach($entry in $evidence){$lookup[$entry.id]=$entry}
    $relations=[Collections.Generic.List[object]]::new()
    foreach($relation in @($analysis.relacoes)) {
        if ($relation.tipo -notin @('concordancia','diferenca') -or @($relation.passagens).Count -lt 2) { throw 'A comparação tem uma relação sem duas passagens válidas.' }
        $urls=[Collections.Generic.HashSet[string]]::new()
        foreach($id in $relation.passagens) { if(-not $lookup.ContainsKey([string]$id)){throw 'A comparação referiu uma passagem inexistente.'}; $null=$urls.Add($lookup[[string]$id].url) }
        if($urls.Count -lt 2){throw 'Uma comparação entre fontes deve identificar pelo menos duas páginas.'}
        # Render only original passages and validated references. Do not turn a generated synthesis into fact.
        $relations.Add(@{type=$relation.tipo;passages=@($relation.passagens);authority='candidate'})
    }
    Write-FolhaData 'comparison-relations.json' $relations.ToArray()
    $report=[Text.StringBuilder]::new()
    $null=$report.AppendLine('Estudo candidato: '+$Request.body)
    $null=$report.AppendLine('Comparação proposta pelo Open Notebook. Os excertos abaixo são copiados das fontes; a concordância, a diferença e a independência das páginas continuam sujeitas a avaliação humana.')
    $used=@{}
    foreach($relation in $relations){
        $label=if($relation.type -eq 'diferenca'){'Possível diferença por esclarecer'}else{'Possível concordância'}
        $null=$report.AppendLine("`n## "+$label)
        foreach($id in $relation.passages){
            $entry=$lookup[[string]$id];$used[[string]$id]=$true
            $null=$report.AppendLine("`n["+$entry.id+'] '+$entry.url)
            $null=$report.AppendLine(($entry.quote -split '\r?\n' | ForEach-Object {'> '+$_}) -join "`n")
        }
    }
    $null=$report.AppendLine("`n## Outras passagens recolhidas")
    foreach($entry in $evidence){
        if($used.ContainsKey($entry.id)){continue}
        $null=$report.AppendLine("`n["+$entry.id+'] '+$entry.url)
        $null=$report.AppendLine(($entry.quote -split '\r?\n' | ForEach-Object {'> '+$_}) -join "`n")
    }
    $null=$report.AppendLine("`nA ausência de uma diferença identificada não prova que as fontes estejam corretas. Os textos extraídos completos permanecem guardados com o trabalho.")
    [IO.File]::WriteAllText((Join-Path (Get-Location).Path 'content.md'),$report.ToString(),[Text.UTF8Encoding]::new($false))
}

function Invoke-FolhaPodcast {
    param($Request, [string]$Content)
    $config = Get-FolhaNotebookConfig $Request
    $settings = Get-Content -LiteralPath $Request.tools_file -Raw -Encoding UTF8 | ConvertFrom-Json
    $profiles = @(Invoke-FolhaLocalApi $config.api '/api/episode-profiles' -Password $config.password)
    $chosen = @($profiles | Where-Object name -ceq $settings.notebook.podcast_profile)
    if ($chosen.Count -ne 1 -or -not $chosen[0].speaker_config_name) { throw 'O perfil de podcast local não está pronto.' }
    $tokens = Invoke-FolhaLocalApi $config.model_api '/tokenize' 'POST' @{content=$Content;add_special=$true}
    $props = Invoke-FolhaLocalApi $config.model_api '/props'
    if (@($tokens.tokens).Count -gt ([int]$props.default_generation_settings.n_ctx-4096)) { throw 'Este conteúdo precisa de um percurso de podcast por partes; o original foi conservado.' }
    Write-FolhaStep 'O Open Notebook está a preparar o guião e a voz do podcast local.'
    $submitted = Invoke-FolhaLocalApi $config.api '/api/podcasts/generate' 'POST' @{episode_profile=$chosen[0].name;speaker_profile=$chosen[0].speaker_config_name;episode_name=('Nexus '+$Request.run_id);content=$Content;briefing_suffix='Português de Portugal. Usa apenas o conteúdo recebido. Conserva as incertezas. Não acrescentes factos, datas ou fontes.'} -Password $config.password
    Write-FolhaData 'podcast-job.json' $submitted
    while ($true) {
        $status = Invoke-FolhaLocalApi $config.api ('/api/podcasts/jobs/'+$submitted.job_id) -Password $config.password
        Write-FolhaData 'podcast-status.json' $status
        if ($status.status -in @('completed','succeeded')) { break }
        if ($status.status -in @('failed','cancelled','canceled')) { throw 'A ferramenta terminou sem produzir o podcast. O estado e o pedido foram conservados.' }
        Write-FolhaStep ('A aguardar o podcast local: '+$status.status+'.')
        Start-Sleep -Seconds 2
    }
    $episodes = @(Invoke-FolhaLocalApi $config.api '/api/podcasts/episodes' -Password $config.password)
    $episode = @($episodes | Where-Object name -ceq ('Nexus '+$Request.run_id))
    if ($episode.Count -ne 1 -or -not $episode[0].audio_url) { throw 'O episódio concluído não tem um áudio inequívoco.' }
    Write-FolhaData 'podcast-episode.json' $episode[0]
    $null = Invoke-FolhaLocalApi $config.api ('/api/podcasts/episodes/'+$episode[0].id+'/audio') -Password $config.password -WaitSeconds 0 -OutputFile 'resultado.mp3'
    $ffmpeg = [string]$settings.ffmpeg
    if (-not (Test-Path -LiteralPath $ffmpeg -PathType Leaf)) { throw 'O FFmpeg configurado não está disponível para verificar o áudio.' }
    Write-FolhaStep 'A verificar o áudio produzido e a preparar a entrega.'
    $previous = $ErrorActionPreference
    try { $ErrorActionPreference='Continue'; & $ffmpeg -nostdin -v error -i resultado.mp3 -f null - 2> audio-check.log; $code=$LASTEXITCODE }
    finally { $ErrorActionPreference=$previous }
    if ($code -ne 0 -or (Get-Item -LiteralPath resultado.mp3).Length -le 0) { throw 'O áudio produzido não passou a verificação de descodificação.' }
    $sha = [Security.Cryptography.SHA256]::Create(); $stream=[IO.File]::OpenRead((Join-Path (Get-Location).Path 'resultado.mp3'))
    try {$hash=[BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-','').ToLowerInvariant()} finally {$stream.Dispose();$sha.Dispose()}
    Write-FolhaData 'artifacts.json' @(@{name='resultado.mp3';label='Descarregar áudio';content_type='audio/mpeg';sha256=$hash})
    $report = "Podcast candidato criado localmente.`n`nO áudio foi descodificado e verificado pelo FFmpeg. A qualidade e fidelidade do guião requerem audição humana.`n`nSHA256: " + $hash + "`n`nConteúdo original:`n`n" + $Content
    [IO.File]::WriteAllText((Join-Path (Get-Location).Path 'content.md'),$report,[Text.UTF8Encoding]::new($false))
}
