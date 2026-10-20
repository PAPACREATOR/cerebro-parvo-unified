# Relatório técnico — Kernel + Spiff + Conductor

Data: 2026-10-04  
Estado: investigação de implementação; arquitetura Nexus não alterada.

## Resultado da fase 1

Versões testadas:
- SpiffWorkflow: `3.2.0`
- Microsoft Conductor: commit fixado `11dcc41ed3df78f0806127cc901822fe8758294b`, package `0.1.41`

### FAIL inicial útil

O primeiro S0 falhou antes da execução:
- fixture Conductor declarou input `integer`;
- Conductor aceita `string | number | boolean | array | object`;
- correção mínima: `integer -> number`.

O gate funcionou: S1–S5 não arrancaram enquanto S0 estava FAIL.

### PASS conjunto

Run Spiff+Conductor: `37206389246`.

- S0 smoke: PASS;
- S1: 1000/1000 ida, ~9.08 s;
- S2: 1000/1000 volta, ~9.13 s;
- S3: 1000/1000 limites/single-dispatch, ~9.15 s;
- S4: 1000/1000 classificações, ~9.17 s;
- S5: 1000/1000 stress seed fixa, ~9.30 s.

Total: **5000/5000 casos conjuntos PASS**, além de S0.

Todos os casos usam Spiff e Conductor no mesmo circuito. O Conductor usado nesta carga é um workflow `set` sem I/O externo e sem IA, para medir coordenação/routing/contrato em vez de custo de criação de subprocessos.

### Nexus base não contaminado

No primeiro ensaio, a suite Nexus normal falhou na recolha porque Spiff ainda não era dependência normal. Isso foi corrigido tornando o teste Spiff opcional fora do workflow dedicado.

HEAD posterior:
- Auditoria: SUCCESS;
- Spiff+Conductor: SUCCESS;
- Nexus Windows normal: SUCCESS;
- Spiff **não** foi acrescentado a `requirements-test.txt` normal.

Conclusão: Spiff continua componente experimental/opcional.

## O que os 5000 provam

Provado:
1. Kernel consegue impor limite externo antes dos motores.
2. Spiff 3.2.0 e Conductor 0.1.41 coexistem.
3. Um workflow Spiff pode disparar uma capability Conductor.
4. O resultado regressa de Conductor -> Spiff -> Kernel.
5. Identidade fecha por `case_id + input_hash`.
6. O trace Conductor regressa ao Kernel.
7. Cada caso usa uma chamada externa lógica; não há duplicação no contrato testado.
8. PASS/FAIL/UNKNOWN/BLOCKED podem ser transportados sem os motores ganharem autoridade de promoção.
9. Seeds fixas tornam stress reproduzível.
10. Nenhuma IA/provedor é necessária para esta integração.

Não provado ainda:
- escolha/gate/mutex/multi-instance reais do Spiff;
- parallel/foreach/MCP reais do Conductor dentro de um agente Spiff;
- crash entre duas capabilities de um agente;
- replay Kernel-owned de agente multi-passo;
- ferramenta Windows real nesta suite conjunta nova;
- IA real;
- PC físico `C:\Nexus-Lab`.

## Modelo de responsabilidade a testar

### Kernel — autoridade

O Kernel é o único componente que sabe política e autoridade.

Responsável por:
- `operation_id`;
- input/hash;
- Store/EventLog;
- Creative/Canonical;
- Human Gate;
- allowed capabilities;
- decidir se IA pode ou não ser usada;
- escolher backend/motor;
- limites globais;
- deadline;
- número máximo de dispatches;
- idempotência;
- replay/recovery;
- validar outputs e traces.

### Spiff — agente efémero

Hipótese funcional a provar:
- representa lógica transitória do agente;
- routing;
- escolhas;
- gates técnicos;
- joins/merge;
- multi-instance;
- mutex interno;
- subworkflow lógico.

Spiff **não precisa saber** se uma capability é:
- Python;
- PowerShell;
- LibreOffice;
- MCP;
- modelo tiny;
- outra IA.

O agente pede uma capacidade abstrata ao dispatcher do Kernel. O Kernel resolve a implementação.

Spiff não pode possuir:
- memória Nexus;
- credenciais;
- Canonical;
- Human Gate;
- política de IA;
- retry global;
- recovery;
- autoridade de persistência.

### Conductor — executor de capability efémero

Adequado a:
- `script`;
- `set`;
- MCP direto sem LLM;
- `wait`;
- workflow/subworkflow técnico;
- parallel;
- foreach;
- timeouts;
- eventos/traces;
- execução de ferramentas.

Conductor não pode possuir:
- estado autoritativo Nexus;
- Human Gate Nexus;
- Canonical;
- decisão de usar IA;
- recovery Nexus.

O step Conductor `agent`/provider-backed continua fora do adaptador Nexus por defeito. Qualquer IA só pode entrar se o Kernel autorizar uma capability específica.

## Três rotas possíveis do Kernel

### A — Kernel -> Conductor
Usar para uma capability simples ou fluxo técnico onde Spiff não acrescenta lógica.

### B — Kernel -> Spiff
Usar para lógica de agente puramente transitória que não necessita ferramenta externa.

### C — Kernel -> Spiff -> Kernel dispatcher -> Conductor
Usar quando um agente tem lógica própria e precisa de uma ou várias capabilities.

A forma C é a principal hipótese desta investigação.

## Limites em camadas

### Limites globais Kernel
Sempre superiores/externos:
- tamanho máximo de input;
- allowed capabilities;
- `allow_ai`;
- máximo de dispatches;
- deadline da operação;
- idempotency key;
- máximo de replay;
- estado final permitido.

### Limites Spiff
A provar/implementar no adaptador:
- task types permitidos;
- máximo de transições;
- máximo de branches;
- máximo de multi-instances;
- sem `Execute/Transform` direto se isso puder contornar o dispatcher.

### Limites Conductor
Já existem no motor:
- `max_iterations`;
- `timeout_seconds`;
- timeout por script/MCP;
- `max_concurrent` no foreach;
- failure mode;
- profundidade de workflow.

Regra: o limite efetivo é sempre o mais restritivo entre Kernel e executor.

## Contrato de replay Kernel-owned — hipótese crítica

Para agentes multi-passo:

1. Kernel cria operação e fixa hash do agent spec.
2. Spiff novo inicia de forma efémera.
3. Quando o agente pede uma capability, o Kernel calcula `dispatch_id` determinístico:
   - operation_id;
   - agent_spec_hash;
   - task/step lógico;
   - ordinal;
   - capability abstrata;
   - input_hash.
4. Kernel verifica se esse `dispatch_id` já tem resultado durável.
5. Se não tem:
   - resolve backend;
   - executa Conductor/capability;
   - persiste resultado bruto + trace;
   - só depois devolve ao Spiff.
6. Se já tem:
   - **não reexecuta a ferramenta**;
   - devolve ao Spiff o resultado gravado.
7. Se o Kernel morrer:
   - novo Kernel cria novo Spiff;
   - reproduz a lógica desde o início;
   - chamadas já gravadas são respondidas pelo ledger;
   - só executa a primeira capability ainda não durável.
8. Divergência de spec/hash/call order -> BLOCKED/RECOVERY_REQUIRED.

Assim Spiff permanece descartável e a memória continua exclusivamente no Kernel.

## Fase 2

Testar, por esta ordem:
- R0: Spiff usa o mesmo agente com backend diferente decidido pelo Kernel; o agente não vê `AI vs deterministic`.
- R1: capability proibida é bloqueada pelo Kernel antes de Conductor.
- R2: limite global de dispatches bloqueia um agente que tente exceder.
- R3: routing/choice Spiff.
- R4: Conductor parallel/foreach chamado pelo agente.
- R5: crash depois do primeiro dispatch e replay com Spiff novo sem repetir Conductor.
- R6: spec alterado durante replay -> BLOCKED.
- R7: ferramenta Windows real numa amostra pequena.

Nenhum destes testes promove Spiff a dependência obrigatória. A decisão só ocorre depois da fase 2.
