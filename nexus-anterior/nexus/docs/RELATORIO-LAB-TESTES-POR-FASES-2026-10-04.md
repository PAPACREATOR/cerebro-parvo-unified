# Relatório — organização dos testes do Nexus-Lab

Data: 2026-10-04

## Objetivo

Executar a futura versão do Nexus por fases no `C:\Nexus-Lab`, sem contaminar `C:\Nexus`.

## Ordem

1. `TESTAR-NUCLEO.bat`
2. `TESTAR-BLOCOS.bat`
3. `TESTAR-NEXUS-COMPLETO.bat`
4. `TESTAR-PRATICO.bat`

Todos usam o mesmo `nexus/windows/check-nexus.ps1`, que continua a executar `all` por defeito.

## Núcleo

Inclui Store, Host, startup, crash/recovery, reverse provenance, vaults, schemas e adversarial.

Objetivo:
- estado;
- Human Gate;
- Creative/Canonical;
- proveniência;
- restart/recovery;
- idempotência;
- segurança do núcleo.

## Blocos

Inclui Conductor/workflows, Windows hash, LanguageTool, Office, Notebook e multimédia.

Objetivo:
- testar as peças antes do sistema completo;
- localizar falhas por capability;
- não atribuir um FAIL externo ao Kernel sem prova.

## Nexus completo

Executa `pytest nexus/tests` inteiro, incluindo a matriz determinística de 100 000 casos.

Objetivo:
- regressão integral;
- detectar interferência entre blocos;
- confirmar integridade.

## Prático v1

Executa os contratos que já usam Windows/Conductor real:
- ferramenta Windows sem IA;
- hash Windows em ambiente reduzido;
- ida/volta real Windows + restart;
- leitura real das famílias por Conductor.

Limite:
- ainda não prova instalações reais de LibreOffice, LanguageTool e OpenNotebook no PC Lab;
- estes testes serão acrescentados quando cada capability for instalada/ligada no Lab;
- depois serão acrescentados testes práticos de uso pela Folha e, mais tarde, Nexus completo/homelab.

## Regra

Cada fase produz:
- SHA;
- PASS/FAIL;
- state.json;
- stdout/stderr;
- JUnit XML;
- relatório do verificador.

Nenhum PASS remoto ou parcial promove automaticamente a versão antiga.

## Promoção

O `C:\Nexus-Lab` aprovado integralmente será a nova versão oficial.
`C:\Nexus` atual permanece congelado até decisão humana de promoção.


## Evidência de validação do harness

### FAIL 1 — manifesto de integridade desatualizado
- Work HEAD alterou `store.py` para bloquear `state.json` redirecionado.
- `integrity.json` ficou com o hash anterior.
- Resultado: Windows bloqueou em `INTEGRITY`.
- Interpretação: a proteção funcionou corretamente.
- Correção no Lab: alinhar o hash SHA-256 de `store.py` com o conteúdo atual.
- Foi comunicado no PR #8 para o Work incorporar.

### FAIL 2 — nome de relatório incompatível
- O Nexus terminou com `NEXUS PASS | COMPLETE`.
- O workflow existente procurava `TESTS.stdout.txt`.
- O novo harness tinha renomeado a suite completa para `TESTS-ALL.stdout.txt`.
- Correção: `Suite=all` conserva os nomes `TESTS.*`; só as suites adicionais usam nomes próprios.

### PASS final remoto
HEAD validado:
`9799858b61d4e9a392df0827fd13ea7c07d841e9`

GitHub Windows run:
`37204485220`

Resultado:
- **1219 passed in 54.67s**
- `NEXUS PASS | COMPLETE`
- `POWERSHELL_WRAPPER=PASS`
- Auditoria e suites: SUCCESS

Estado:
- harness por fases: **PASS REMOTO**
- execução em `C:\Nexus-Lab` físico: **NOT RUN**
- promoção: **não autorizada / não executada**

## Aprendizagem

1. O manifesto de integridade deve acompanhar qualquer alteração a ficheiro protegido.
2. Extensões do harness devem manter compatibilidade com nomes/contratos já consumidos por CI.
3. Um FAIL posterior ao `NEXUS PASS` pode pertencer ao harness, não ao núcleo; separar as duas camadas no diagnóstico.
4. Cada novo nível de testes deve reaproveitar o verificador existente, não duplicar lógica.


## Baseline prática v2 — fronteiras de entrada

HEAD funcional testado antes do reforço Conductor:
`f275c49f9ab88790ff722dbb768ff11f855646c1`

Windows run:
`37205291446`

Resultados:
- núcleo: **140 PASS**;
- blocos: **1075 PASS**;
- Nexus completo: **1222 PASS**;
- prático: **16 PASS**;
- `POWERSHELL_WRAPPER=PASS`;
- auditoria: SUCCESS.

Novos contratos provados:
- attachment de **2 MiB exatos** atravessa Folha/Host/Conductor/Windows hash, chega a Human Gate, é aprovado e sobrevive restart;
- **2 MiB + 1 byte** é bloqueado antes de criar run;
- Unicode no limite de 100000 caracteres é aceite;
- 100001 caracteres são bloqueados;
- restart do caso 2 MiB usa evidência durável e não reexecuta a ferramenta;
- IA usada no fluxo verify: zero.

Próximo reforço:
- incluir no prático a via real Conductor de ficheiro ausente -> FAIL determinístico;
- conservar o teste de workflow inválido;
- depois expandir falhas controladas por capability.
