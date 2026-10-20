# Handoff Codex — validação em C:\Nexus-Lab

Data: 2026-10-04

## Missão

Aplicar a branch já auditada no laboratório Windows real e executar os mesmos contratos sem tocar em `C:\Nexus` produção.

Branch:
`work/audit-bidirectional-20261004`

Baseline de código de recovery/checkpoints:
`a3fe00de18d05c04e3b0f14024aac6907ed22c55`

Commits posteriores nesta branch são documentação/estado de auditoria salvo indicação contrária.

## Regras

1. `C:\Nexus` é produção/KNOWN_GOOD: não alterar.
2. Usar apenas `C:\Nexus-Lab`.
3. Não copiar runtime, Canonical, credenciais ou bases abertas da produção.
4. Identificar SHA exato antes do teste.
5. Não corrigir arquitetura localmente.
6. Se FAIL: preservar logs, estado e diff; publicar evidência no GitHub.
7. Se PASS: publicar relatório; não promover automaticamente para produção.

## Preparação esperada

Se `C:\Nexus-Lab` ainda não existir, criar clone separado do repositório.
Se existir, primeiro:
- `git status --short`;
- conservar alterações locais;
- não fazer reset destrutivo.

Checkout da branch auditada somente quando a árvore estiver segura.

## Teste principal

Executar a partir do clone Lab:

```powershell
powershell -NoProfile -File .\nexus\windows\check-nexus.ps1
```

Guardar o caminho do relatório produzido.

## Evidência obrigatória

Registar:
- SHA testado;
- versão Windows;
- Python usado;
- estado Git antes/depois;
- `state.json` do verificador;
- contagem pytest;
- `NEXUS PASS/FAIL`;
- wrapper PowerShell;
- duração;
- erros completos se houver.

## Contratos críticos a confirmar

- PREPARED antes de execução externa;
- EXECUTING antes do spawn;
- crash EXECUTING sem resultado -> BLOCKED/RECOVERY_REQUIRED;
- output durável -> reconciliação sem reexecutar Conductor;
- RESULT_ACCEPTED depois de Store.accept;
- Human Gate sem bypass;
- Canonical vazio sem decisão humana;
- proveniência ida/volta;
- 100 000 casos determinísticos incluídos.

## Resultado

Usar apenas:
`PASS / FAIL / BLOCKED / NOT RUN`.

Só PASS completo no PC Lab permite marcar o commit como candidato `PROMOTABLE`. A promoção para `C:\Nexus` continua dependente da decisão humana de Pedro.
