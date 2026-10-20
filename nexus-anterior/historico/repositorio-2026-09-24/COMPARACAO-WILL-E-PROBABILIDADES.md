# Will como precedente técnico e modelo probabilístico honesto

**Nota de atualização — 2026-09-22:** as menções abaixo a «Final Vault SQLCipher» refletem a arquitetura v0.1 no momento desta comparação. A correção posterior de Pedro fixou o final separado com Markdown **e SQLite interno vivo**, mais um segundo SQLite espelhado. A tabela abaixo é histórica; para comparação atual com Will **e ResearchVault**, ver `COMPARACAO-RESEARCHVAULT-WILL-2026-09-22.md`.

Revisão: 2026-09-22, Europe/Lisbon. Pedido de Pedro Alexandre Caldas Coelho: usar matemática e projetos funcionais para avaliar a viabilidade, sem mudar a sua arquitetura. Candidato encontrado: [mindot-ai/will](https://github.com/mindot-ai/will). A busca textual no acervo **atualmente arquivado** (`fontes/recebidas-2026-09-22/`, `fontes/disco-D-2026-09-22/` e documentos numerados) não localizou uma referência inequívoca a esse nome; isto não nega que conste de outra conversa entregue ou disponível noutro local. Não atribuir ao autor uma data de estudo de Will que não foi verificada.

## O que Will demonstra — e o que não demonstra

O repositório público de Will contém código TypeScript, testes, scripts de teste, histórico de versões e licença Apache-2.0; descreve execução por ticks determinísticos, replay, memória, LLM chamado como componente e funcionamento com executivo simulado sem chave. O README mostra interfaces de outbox e confirmação; as [notas da versão 0.10.0](https://github.com/mindot-ai/will/releases) relatam correções de fronteiras/proveniência, replay e um ensaio de 100 mil ticks. Isto é **evidência de uma implementação pública de mecanismos análogos**, não teste independente do Codex nem prova de que cada afirmação do projeto ocorre em todas as máquinas. [Código e arquitetura de Will](https://github.com/mindot-ai/will), [scripts de testes](https://github.com/mindot-ai/will/blob/main/package.json), [licença](https://github.com/mindot-ai/will/blob/main/LICENSE).

| Aspeto | Will — evidência pública | Cérebro Independente de Pedro | Inferência permitida |
| --- | --- | --- | --- |
| Relógio, eventos, replay | Tick determinístico, gravação/comparação de replay descritos e código/testes publicados. | F0 exige EventLog versionado, transição pura, snapshot e replay. | Forte precedente de **exequibilidade do mecanismo**, não de compatibilidade automática do código TS com Python. |
| IA não é o substrato | Will descreve muitos ticks sem LLM e um executivo simulado sem chave; o runner pode chamar o LLM por intervalo ou urgência. | Núcleo funciona sem IA; F1 AIcalls=0; F4 chama só por pedido humano ou evento concreto necessário não resolvido por regras, sem capacidade de agir. | Precedente forte para separar motor e modelo, **não** para copiar a política de chamadas periódicas ou a persistência da “mente” de Will. |
| Memória e persistência | Will tem memória em vários níveis e artefacto de persistência da identidade sintética. | Dois cofres de funções diferentes: Logseq humano e Final Vault SQLCipher; staging não é cofre. | Prova só do padrão geral de camadas; não valida o desenho específico dos dois cofres. |
| Ações e permissões | Will expõe effectors e confirmações do host; tem agência autónoma. | F4 **não concede ações** à IA; F5 futuro requer leases/Gate por operação. | Divergência importante: não importar a agência/efeitos de Will para F4. |
| Interface e ecossistema | Will oferece SDK, canais, MCP e HTTP sidecar. | Logseq como superfície de conversa/documento; pesquisa e entradas por Activepieces. | Will não demonstra a UX Logseq nem a integração Activepieces. |
| Tecnologia | Node/TypeScript/Bun; licença Apache-2.0. | Núcleo Python; componentes escolhidos por Pedro. | Comparar conceitos e testes; não clonar sem revisão de dependências, licença, NOTICE, limites e utilidade. |

Will **valida parcialmente a direção técnica de F0/F1/F4** no sentido de tornar plausível uma implementação de mecanismos semelhantes. Não valida sozinho F2/F3, onboarding, experiência humana, segurança do Final Vault, propriedade intelectual, nem prazo. Na realidade, as notas de versão de Will mostram que mesmo com uma implementação extensa apareceram erros de fronteira em uso vivo — motivo para os testes de falha e proveniência deste projeto, não para concluir “já está tudo resolvido”.

## Matemática aplicável sem inventar percentagens

Definir primeiro o evento mensurável: `E(T,B)` = “protótipo técnico F4 passa a matriz de aceitação até ao tempo T, com orçamento B e recursos definidos”. Isto é diferente de “é conceptualmente possível” e de “um Alpha F9 fica pronto”.

Pela regra da cadeia, sem supor independência:

`P(E) = P(F-1) × P(F0 | F-1) × P(F1 | F0,F-1) × P(F2 | anteriores) × P(F3 | anteriores) × P(F4 | anteriores)`.

Cada termo é **condicional à passagem real dos anteriores, ao prazo T, ao hardware e ao critério PASS**. Multiplicar percentagens escolhidas por intuição não produz uma previsão. Repetir uma fase após falha altera o tempo disponível e o estado de conhecimento; não justifica dizer que a probabilidade final tende automaticamente a 100%.

Para cada contrato testável, registar número de ensaios independentes `n`, sucessos `s`, ambiente e cobertura. Um modelo exploratório beta-binomial, com prior declarado `Beta(a,b)`, produz posterior `Beta(a+s,b+n-s)` e média `(a+s)/(a+b+n)`. Porém, 100 testes artificiais correlacionados não equivalem a 100 amostras independentes de sucesso em uso real. Intervalos e cenários de falha são obrigatórios; uma suite verde só sustenta a suite que executou.

Os projetos comparáveis entram como **evidência prévia por mecanismo**: Will aumenta a plausibilidade de tick/replay e LLM opcional; Logseq, SQLCipher e Activepieces demonstram que existem componentes; nenhum desses factos determina numericamente a probabilidade de integração deste projeto. Para estimar um número defensável são necessários: versões fixadas, máquina verificada, SPECs e critérios fechados, tempos reais de F-1/F0, taxa de falhas/retomas e resultados de integração. Neste momento esses dados faltam; **não há percentagem calibrada para “F4 em dois dias”**.

## Como transformar evidência em previsão útil

1. Congelar critérios PASS de cada fase e definir T/B sem alterar arquitetura.
2. Em cada SPEC, guardar início/fim, tentativas, falhas por categoria, tempo de correção, suite executada e cobertura de falhas.
3. Atualizar uma previsão de tempo e probabilidade **por fase e com intervalo**, depois de pelo menos uma vertical real; separar falhas técnicas de espera por instalação, credenciais e decisão humana.
4. Rever a previsão quando aparecer novo dado, incluindo comparáveis. Identificar explicitamente “estimativa”, “prior”, “observação” e “inferência”.
5. Nunca converter semelhança com Will em alegação de originalidade absoluta ou licença para copiar código. A diferença de produto continua a ser julgada pelo conjunto específico de regras, experiência, integração e uso demonstrado.

## Decisão operacional

Will fica como **referência comparativa**, não dependência nem substituto do Cérebro Independente. Não foi descarregado, executado ou incorporado neste projeto. Qualquer reaproveitamento futuro precisa de SPEC, licença/NOTICE, avaliação de código e decisão de Pedro.

## Revisão de mecanismos — 2026-09-22, 20:37 Europe/Lisbon

**Âmbito da evidência:** nesta ronda foi relido o [README oficial de Will](https://github.com/mindot-ai/will) e a árvore pública `src/cognition/`. O navegador não conseguiu abrir os ficheiros individuais; o acesso direto a `raw.githubusercontent.com` foi bloqueado pelas permissões de rede. Portanto, as afirmações abaixo sobre comportamento de Will são **descrições públicas dos autores**, não uma auditoria linha a linha, reprodução de testes ou garantia independente. Isto corrige qualquer leitura demasiado forte da tabela anterior.

| Mecanismo / problema | Como Will declara resolvê-lo | Contrato do Cérebro Independente | Decisão de comparação |
| --- | --- | --- | --- |
| Continuidade sem chamadas constantes ao LLM | Motores avançam por ticks; o executivo é chamado por intervalo ou urgência; há modo mock sem chave. | Núcleo Python permanece ativo sem IA; em F4 só há chamada por pedido humano ou evento concreto não resolvido pelas regras. | **Mesma separação lógica**, gatilho diferente. Não importar o agendamento periódico nem a urgência afetiva de Will. |
| Reprodutibilidade | Will documenta replay tick-a-tick quando são fixados `randomSeed` e `clock`; declara que execução normal costuma usar relógio de parede. | Toda transição `F(S,E,R,K)` é pura no funcionamento normal; hora, UUID, aleatoriedade e resultado externo entram como valores congelados em eventos. | Padrão útil para testes, mas **garantia diferente**. Não aceitar “tem replay” como prova do determinismo operacional exigido em F0. |
| Entradas e proveniência | Will distingue estímulo externo, efeito da própria ação e origem desconhecida; as notas de versão relatam correções nesta fronteira. | Entrada externa passa por staging, hash, deduplicação, proveniência, validação e evento; resultado de IA também é evento. | Aproveitar a disciplina de **marcar origem em cada fronteira**. Testar que output próprio não volta como fonte independente e que origem desconhecida não recebe confiança. |
| Efeitos externos | Will expõe effectors via host, outbox e confirmação; o resultado regressa ao agente para aprendizagem. | Activepieces é automação externa; F3 requer outbox/retry; F4 não permite ação de IA e F5 futuro exige Gate/capability lease por operação. | Padrão de correlação e confirmação aproveitável em F3; **não** copiar a agência, o autoaprendizado de ações ou autorização geral para F4. |
| Memória | Will descreve crenças, objetivos, narrativa e identidade sintética portátil (PMA). | Working/Behavioral Memory, cofre Logseq humano e Final Vault SQLCipher canónico separados; alterações consolidadas com evidência e autoridade humana. | Analogia só na necessidade de persistência. PMA **não equivale** aos dois cofres nem valida cifragem, proveniência ou supersession. |
| Interação | Will usa SDK, canais, MCP/HTTP e pode decidir falar ou calar-se. | Logseq é superfície de conversa/documento contínuo, sem parede de botões; linguagem natural é convertida em contratos; Activepieces alimenta fluxos externos. | Nenhuma interface Will substitui a UX escolhida. Validar esta parte com protótipo Logseq, não por semelhança conceitual. |
| Escala/complexidade | Will é um motor TypeScript/Bun de mente autónoma com numerosas faculdades. | Python-first e princípio `USE > ADAPT > CREATE`, pequeno núcleo de regras e adaptadores maduros. | Não clonar Will inteiro: aumentaria dependências e provavelmente inverteria a simplicidade e autoridade do produto. |

**Fluxo de referência equivalente sem copiar o produto Will:** `evento externo/humano → fronteira de proveniência → EventLog → transição determinística → (se necessário) NeedAI → contexto mínimo/sem ações → resposta como evento → validação/Gate → novo estado/snapshot`. Em Will, o fluxo correspondente tem perceção → tick cognitivo → executivo periódico/urgente → eventual effector → ack/reafferência → memória/PMA. A semelhança está na **separação motor/modelo/efeito e no registo das fronteiras**; o que muda é quem possui objetivos, quem autoriza ações, quando o LLM é chamado e qual estado é canónico.

**Teste de correção conceitual, ainda por executar:** dada uma lista de eventos versionados e a mesma configuração, duas reconstruções têm de produzir o mesmo hash; nenhuma chamada de IA/Activepieces ocorre durante replay. Um evento sem resolução por regra pode gerar `NeedAI` ou `HumanDecisionRequest` segundo política explícita, mas nunca uma ação implícita. Se a IA não estiver disponível, o sistema preserva o evento pendente e continua as funções determinísticas; o Final Vault não muda sem validação. Se a gravação de evento e a entrega externa falharem a meio, a outbox retoma de forma idempotente. Este conjunto testa **a arquitetura de Pedro**, não é coberto pelo README de Will.

**Veredicto limitado:** não apareceu contradição lógica que obrigue a trocar a arquitetura. Há mecanismos públicos próximos que tornam plausível implementá-la de outra forma mantendo a mesma lógica, mas a integração Logseq/SQLCipher/Activepieces e a garantia de replay ainda carecem de código e testes reais. A afirmação adequada não é “Will valida quase tudo” nem “Will não serve”: Will sustenta sobretudo os padrões de separação, ciclo e confirmação, enquanto o produto de Pedro mantém fronteiras de dados e autoridade substancialmente diferentes. Não atribuir percentagem de sucesso a partir desta comparação.
