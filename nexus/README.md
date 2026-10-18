# Nexus Minimal — protótipo Windows

Folha → Kernel/Host Python → adapter na fronteira nativa Windows → JSON validado → Creative. MCP externo é transporte opcional. A promoção para Canonical exige confirmação humana ligada.

Estado, SHA validado e falhas pendentes: veja nexus/docs/PONTO-DE-SITUACAO.md.

Arranque determinístico (exemplo):

```powershell
$accepted = git rev-parse HEAD
powershell.exe -NoProfile -File nexus/windows/bootstrap-nexus-local.ps1 -RepoRoot (Get-Location).Path -ExpectedHead $accepted -AuthorizePrepare
```

Ver README original para detalhes de integração e requisitos.
