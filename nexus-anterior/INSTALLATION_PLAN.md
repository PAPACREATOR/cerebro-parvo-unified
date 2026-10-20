# Instalação local — procedimento vigente

Este documento descreve a instalação segura do candidato atual. Não usar os procedimentos históricos de Activepieces/Conductor como instrução corrente.

## Pré-requisitos

- Windows 64-bit;
- Git;
- Python 3.12;
- uma única cópia oficial do repositório;
- origin exato: `https://github.com/PAPACREATOR/cerebro-parvo-.git`.

## 1. Sincronizar código

Usar `nexus/windows/sync-nexus-code.ps1`.

O script:
- pode ser lançado fora da pasta do repositório;
- procura apenas locais limitados;
- valida origin;
- recusa múltiplas cópias;
- recusa árvore suja;
- faz apenas fast-forward;
- não instala ferramentas.

## 2. Preparar e testar o Core

Usar `nexus/windows/bootstrap-nexus-local.ps1`.

Sequência:
1. sync;
2. `.venv` Python 3.12;
3. dependências Nexus;
4. Core;
5. Blocks;
6. Practical;
7. All;
8. gates de autoridade/confinamento/recovery/bidirecionalidade;
9. inventário externo;
10. plano do que falta;
11. relatório final.

## 3. Relatórios esperados

Em `C:\Nexus-Tools`:
- `pc-core-report.json`;
- `external-tools-inventory.json`;
- `external-provision-plan.json`;
- `local-bootstrap-report.json`.

Cada relatório deve corresponder ao HEAD local.

## 4. Provisioning externo

Os instaladores históricos de ACE-Step/Forge/avatar/isolamento continuam bloqueados por `NEXUS_PROTECTED_PROVISIONING_PENDING`.

Isto é intencional.

Não remover o guard apenas para instalar. O provisioning só abre depois de:
- inventário real;
- pin/licença;
- staging protegido;
- verificação;
- cleanup/recovery;
- teste positivo;
- teste de bloqueio;
- regressão.

## 5. Ferramentas já presentes

Não reinstalar automaticamente LibreOffice, Zotero, LanguageTool, OpenNotebook, FFmpeg ou Java sem primeiro os detetar e validar.

## 6. Regra de segurança

CI PASS não substitui PASS físico do PC. Uma ferramenta instalada não equivale a capability integrada. Uma capability integrada não equivale a autoridade.

O histórico de instalação anterior permanece no Git e em `historico/`.
