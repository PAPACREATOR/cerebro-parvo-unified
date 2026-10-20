# Continuidade — 04-10-2026

## Trabalho retomado
[PR #7](https://github.com/PAPACREATOR/cerebro-parvo-/pull/7), branch
`nexus-startup-lock-20261003`. F011 arranque único, F012 hash Windows no
ambiente reduzido e F013 proveniência inversa estão implementados.
Main ainda não contém estas correções.

[Última execução Windows](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37162599479):
commit `2870e3366bf9a7baefe392193e375c1ddaabfc11`, Python 3.12.10,
1194 passed in 56.15s, INTEGRITY=PASS. Logs consultados em 04/10.
Contagem inclui variantes parametrizadas; não são 1194 tarefas E2E.
Esta atualização é documental e não altera o código validado.

[Estado](PONTO-DE-SITUACAO.md) · [F011](F011-ARRANQUE-UNICO.md) ·
[F012](F012-HASH-WINDOWS-ISOLADO.md) · [F013](F013-PROVENIENCIA-INVERSA.md).

## PowerShell para reproduzir em cópia separada
Executar na raiz de uma cópia Git deste repositório. Git, Python 3.12 e rede
para dependências são necessários. Não requer administrador. Não altera
C:\Nexos, não copia cofres e não sobrescreve as diferenças locais Spiff.

```powershell
$ErrorActionPreference = 'Stop'
$repoUrl = git remote get-url origin
if ($LASTEXITCODE -ne 0) { throw 'Executar na copia Git do Nexus.' }
if ($repoUrl -notmatch 'PAPACREATOR/cerebro-parvo-') {
    throw 'Origin diferente do repositorio Nexus esperado.'
}
git status --short
if ($LASTEXITCODE -ne 0) { throw 'Falha ao consultar Git.' }
git fetch origin nexus-startup-lock-20261003
if ($LASTEXITCODE -ne 0) { throw 'Falha ao obter a branch.' }
$testedCommit = '2870e3366bf9a7baefe392193e375c1ddaabfc11'
$reviewRoot = Join-Path $env:TEMP ('nexus-review-' + [guid]::NewGuid().ToString('N'))
git worktree add --detach $reviewRoot $testedCommit
if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar a copia separada.' }
Push-Location -LiteralPath $reviewRoot
try {
    py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12/venv indisponivel.' }
    $reviewPython = Join-Path $reviewRoot '.venv\Scripts\python.exe'
    & $reviewPython -m pip install -r nexus/requirements-test.txt
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependencias.' }
    & $reviewPython -c "from nexus.host import verify_integrity; verify_integrity(); print('INTEGRITY=PASS')"
    if ($LASTEXITCODE -ne 0) { throw 'Manifesto invalido.' }
    & $reviewPython -m pytest nexus/tests -q --color=no -p no:cacheprovider -o pythonpath=. --junitxml=nexus-windows-results.xml
    if ($LASTEXITCODE -ne 0) { throw 'Suite FAIL. Conservar diagnostico.' }
    Write-Host "Resultados em $reviewRoot"
} finally {
    Pop-Location
}
```

Comandos entregues para reprodução; não executados no PC nesta sessão.
PASS desse checkout não prova a instalação pessoal nem autoriza sobrescrever
uma versão divergente.

## Pendências para o próximo executor
1. Comparar diferenças locais de Spiff/Conductor, Host, workflows e manifesto,
   preservando o trabalho não commitado em C:\Nexus\repositorio.
2. Conciliar F011–F013 e testar a versão local. Não copiar manifesto antigo
   sobre adaptador novo nem substituir a pasta de dados.
3. Ligar a identidade/ACL Nexus ao executor e provar o circuito real.
4. Configurar Open Notebook/tiny na instalação; confronto com Zotero,
   pesquisa web e/ou humano conforme o contrato aplicável.
5. Provar backup/restauro e ligar capabilities uma a uma.

F013 valida pacotes existentes; navegação clicável e wiki relacional completa
continuam pendentes. Instalação pessoal, Spiff local, tiny e ACL não foram
novamente testados pelo runner. O produto completo não está concluído.

## Atualização posterior — script e regras de trabalho
[Estado atual](ESTADO-TRABALHO.md) contém o script de comando único, a evidência
Windows e as exclusões. Decisão humana de 04/10: Conductor mantém a execução;
Spiff sai do plano. As referências anteriores à conciliação Spiff são históricas.
Regra permanente: testes de ida e retorno, falhas e recuperação por ligação.
