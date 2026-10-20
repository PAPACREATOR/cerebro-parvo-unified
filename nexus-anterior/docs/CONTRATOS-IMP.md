# Contratos corrigidos IMP-001–026

Extração da Parte III do [prompt mestre](baseline/CEREBRO_PROMPT_MESTRE_CURSOR_2026-09-26.md), preservado integralmente. A extração é uma vista de consulta; não declara testes executados.


Esta é a versão mais detalhada dos contratos IMP recuperada. Os marcadores **POR DEFINIR** são bloqueios reais. Não os preencher por inferência.

# IMP-001–IMP-026 — Especificação funcional corrigida

Estado: contrato de desenho para futura programação; não é código, nem teste executado, nem alteração ao repositório. Subordinado à arquitetura conceptual fechada: pessoa no topo; Creative e Canonical como domínios de autoridade distintos; eventos autoritativos → estado materializado → derivados. Questões ainda não decididas estão marcadas **POR DEFINIR**, não são delegadas ao programador para improvisação.

## Regras globais

G1. Nenhum IMP escreve diretamente em Canonical.\
G2. Nenhum adaptador escreve diretamente em Creative, SQLite, Markdown ou EventLog.\
G3. Cada execução admitida possui `operation_id` a partir de IMP-003. Antes disso, a receção tem apenas uma referência/recibo temporário que permite correlacionar retries; isso não é um `operation_id` nem autoriza efeitos autoritativos.\
G4. Cada transição aceita somente estados e entradas explicitamente permitidos; o orquestrador, não um IMP adjacente, decide a próxima etapa.\
G5. Falha nunca é interpretada como sucesso.\
G6. Repetição da mesma `operation_id` não duplica efeitos; a prova de que duas tentativas pertencem à mesma receção lógica exige correlação suficiente, não mera igualdade de nome ou bytes.\
G7. O original nunca é alterado durante processamento; a eliminação futura é ramo separado e autorizado.\
G8. Semelhança semântica nunca significa duplicação.\
G9. Duplicação exata significa igualdade de bytes demonstrada por critérios definidos; digest idêntico é candidato a comparação, não autorização para eliminação.\
G10. Qualquer efeito autoritativo passa pelo mecanismo de eventos; operações persistentes anteriores a IMP-018 requerem contrato de recibos/reconciliação compatível com a hierarquia autoritativa. **POR DEFINIR:** quais eventos e fronteiras transacionais representam essas mutações preliminares.\
G11. FTS5/cache são derivados e reconstruíveis.\
G12. `RECOVERY_REQUIRED` bloqueia novas mutações da operação até reconciliação.\
G13. Plugins e IA não aprovam nada.\
G14. Eliminação do original exige decisão humana explícita, específica e atual.\
G15. Cada IMP executa só a sua responsabilidade.\
G16. Resultados externos que sustentem uma mutação autoritativa têm evidência/proveniência congelada; replay não invoca novamente adaptadores, Web ou IA.

## Desenho e estados

```
text
```

`001 → 002 → 003 → 004 → 005 → 006 → 007 → 008 → 009 → 010     → 011 → 012 → 013 → 014 → 015  IMP-015: READY  → 016 → 017 → 018 → 019 → 020 → 021          REVIEW → 021 (apresentar revisão; sem Creative automático)          FAILED → 022 (falha de conteúdo)  Falha técnica em qualquer etapa → 022; interrupção/incerteza → 023. RECOVERY_REQUIRED → bloquear mutações da operação até reconciliação. Pedido futuro e separado: 024 → 025 → 026.`

Os estados de progresso da operação podem ser `RECEIVED`, `VALIDATED`, `IDENTIFIED`, `QUARANTINED`, `HASHED`, `FORMAT_DETECTED`, `ADAPTER_SELECTED`, `PROCESSING`, `UNTRUSTED_RESULT`, `VALIDATING`, `MATERIALIZED`, `DERIVATIVES_UPDATED`/`DERIVATIVES_DIRTY` e `PRESENTED`. `READY`/`REVIEW`/`FAILED` de IMP-015 são classificações do conteúdo, não recibos de commit. `COMMITTED`/`NOT_COMMITTED`/`RECOVERY_REQUIRED` são estados de reconciliação de mutações. `RETRYABLE` é um resultado operacional condicionado a segurança comprovada, não um estado de sucesso. Uma UI apresentada não aprova nem materializa conhecimento.

A classificação de conteúdo `REVIEW` conserva a ligação ao original e a evidência existente e é apresentada em IMP-021; não cria Creative. Uma decisão humana posterior que aceite ou transforme esse conteúdo exige contrato específico futuro, fora do fluxo automático aqui definido. **POR DEFINIR:** limites concretos de aceitação de formato, tamanho, classificação e retenção; não há valores inventados neste documento.

## Microprocessos e testes de contrato

Para cada IMP, os testes abaixo são casos especificados com resultado esperado; nenhum foi executado. O portão de revisão exige coerência das pré-condições, saídas, falhas, transições, idempotência e invariantes aplicáveis antes de avançar ao IMP seguinte. Um caso não resolvido bloqueia o portão.

## IMP-001 — Receber ficheiro

Entrada: ficheiro largado na Folha e contexto da sessão. Receber stream/referência, sem interpretar conteúdo, converter ou alterar bytes; criar receção temporária. Saída: `ReceivedInput(temp_ref, filename, byte_size)` ou `RECEIVE_FAILED` por acesso ausente, transferência incompleta ou interrupção. Proibido criar IDs definitivos, hash, deduplicar ou escrever Creative/Canonical. Testes: igualdade dos bytes recebidos com os enviados; nome Unicode; ficheiro vazio; ficheiro grande; interrupção; ausência de efeito autoritativo. Um ficheiro vazio pode ser recebido aqui; a aceitação é decidida em IMP-002.

## IMP-002 — Validar entrada

Entrada: `ReceivedInput`. Confirmar existência, legibilidade, integridade verificável da transferência, limite de tamanho configurado e objeto processável; não inferir formato pelo nome. Saída: `InputAccepted` ou `InputRejected(reason)`. Rejeição encerra o processamento normal, preservando apenas a evidência exigida pela política de falhas/retenção. Testes: válido; inexistente; ilegível; truncado detetável; tamanho fora do limite; nome enganador; ficheiro vazio segundo regra explícita. Limites/política concretos: **POR DEFINIR**.

## IMP-003 — Criar `operation_id`

Entrada: `InputAccepted`. Se houver prova de pertença a operação já registada, reutilizar o ID; caso contrário, gerar ID único e registar contexto mínimo. Saída: `OperationCreated(operation_id, temp_ref)`. Igualdade de nome/hash não prova mesma operação lógica. Testes: unicidade; retry correlacionado; receções separadas de bytes iguais; colisão simulada; crash; ID inválido recusado. A persistência do registo inicial deve satisfazer G10: fronteira de evento/recibo **POR DEFINIR**.

## IMP-004 — Criar `attachment_id`

Entrada: operação válida e input aceite. Atribuir ID estável ao anexo, independente de nome e localização; associá-lo à operação. Saída: `AttachmentIdentified`. Proibido usar filename/path como identidade. Testes: mover/renomear preserva ID; colisão; retry da mesma operação não cria segundo anexo; receções independentes não são fundidas automaticamente. Persistência e replay desta atribuição: sujeitos a G10.

## IMP-005 — Colocar em quarentena

Entrada: anexo identificado. Copiar bytes para localização controlada, fechar a escrita, confirmar existência e tamanho básico antes de reconhecer conclusão. Não destruir entrada/original. Saída: `Quarantined(attachment_id, quarantine_ref)` ou falha explícita. Artefacto parcial comprovadamente criado pela operação pode ser removido apenas segundo contrato de recuperação; na dúvida, não apagar. Testes: sucesso; disco cheio; crash; escrita parcial; retry; original byte-a-byte intacto; quarentena sem recibo → reconciliação.

## IMP-006 — Calcular hash

Entrada: `Quarantined`. Ler sem modificar; calcular SHA-256 dos bytes completos e associar digest ao anexo. Saída: `HashCalculated(attachment_id, algorithm, digest)` ou falha de leitura explícita. Hash não autoriza eliminação. Testes: vetor conhecido; repetibilidade; mudança de um byte; vazio se aceite; falha de leitura; arquivo não modificado.

## IMP-007 — Verificar duplicação exata

Entrada: anexo e digest. Procurar digests coincidentes e verificar igualdade exata pelos critérios de bytes definidos; classificar `EXACT_DUPLICATE` com IDs correspondentes ou `UNIQUE_BINARY`. Um digest igual sozinho não é prova incondicional; ausência de coincidência não prova identidade semântica. Proibido deduplicar por embeddings/IA ou eliminar. Testes: bytes iguais; texto equivalente com bytes diferentes; paráfrase; mesmo nome e bytes diferentes; digest não encontrado; colisão simulada → não declarar igualdade sem verificação.

## IMP-008 — Identificar formato

Entrada: anexo em quarentena. Combinar evidências do conteúdo, MIME/assinaturas apropriadas; extensão é auxiliar. Saída: `FormatDetected(format, evidence)` ou `FORMAT_UNKNOWN`/inconsistência explícita. Testes: PDF renomeado `.txt`; DOCX; EPUB; imagem; sem extensão; assinatura inválida; conflito entre extensão e conteúdo. O grau de confiança e política de formatos ficam **POR DEFINIR**.

## IMP-009 — Selecionar adaptador

Entrada: formato identificado ou desconhecido. Consultar registo de capacidades autorizado, compatibilidade e regras; não instalar software nem improvisar fornecedor. Saída: `AdapterSelected(adapter_id, adapter_version, task_type)` ou encaminhamento explícito a revisão/falha conforme regra. Exemplos condicionais: PDF → adaptador configurado; DOCX/EPUB → Docling se configurado. Testes: disponível; indisponível; dois candidatos; versão incompatível; formato desconhecido. Prioridade e destino exato de casos sem adaptador: **POR DEFINIR**.

## IMP-010 — Criar tarefa

Entrada: operação, anexo e adaptador escolhido. Construir tarefa fechada com `task_id`, IDs, input autorizado, permissões mínimas, limites, timeout e contrato do resultado. Saída: `AdapterTask`; nenhum acesso global ao Cérebro. Testes: envelope completo; task ID único; retry sem duplicar tarefa lógica; ausência de campo obrigatório; privilégios excessivos rejeitados. Limites concretos: **POR DEFINIR**.

## IMP-011 — Executar adaptador

Entrada: `AdapterTask`. Executar somente a tarefa, com isolamento efetivo adequado ao risco; capturar versão, saída, código de saída e erros. Saída: `AdapterExecutionResult` explícito inclusive timeout/crash. Adaptador não acede diretamente aos cofres, SQLite, Markdown ou EventLog. Testes: sucesso; timeout; crash; saída enorme/malformada; tentativa de acesso proibido → bloqueio; ausência de falso sucesso. Modelo de sandbox e limites: **POR DEFINIR**.

## IMP-012 — Receber resultado

Entrada: output do adaptador. Receber como não confiável e correlacionar com `task_id`, `operation_id`, `attachment_id` e versão. Saída: `UntrustedAdapterResult` ou recusa explícita; ainda não é conhecimento. Testes: IDs certos; task errada; duplicado; resposta tardia; sem origem. Resposta tardia não substitui estado reconciliado nem contorna o orquestrador.

## IMP-013 — Validar envelope

Entrada: resultado não confiável. Validar schema/versionamento, IDs, estado, tamanho e campos obrigatórios antes de validar conteúdo. Saída: `EnvelopeValid` ou `EnvelopeInvalid`. JSON sintaticamente válido não é conhecimento persistível. Testes: schema correto; campo em falta; ID trocado; campo extra perigoso; payload truncado; versão incompatível. Schema exato: **POR DEFINIR**.

## IMP-014 — Validar conteúdo

Entrada: envelope válido e original acessível. Efetuar verificações estruturais e de coerência mensuráveis; detetar extrações vazias/incompletas quando possível, preservando avisos e evidência. Não prometer fidelidade perfeita: `sanity check ≠ prova de conversão perfeita`. Saída: `ContentValidation(evidence, warnings, failures)`. Testes: boa extração; vazia; página perdida detetável; estrutura inválida; tabela corrompida; conteúdo suspeito. Métricas e limiares: **POR DEFINIR**.

## IMP-015 — Classificar

Entrada: `ContentValidation`. Aplicar regras determinísticas configuradas: suficiente → `READY`; incerteza relevante → `REVIEW`; inutilizável → `FAILED`; sempre com razões. Não atribuir aprovação à IA. Saída: classificação de conteúdo, não commit. Testes: fronteiras; mesma entrada e mesmas regras → mesma classificação; ausência de evidência não gera READY; razões auditáveis. Critérios concretos: **POR DEFINIR**. Transições: READY → 016; REVIEW → 021; FAILED → 022.

## IMP-016 — Criar representação Creative

Entrada: exclusivamente `READY` válido com os IDs desta operação. Construir candidato a documento/blocos de trabalho com IDs estáveis e ligação ao anexo/original; não persistir fora da cadeia de eventos nem promover. Saída: candidato a persistência Creative. `REVIEW` não entra automaticamente neste IMP; eventual aceitação posterior requer contrato próprio. Testes: conteúdo e IDs; ligação ao original; nenhuma promoção; retry não duplica; REVIEW recusado.

## IMP-017 — Criar proveniência

Entrada: candidato de representação e cadeia da operação. Construir registo de origem, anexo, ferramenta/versão, transformação, operation ID e evidência relevante, permitindo traçar bloco → transformação → ferramenta → attachment → original. Saída: `ProvenanceRecord`. Testes: cadeia completa; ferramenta desconhecida; referência quebrada; evidência externa congelada para replay; nenhuma relação inventada.

## IMP-018 — Criar eventos necessários

Entrada: mutação Creative preparada e proveniência. Preparar eventos autoritativos versionados, com IDs e ordem determinísticos para aplicação e replay. Saída: lote válido de eventos, ainda distinguível de commit confirmado. Não chamar Web/IA/plugin no replay. Testes: schema/versão; ordem; duplicação; evento inválido; replay determinístico; evidência suficiente congelada. Aplicam-se também os eventos necessários às mutações autoritativas anteriores, conforme contrato G10 ainda **POR DEFINIR**.

## IMP-019 — Materializar estado

Entrada: eventos autoritativos válidos. Aplicar deterministicamente a SQLite/Markdown e produzir recibos; não pressupor atomicidade conjunta entre SQLite, filesystem e log. Saída: `MaterializationReceipt` ou `COMMITTED`/`NOT_COMMITTED`/`RECOVERY_REQUIRED` conforme evidência e protocolo. Um estado incerto bloqueia novas mutações. Testes: normal; crash antes/durante/depois; retry sem duplicação; recibo sem estado; hash do estado autoritativo canonizado igual ao replay. Protocolo de gravação/reconciliação: **POR DEFINIR**.

## IMP-020 — Atualizar derivados

Entrada: materialização confirmada. Atualizar FTS5/caches; se falhar, assinalar `DerivativesDirty` e permitir reconstrução sem alterar conhecimento autoritativo. Saída: `DerivativesUpdated` ou `DerivativesDirty`. Testes: FTS apagado; reconstrução; crash; índice corrupto; estado autoritativo inalterado. Política de exposição de pesquisa com índice sujo: **POR DEFINIR**.

## IMP-021 — Apresentar resultado

Entrada: resultado final de operação confirmada, `REVIEW`, falha, ou derivados sujos conforme estado permitido. Mostrar na Folha linguagem simples, por exemplo “Livro.epub — Importado” somente após commit confirmado, ou “Livro.epub — Precisa de verificação” em REVIEW. Não mostrar IDs/Markdown/SQL por defeito; apresentação não é aprovação. Testes: READY com commit; REVIEW sem Creative; falha sem falso “Importado”; original acessível segundo política; fechar/reabrir UI não altera estado; `DerivativesDirty` não apaga conteúdo.

## IMP-022 — Tratar falha

Entrada: falha de conteúdo de IMP-015 ou falha técnica de qualquer IMP. Identificar etapa e razões, preservar evidência necessária, impedir falso sucesso e determinar `FAILED`, `RETRYABLE` ou `RECOVERY_REQUIRED`. Não corrigir conteúdo silenciosamente. `RETRYABLE` requer prova de segurança e idempotência para a operação; incerteza sobre commit exige reconciliação. Saída: estado operacional e destino explícito para apresentação, retry autorizado ou IMP-023. Testes: falha de conteúdo versus técnica; vários pontos; erro desconhecido; retry; original preservado; nenhum status falso.

## IMP-023 — Reconciliar interrupção

Entrada: operação incompleta detetada no arranque ou verificação. Ler `operation_id`, eventos, recibos, materialização e artefactos; determinar `COMMITTED`, `NOT_COMMITTED` ou `RECOVERY_REQUIRED` sem chamar novamente adaptador/Web/IA. Neste último estado bloquear mutações até resolução fundamentada. Testes: crash em vários pontos; recibo sem estado; estado sem recibo; evento parcial; replay; idempotência; operação sem prova suficiente permanece bloqueada. Reconciliação tem de considerar mutações desde IMP-003, não apenas IMP-019.

## IMP-024 — Pedido de eliminação do original

Entrada: pedido explícito da pessoa relativo a anexo concreto, posterior e separado da importação. Resolver ID e alvo, verificar existência, referências e consequências; apresentar proposta precisa. Saída: `DeletionProposal`; nada é eliminado. Testes: existente; inexistente; várias referências; duplicado binário exato; semelhante semanticamente; ambiguidades não adivinhadas. Retenção legal/backup e política de ficheiros: **POR DEFINIR**.

## IMP-025 — Autorização humana

Entrada: proposta e decisão humana explícita. Confirmar alvo, contexto e atualidade; registar decisão autoritativa. Saída: `DeletionApproved` ou `DeletionRejected`. Silêncio, timeout, plugin e IA nunca aprovam. Testes: aprovação; rejeição; proposta expirada; ID divergente; duplo clique; decisão repetida; aprovação não alargada a outros anexos.

## IMP-026 — Eliminação autorizada

Entrada: aprovação válida e específica. Revalidar autorização e alvo, usar operação identificada, eliminar exclusivamente o original autorizado, preservar genealogia/eventos/conhecimento que devam sobreviver e produzir recibo; falha não é sucesso. Saída: `OriginalDeleted` ou estado recuperável/bloqueado. Testes: eliminação correta; crash; alvo desaparecido; autorização reutilizada recusada; referências coerentes; Creative/Canonical não eliminados; nenhum outro attachment afetado. Precisar o significado operacional de “original” quando há entrada, quarentena e cópias de backup: **POR DEFINIR** antes da implementação.

## Orquestração e portões

Um IMP não chama arbitrariamente outro. Recebe a entrada contratada e produz saída tipada/falha. O orquestrador verifica IDs, estado e regras e só então escolhe a transição permitida. Caminhos de falha/reconciliação são transversais; IMP-024–026 não são continuação automática de IMP-021.

Portão 1 — **Especificação verificada**: casos, pré-condições, saídas, transições, idempotência, falhas e invariantes são revistos sequencialmente para cada IMP. Se algum ponto estiver POR DEFINIR e for necessário para decidir comportamento, o portão permanece fechado; corrigir e repetir antes do próximo IMP.

Portão 2 — **Implementação testada**: só se atribui após escrever e executar testes reais com sucesso. Nada neste documento declara testes executados ou autoriza programar lacunas.

Cabeçalho obrigatório de tarefa futura:

```
text
```

`ARQUITETURA: CONGELADA ESCOPO: Implementar exclusivamente IMP-XXX. NÃO AUTORIZADO: alterar arquitetura; implementar IMP futuros; criar decisões  de negócio; alterar T1–T6; substituir tecnologias sem autorização;  refatorar módulos fora do escopo; interpretar ambiguidades silenciosamente. SE A ESPECIFICAÇÃO FOR INSUFICIENTE: PARAR, identificar exatamente  a informação em falta, não inventar comportamento. PORTÃO: testes do IMP atual passam antes do seguinte.`

A família está consolidada como especificação funcional corrigida. Os pontos **POR DEFINIR** são lacunas explícitas que têm de ser decididas e testadas antes de declarar cada contrato pronto para programação. Não equivale a aprovação da implementação, nem a fecho do Catálogo Mestre de todas as famílias do Cérebro.

---
