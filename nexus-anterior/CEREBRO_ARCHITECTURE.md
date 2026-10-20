# Arquitetura vigente — Kernel estável, capacidades substituíveis

## Estado

A arquitetura conceptual está fechada. O runtime candidato atual é Kernel/Host/Store Python com MCP determinístico e ferramentas externas delimitadas. A PR #23 contém a implementação e evidência corrente.

## Diagrama

```mermaid
flowchart TD
 P[Pessoa / autoridade final] --> UI[Folha Única]
 UI --> K[Kernel / Host / Store]
 K --> CMP[Validação + comparadores]
 K --> MCP[MCP / adapters delimitados]
 MCP --> ON[OpenNotebook]
 MCP --> LT[LanguageTool]
 MCP --> LO[LibreOffice]
 MCP --> Z[Zotero]
 MCP --> MM[ACE-Step / Forge / multimédia]
 ON --> U[UNTRUSTED / candidate]
 LT --> U
 LO --> U
 Z --> U
 MM --> U
 U --> K
 K --> CR[Creative]
 CR --> HG[Human Gate]
 P --> HG
 HG --> CA[Canonical]
 K --> EV[Eventos / proveniência / recuperação]
```

## Responsabilidades

### Pessoa
Única autoridade final. Aprova promoções e ações protegidas.

### Kernel / Host / Store
É o cérebro determinístico/constitucional:
- identidade e estado;
- regras e invariantes;
- seleção de processo/capability;
- Creative e Canonical;
- Human Gate;
- proveniência direta e inversa;
- eventos, integridade, recovery e replay;
- validação de outputs externos;
- confinamento dos processos que lança.

### MCP
Transporte determinístico:
- allowlist de tools;
- argumentos delimitados;
- timeouts e limites;
- zero autoridade;
- zero Store/Canonical direto.

### Ferramentas externas
Executam capacidades especializadas e devolvem candidatos. Não governam o Nexus.

Exemplos: OpenNotebook, LanguageTool, LibreOffice, Zotero, ACE-Step, Forge, FFmpeg, Whisper/TTS e modelos locais.

## Três memórias

Papéis lógicos, não três programas:
- Working;
- Behavioral/Procedural;
- Persistent Knowledge, com Creative e Canonical.

## Três comparadores

- determinístico/exato;
- semântico;
- relacional/proveniência.

Nenhum comparador decide Canonical.

## Adaptabilidade

Adicionar capacidade não deve redesenhar o núcleo:

`nova ferramenta → adapter/contrato → MCP/runner → Kernel valida → Creative → humano → Canonical`.

A ferramenta deve ser substituível. Se a remoção de uma capability destrói a memória ou a autoridade do sistema, está mal integrada.

## Windows

O Host limita processos que lança através da fronteira nativa validada. Isso não significa controlo total sobre todo o Windows nem sobre processos externos iniciados fora do Host.

Provisioning externo permanece um gate separado: recusa segura não equivale a instalação protegida funcional.

## Genealogia

Activepieces, Memory Provider, Spiff e Conductor foram etapas reais da investigação e implementação. Permanecem em `DECISIONS.md`, `historico/` e relatórios. Não são runtime obrigatório atual.

## Critério de desacoplamento

```text
Remove(AI)              -> autoridade e conhecimento sobrevivem
Remove(OpenNotebook)    -> Creative/Canonical/proveniência sobrevivem
Remove(LibreOffice)     -> documentos e memória sobrevivem; capability fica indisponível
Remove(MCP tool)        -> Kernel bloqueia a capability, não perde estado
Internet=OFF            -> núcleo continua utilizável
```
