# Pesquisa — Sandbox nativa Windows para IA

Data: 2026-09-23  
Estado: investigação; não é validação experimental nem autorização de implementação.

## Regra arquitetural

**A IA tem de ficar em sandbox. Docker não é requisito; a fronteira de sandbox é requisito.**

`AIOutput = Proposal`. A IA não escreve diretamente nas memórias, não altera objetivos/regras/permissões, não apaga conhecimento e não executa ações externas diretamente.

## Evidência encontrada

### 1. CPython em Win32 App Isolation

A Microsoft publicou em 2024 um caso específico de execução de CPython 3.12 dentro de Win32 App Isolation. É o precedente mais próximo do nosso núcleo Python-first. A publicação relaciona o isolamento de Python com execução de código não confiável e cenários de segurança envolvendo LLMs.

Conclusão limitada: demonstra que **Python dentro de uma sandbox nativa Windows é um caminho real**. Não demonstra ainda que o nosso runner, CUDA ou RTX 2080 funcionem nessa fronteira.

Fonte primária: Microsoft Windows Developer Blog, “Sandboxing Python with Win32 App Isolation”.

### 2. Chromium em Windows

A documentação oficial do Chromium descreve sandbox Windows com arquitetura broker/target e uso de AppContainer/LowBox como uma das camadas de restrição. Capabilities controlam recursos como rede.

Lição para o Cérebro:

`núcleo confiável (broker lógico) → processo IA não confiável (target) → proposta → validação`

O Chromium também mostra que AppContainer deve fazer parte de defesa em profundidade; não deve ser tratado como solução mágica isolada.

Fonte primária: Chromium Project, documentação “Sandbox”.

### 3. AppContainer / LPAC

A documentação Microsoft descreve AppContainer como fronteira para limitar processos, janelas, dispositivos, ficheiros/diretórios, Registry, rede e credenciais. Less Privileged AppContainer (LPAC) é uma variante mais restritiva.

Isto corresponde ao nosso princípio: **negar por defeito e conceder apenas a capacidade mínima necessária**.

### 4. Correção importante: Win32 App Isolation moderno

A via moderna Win32 App Isolation não deve ser confundida com AppContainer em geral. A documentação atual da Microsoft apresenta Win32 App Isolation moderno como funcionalidade ainda em preview e com requisitos de Windows 11 24H2/build 26100 ou posterior e tooling recente.

Logo devemos separar:
- AppContainer/LPAC = mecanismo de segurança Windows com história anterior;
- Win32 App Isolation moderno = experiência/empacotamento mais recente, com requisitos próprios.

## Hipótese mínima a testar

`Humano → linguagem natural → núcleo Python → pedido estruturado → AppContainer/LPAC → IA → proposta estruturada → validação determinística → evento → resultado`

A sandbox recebe apenas:
- contexto mínimo;
- pesos/modelo necessários;
- canal estreito de entrada/saída;
- capacidades explicitamente concedidas.

Por defeito não recebe:
- cofre criativo;
- cofre canónico;
- SQLite;
- credenciais;
- rede;
- acesso arbitrário ao filesystem;
- autoridade para criar processos/ações externas.

## Ordem de investigação

1. AppContainer/LPAC ou mecanismo nativo equivalente.
2. Medir compatibilidade Python + runner + IPC + pesos.
3. Testar RTX 2080/CUDA.
4. Testar tentativas de acesso indevido.
5. Medir RAM/CPU/latência/arranque.
6. Fazer teste de instalação e recuperação por utilizador não técnico.
7. Repetir exatamente os mesmos testes com Docker endurecido.
8. Só estudar gVisor/VM/microVM se o risco justificar a complexidade.

## Critério de decisão

Não escolher pela popularidade da tecnologia.

`ValorSandbox ≈ Isolamento demonstrado / (RAM + CPU + dependências + instalação + manutenção + recuperação + esforço humano)`

Heurística comparativa; não é uma métrica de segurança calibrada.

## Questões ainda abertas

- CUDA/GPU funciona dentro da fronteira escolhida?
- O runner local funciona sem permissões excessivas?
- Como expor pesos em read-only?
- Qual IPC é mais simples e auditável?
- Que versões de Windows devemos suportar?
- AppContainer/LPAC puro é suficientemente simples de empacotar?
- Docker oferece ganho líquido suficiente para justificar a dependência?

## Resultado desta ronda

A evidência melhora a plausibilidade de uma solução Windows sem Docker e reduz o risco específico de “Python não cabe nesta abordagem”. Não valida ainda a solução para o Cérebro Independente e **não altera formalmente a confiança histórica aproximada de 85%**.

A decisão continua experimental: vence a implementação que preserve a sandbox obrigatória com menor custo total e menor esforço humano.
