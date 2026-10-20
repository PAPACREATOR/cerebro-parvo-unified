[CmdletBinding()]
param(
    [string]$RepoRoot = '',
    [string]$Branch = '',
    [string]$ExpectedHead = ''
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ((-not $Branch -and -not $ExpectedHead) -or
    ($ExpectedHead -and $ExpectedHead -cnotmatch '^[0-9a-f]{40}$')) {
    throw 'NEXUS_EXPECTED_HEAD_REQUIRED'
}

$Git = (Get-Command git.exe -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$OfficialOrigin = 'https://github.com/PAPACREATOR/cerebro-parvo-.git'

function Test-NexusRepo {
    param([string]$Candidate)
    if (-not $Candidate) { return $false }
    try {
        $resolved = (Resolve-Path -LiteralPath $Candidate -ErrorAction Stop).Path
    } catch {
        return $false
    }
    if (-not (Test-Path -LiteralPath (Join-Path $resolved '.git'))) { return $false }
    $origin = (& $script:Git -C $resolved config --get remote.origin.url 2>$null)
    if ($LASTEXITCODE -ne 0) { return $false }
    return (($origin | Select-Object -First 1).Trim() -eq $script:OfficialOrigin)
}

function Resolve-NexusRepo {
    param([string]$Requested)

    if ($Requested) {
        if (-not (Test-NexusRepo $Requested)) {
            throw 'NEXUS_REPOSITORY_NOT_FOUND: -RepoRoot não é o checkout oficial Nexus.'
        }
        return (Resolve-Path -LiteralPath $Requested).Path
    }

    $direct = @(
        (Get-Location).Path,
        'C:\Nexos',
        'C:\Nexus',
        'C:\work\nexus-publicacao',
        (Join-Path $env:USERPROFILE 'cerebro-parvo-'),
        (Join-Path $env:USERPROFILE 'Desktop\cerebro-parvo-'),
        (Join-Path $env:USERPROFILE 'Documents\cerebro-parvo-'),
        (Join-Path $env:USERPROFILE 'Downloads\cerebro-parvo-')
    )

    $parents = @(
        'C:\work',
        $env:USERPROFILE,
        (Join-Path $env:USERPROFILE 'Desktop'),
        (Join-Path $env:USERPROFILE 'Documents'),
        (Join-Path $env:USERPROFILE 'Downloads')
    )

    $candidates = [System.Collections.Generic.List[string]]::new()
    foreach ($candidate in $direct) {
        if ($candidate) { $candidates.Add($candidate) }
    }
    foreach ($parent in ($parents | Select-Object -Unique)) {
        if (-not $parent -or -not (Test-Path -LiteralPath $parent)) { continue }
        Get-ChildItem -LiteralPath $parent -Directory -Force -ErrorAction SilentlyContinue |
            ForEach-Object { $candidates.Add($_.FullName) }
    }

    $matches = @(
        $candidates |
        Select-Object -Unique |
        Where-Object { Test-NexusRepo $_ } |
        ForEach-Object { (Resolve-Path -LiteralPath $_).Path }
    )

    if ($matches.Count -eq 0) {
        throw 'NEXUS_REPOSITORY_NOT_FOUND: não encontrei uma cópia oficial existente. Não foi criado clone novo.'
    }
    if ($matches.Count -gt 1) {
        throw ('NEXUS_MULTIPLE_REPOSITORIES: encontrei mais de uma cópia oficial: ' + ($matches -join ' | '))
    }
    return $matches[0]
}

function Invoke-GitChecked {
    param([string[]]$Arguments, [string]$WorkingDirectory)
    & $script:Git -C $WorkingDirectory @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw ('Git falhou: ' + ($Arguments -join ' '))
    }
}

$RepoRoot = Resolve-NexusRepo -Requested $RepoRoot

$origin = (& $Git -C $RepoRoot config --get remote.origin.url).Trim()
if ($LASTEXITCODE -ne 0 -or $origin -ne $OfficialOrigin) {
    throw 'NEXUS_WRONG_ORIGIN: o checkout não aponta exatamente para PAPACREATOR/cerebro-parvo-.'
}

$dirty = & $Git -C $RepoRoot status --porcelain --untracked-files=all
if ($LASTEXITCODE -ne 0) { throw 'NEXUS_GIT_STATUS_FAILED' }
if ($dirty) {
    throw 'NEXUS_DIRTY_TREE: existem alterações locais; nada foi atualizado.'
}

if ($Branch) {
Invoke-GitChecked -Arguments @('check-ref-format','--branch',$Branch) -WorkingDirectory $RepoRoot
Invoke-GitChecked -Arguments @('fetch','--prune','origin',$Branch) -WorkingDirectory $RepoRoot
$remote = (& $Git -C $RepoRoot rev-parse "origin/$Branch").Trim()
if ($LASTEXITCODE -ne 0 -or ($ExpectedHead -and $remote -ne $ExpectedHead)) {
    throw 'NEXUS_HEAD_NOT_ACCEPTED'
}

& $Git -C $RepoRoot show-ref --verify --quiet "refs/heads/$Branch"
$localExists = ($LASTEXITCODE -eq 0)
if ($localExists) {
    Invoke-GitChecked -Arguments @('switch',$Branch) -WorkingDirectory $RepoRoot
}
else {
    Invoke-GitChecked -Arguments @('switch','--track','-c',$Branch,"origin/$Branch") -WorkingDirectory $RepoRoot
}

Invoke-GitChecked -Arguments @('merge','--ff-only',"origin/$Branch") -WorkingDirectory $RepoRoot

$head = (& $Git -C $RepoRoot rev-parse HEAD).Trim()
$remote = (& $Git -C $RepoRoot rev-parse "origin/$Branch").Trim()
if ($LASTEXITCODE -ne 0 -or $head -ne $remote) {
    throw 'NEXUS_SYNC_MISMATCH: HEAD local não corresponde ao remoto.'
}
} else {
    $head = (& $Git -C $RepoRoot rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $head -ne $ExpectedHead) { throw 'NEXUS_HEAD_NOT_ACCEPTED' }
}

Write-Host 'NEXUS CODE SYNC = PASS'
Write-Host ('REPO: ' + $RepoRoot)
Write-Host ('BRANCH: ' + $Branch)
Write-Host ('HEAD: ' + $head)
Write-Host 'Provisioning/instalação não foi executado.'
