# Validação conceptual, comparação e mitigação — F-1 a F4

**Nota de atualização — 2026-09-22:** este relatório conserva riscos formulados antes da última correção. Decisão vigente: criativo nativo Logseq, final separado com Markdown gerido pelo sistema e **SQLite interno vivo**, mais **SQLite espelhado distinto**. O utilizador escreve normalmente. Menções abaixo a SQLite único/mero índice estão superadas; F2 exige testes de proteção e reconciliação entre Markdown, base interna e espelho. Ver Arquitetura v0.3.

Revisão: 2026-09-22, 20:16 Europe/Lisbon. Autor da conceção declarado: Pedro Alexandre Caldas Coelho. Objeto: Plano Mestre F12 comparado com Constituição, Arquitetura, SPEC-F0-001, plano de instalação, cronologia e decisão explícita de parar no protótipo técnico F4. **Conclusão:** a separação núcleo determinístico / dois cofres / Activepieces / IA opcional é coerente; não é correto afirmar que está “sem erros” ou validada em funcionamento. Os pontos abaixo são lacunas de contrato e de integração a resolver por SPEC e teste, sem trocar a arquitetura.

## Escala de evidência

- **Regra decidida:** expressa por Pedro ou já inscrita na Constituição/Arquitetura.
- **Inferência técnica:** mitigação proposta aqui; não modifica a Constituição.
- **Verificado documentalmente:** coerência entre ficheiros ou documentação oficial de componentes.
- **Não testado:** nenhum código do Cérebro, Logseq, SQLCipher, Activepieces, runtime IA, GitHub remoto ou fluxo ponta a ponta foi validado nesta auditoria.

## Matriz de falhas e portas de prova

| ID / prioridade | Achado e fonte | Risco concreto | Mitigação mínima proposta / prova necessária |
| --- | --- | --- | --- |
| V01 — alto | F12 desenha EVENT → VALIDATE → TRANSITION → NEW STATE → EVENT LOG; F0 promete recuperar crashes. | Se estado e log forem escritas independentes, crash entre elas cria estado impossível de reproduzir. | SPEC F0 deve definir a fronteira de commit: evento aceite e estado/snapshot consistente, com recuperação que só aplica eventos confirmados. Injetar crash em cada ponto de escrita e comparar hash após restart. Não assumir “append-only” sozinho como atomicidade. [SQLite atomic commit](https://www.sqlite.org/atomiccommit.html), [WAL recovery](https://www.sqlite.org/walformat.html). |
| V02 — alto | F12 alterna `dedup_id` derivado do payload e `eventId`; Constituição fixa `event_id`. | Dois eventos legítimos iguais podem ser apagados por dedup de conteúdo; produtor pode reenviar o mesmo evento com novo ID. | Core idempotente por `event_id`; F3 define separadamente identidade da mensagem externa e política por fonte. Testar repetição idêntica e duas ocorrências iguais legítimas. |
| V03 — alto | F3 atravessa Activepieces, staging e Core; outbox descrita mas não há transação comum entre processos. | Perda ou duplicação após timeout/ack ambíguo. | Sem prometer “exactly once” extremo a extremo: staging durável PENDING → tentativa com ID estável → ack confirmado → PROCESSED; retry seguro e fila de falhas observável. Matar cada processo antes/depois do ack e verificar contagem/eventos. Activepieces usa fila/worker e requer diagnóstico de jobs falhados: [filas oficiais](https://www.activepieces.com/docs/install/troubleshooting/bullboard). |
| V04 — alto | F4 diz guardar output e hashes; um excerto afirma guardar “todo o contexto”. | O EventLog pode virar cópia de dados sensíveis, inclusive informação do Logseq ou resultados de terceiros; hash não protege conteúdo gravado em claro. | Fechar política de minimização/redação/retenção antes da primeira chamada real. Replay guarda AI_RESULT validado e metadados necessários, sem repetir geração. Testar com marcador secreto artificial e procurar vazamento em logs, snapshots e relatórios. |
| V05 — alto, revisto | O cofre final passou a Markdown; SQLite é índice mais estado operacional. Cifragem e backup do Markdown ainda não estão definidos. | Exposição de dados em repouso; perda do estado operacional que não se recompõe só do índice; espelho desatualizado. | Em F2, definir proteção do Markdown e backup/restauro de **ambos os cofres** e do estado operacional; testar acesso não autorizado, reconstrução do índice FTS5 a partir do final e recuperação de decisões pendentes. SQLCipher é opção histórica, não obrigação. |
| V06 — alto, revisto | Logseq Classic/File Graph é o cofre criativo escolhido; o cofre final é outra pasta Markdown. | Plugin ou sincronização podem alterar notas sem preservar identidade, referências ou a fronteira entre os cofres. | Fixar versão do Logseq Classic e testar em grafos/pastas artificiais: importação, links, anexos, leitura e restauro. Garantir que o adaptador não promove automaticamente conteúdo nem aponta a escrita criativa para a pasta final. |
| V07 — alto | “Organizador uma vez” e “qualquer formato” são requisitos humanos, mas não há contrato por formato no F12. | Perda silenciosa de conteúdo/anexos, original modificado, duplicados na retoma. | Inventário por lote; lista explícita de formatos suportados; original intocado e hash; Markdown mais anexos; relatório de perdas/falhas por ficheiro; idempotência de retoma. Testar amostras falsas de cada formato antes de acervo real. “Uma vez” = uma migração por fonte, não proibição de recuperar falha. |
| V08 — médio/alto | F1 Gate 0–3 está definido, mas falta tabela concreta de ações, permissões e versões. | Mesma intenção recebe ALLOW/ASK/DENY inconsistentes após atualização. | Matriz versionada por tipo de ação, recurso, reversibilidade e autorização humana. Testes de tabela e replay com versão congelada; política por defeito conservadora perante ambiguidades. |
| V09 — médio/alto | F4 mede `AI calls desnecessárias / AI calls`. | Denominador zero; mede só chamadas feitas, não tarefas generativas indevidamente bloqueadas; 100+100 não prova robustez geral. | Definir antes do teste: taxa de chamadas indevidas por tarefas determinísticas, taxa de tarefas generativas encaminhadas, custo/latência e falsos positivos; indicar N e falhas. Conjunto sintético fixo e novo conjunto cego. |
| V10 — médio/alto | F-1 inclui Activepieces no Windows e backup Restic. | Instalação não cabe no ambiente real; backup só da pasta perde dados/configuração. | Verificar WSL2/Docker Compose, CPU/RAM, Postgres, Redis e segredo de encriptação do Activepieces antes de F3. Documentação oficial: Windows exige WSL2, pelo menos 2 vCPU/4 GB; dados ficam em volume Postgres e o segredo `.env` é necessário para recuperar ligações: [instalação oficial](https://www.activepieces.com/docs/install/options/docker-compose). Fazer restauro de ensaio, não apenas criar arquivo. |
| V11 — médio | F12 chama “protótipo final” F9, mas Pedro pede F4. | Promessa enganadora sobre funcionalidade final ou prazos. | Nomear a entrega “protótipo técnico F4” e listar ausências: F5 segurança de ações, F6 proatividade, F7 domínios/interface completa, F8 stress, F9 Alpha. Critério de PASS só da fase delimitada. |
| V12 — médio | GitHub privado pedido; fontes e dossier estão dentro da pasta Git. | Push acidental de propriedade intelectual, dados pessoais ou chave; privado não é NDA. | `.gitignore` agora exclui `fontes/`, `juridico/`, `documentacao/`, memória e diário. Verificar `git status`, `git check-ignore`, índice e histórico **antes** de commit/push; usar allowlist de ficheiros. Só criar remoto privado na conta confirmada. Exposição anterior de chave Google exige rotação. |
| V13 — médio | Plano diz IA dispensável; F4 precisa de um fornecedor para demonstrar. | Protótipo parece “offline” quando a API falha, ou teste usa dados sensíveis. | Primeiro fornecedor e conjunto artificial isolados; testar IA OFF com funções F0–F3 ainda PASS. Se usar Google, contexto mínimo e chave nova; se local, registrar hardware/modelo/licença. Sem exigir GPU NVIDIA para núcleo. |
| V14 — médio | Regras de regressão cumulativa e “100%” do F12. | Percentagem pode sugerir ausência total de bugs, e testes da fase podem tornar-se lentos ou frágeis. | Definir suites por fase, execução real, ambiente, duração, PASS/FAIL e regressões; “100%” só significa todos os casos **da suite definida** passam. Falha bloqueia avanço, não é apagada. |

## Validação dos princípios centrais

| Princípio de Pedro | Coerência documental | Estado real |
| --- | --- | --- |
| Pessoa decide; máquina aconselha sob regras | Presente na Constituição, Gate e plano | Contratos e testes ainda por fechar |
| Núcleo determinístico sem IA obrigatória | Presente de F0/F1 até F4; replay grava resultados externos | SPEC-F0-001 escrita; código e replay ausentes |
| Dois cofres Markdown: Logseq criativo e final aprovado | Decisão atual; staging não é terceiro cofre | Versão Logseq, proteção Markdown, promoção e integração pendentes |
| Activepieces é parte do ecossistema, pesquisa não é plugin | Consistente nas decisões atuais | Fluxo F3 não implementado |
| Interface Logseq como conversa/documento, sem parede de botões | Presente na Arquitetura; não entregue em F4 técnico | Design de interação e ensaio com utilizador futuros |
| IA efémera e sem capacidades por defeito | Presente; F4 permite apenas análise/geração sem ação | Política de contexto/auditoria e testes pendentes |
| Reaproveitar antes de criar, licenças antes de incorporar | Regra documental | Licenças por versão ainda não verificadas |
| Extrator inicial termina após migração | Presente na memória; adicionado como dependência transversal ao plano | Conversores e catálogo de formatos pendentes |

## Ordem de mitigação sem redesenhar

1. F-1: confirmar ferramenta/versão/licença, proteção Git e backup/restauro artificial.
2. F0: fechar V01/V02 e implementar a SPEC mínima; crash/replay antes de F1.
3. F1: fechar matriz de Gate V08 com casos artificiais e IA=0.
4. F2: fixar versão Logseq Classic, proteger e restaurar os dois cofres Markdown, testar SQLite/FTS5 como espelho e estado operacional, e provar a regra de aprovação/recuperação; testar V05–V07 revistos.
5. F3: fechar protocolo de entrega e recuperação V03; testar falhas de processo/rede.
6. F4: política de contexto V04, fornecedor V13, métricas V09 e replay de AI_RESULT.

**Veredicto:** arquitetura conceptualmente consistente, mas há bloqueios técnicos verificáveis. Nenhum percentual de probabilidade publicado no F12 foi aceite como estimativa calibrada. Esta matriz é um plano de falsificação por testes, não garantia de que o sistema funcionará.

Ver também `COMPARACAO-WILL-E-PROBABILIDADES.md`: projeto comparável como evidência de mecanismos e regra da cadeia/Bayes para estimar probabilidades quando existirem dados reais. Mitigação e probabilidade são complementares: mitigação tenta reduzir risco; medição estima o risco remanescente.
