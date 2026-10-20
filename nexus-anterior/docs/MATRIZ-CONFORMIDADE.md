> **Documento histórico datado.** Conserva a análise desta fase e não define o runtime atual. Para implementação vigente consultar [CEREBRO_ARCHITECTURE.md](../CEREBRO_ARCHITECTURE.md), [DECISIONS.md](../DECISIONS.md) e [PONTO-DE-SITUACAO](../nexus/docs/PONTO-DE-SITUACAO.md).

# Matriz de conformidade — 27-09-2026

Fontes: [prompt mestre](baseline/CEREBRO_PROMPT_MESTRE_CURSOR_2026-09-26.md), contratos corrigidos Parte III e código candidato importado. Mapeamento abaixo é análise de cobertura, não nova atribuição normativa de módulos.

Estados: EXISTE = artefacto localizado; PARCIAL = parte implementada/documentada, sem contrato integral demonstrado; AUSENTE = não localizado neste candidato; POR DEFINIR = decisão aberta; CONTRADIZ = divergência localizada. Os resultados dos 34 testes estão na evidência, sem transformar cobertura parcial em PASS do módulo.

## M1–M14

| Módulo | Responsabilidade | Estado do código | Observado | IMP/família relacionada | Teste fornecido relevante | Falta demonstrar |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | Identidade | PARCIAL | UUID/temp_ref e operação/anexo | 001, 003–004 | test_distinct_receptions_distinct_operations; test_correlated_ids_must_be_valid_uuid | Persistência, colisão/retry correlacionado e mover/renomear não demonstrados |
| M2 | Documentos/blocos | PARCIAL | ReceivedInput e candidato em dict | 001, 016 | test_imp001_007 | Modelo documental/blocos persistente ausente |
| M3 | Versões/genealogia | AUSENTE | Metadados pontuais não constituem genealogia | 017–019 (parcial de família) | Sem teste completo | História/versionamento consultável e preservação evolutiva |
| M4 | Creative | PARCIAL | build_creative_candidate | 016 | test_review_cannot_enter_creative; test_creative_requires_matching_operation_attachment | Sem persistência/replay; IMP-019 bloqueado |
| M5 | Canonical | AUSENTE | Nenhuma promoção implementada | Outra família a especificar | Sem teste funcional | Preservação de versões aprovadas e promoção |
| M6 | Portão humano | PARCIAL | authorize_deletion restrito a alvo em memória | 024–026 | test_authorization_target_cannot_expand | Atualidade/expiração, origem humana autenticada, registo e não reutilização |
| M7 | Relações | AUSENTE | Refs simples não são motor de relações | Outra família a especificar | Sem teste completo | Identidade independente de paths e relações persistentes |
| M8 | Proveniência/fontes | PARCIAL | provenance com tool id/version | 017 | test_provenance_requires_tool_identity | Cadeia por bloco, evidência congelada e referência quebrada |
| M9 | Contradições | AUSENTE | Conflito de recibos em reconcile não é conhecimento contraditório | Outra família a especificar | Sem teste de contradição epistemológica | Representar/coexistir contradições sem escolha automática |
| M10 | Pesquisa/recuperação | AUSENTE | Não há FTS/pesquisa real | 020 parcial; outras famílias | Sem teste de pesquisa | Construir/reconstruir e pesquisar derivados |
| M11 | Regras | PARCIAL | Policy e classificação por callback | 002, 009–015 | test_undefined_policy_blocks; test_classifier_cannot_return_arbitrary_value | Regras versionadas/invariantes/heurísticas não completas |
| M12 | EventLog/auditoria | PARCIAL | prepare_events gera estrutura em memória | 018–019 | test_materialize_still_blocked | Log persistente, G10, replay determinístico, ordem e idempotência |
| M13 | Integridade/recuperação | PARCIAL | quarantine/hash/reconcile mínimo | 005–007, 022–023 | test_existing_quarantine_with_wrong_bytes_must_not_succeed; test_reconcile_conflicting_evidence_fails_closed | Crash real, recibos, SQLite+filesystem, backup/restore e concorrência |
| M14 | Coordenação/iniciativa | PARCIAL | Seleção de adaptador e callback executor | 009–011, 022–023 | test_adapter_ambiguity_fails_closed; test_activepieces_exception_never_becomes_success | Sem orquestrador de estados persistente nem iniciativa rastreável completa |

## IMP-001–026

| IMP | Responsabilidade | Função localizada | Estado | Limite observado |
| --- | --- | --- | --- | --- |
| 001 | Receber | receive_file | PARCIAL | Referencia Path; não demonstra stream/Folha/interrupção |
| 002 | Validar | validate_input | PARCIAL / POR DEFINIR | Limites/vazio configuráveis; integridade de transferência ainda incompleta |
| 003 | operation_id | create_operation | PARCIAL / POR DEFINIR | G10/persistência e prova de correlação; UUID novo não é replay |
| 004 | attachment_id | create_attachment | PARCIAL / POR DEFINIR | G10; identidade preservada ao mover/renomear não testada |
| 005 | Quarentena | quarantine | PARCIAL / POR DEFINIR | Ficheiro parcial e replace; sem recibos/crash real; G10 |
| 006 | Hash | sha256_file | PARCIAL | Vetor simples coberto; falta completar negativos/leitura/vazio |
| 007 | Duplicação exata | exact_duplicate/byte_equal | PARCIAL | Bytes e colisão simulada cobertos; falta toda a matriz contratual |
| 008 | Formato | detect_format | PARCIAL / POR DEFINIR | Assinaturas mínimas; política/confiança e todos formatos não cobertos |
| 009 | Adaptador | select_adapter | PARCIAL / POR DEFINIR | Registry simples; política de versões/prioridade e ausência |
| 010 | Tarefa | create_task | PARCIAL / POR DEFINIR | Envelope mínimo; retry cria task_id novo, contrato requer idempotência lógica |
| 011 | Executar | execute_via_activepieces | PARCIAL / POR DEFINIR | Callback apenas; timeout/sandbox/versão/limites não impostos pela função |
| 012 | Resultado | receive_untrusted_result | PARCIAL | Correlação básica; versão, tardio e estado reconciliado não verificados |
| 013 | Envelope | validate_envelope | PARCIAL / POR DEFINIR | Campos/limite/negação de campos de autoridade; schema/versionamento por fechar |
| 014 | Conteúdo | validate_content | PARCIAL / POR DEFINIR | Presença/vazio; perdas de página/tabela/formato não verificadas |
| 015 | Classificar | classify_content | PARCIAL / POR DEFINIR | Enum/callback; regras/limiares e razões normativas não fechados |
| 016 | Candidato Creative | build_creative_candidate | PARCIAL | READY e correlação; estabilidade de candidato no retry não demonstrada |
| 017 | Proveniência | provenance | PARCIAL | Metadados mínimos; cadeia completa e referências não verificadas |
| 018 | Eventos | prepare_events | PARCIAL / POR DEFINIR | Estrutura em memória; G10/log/replay ausentes |
| 019 | Materializar | materialize | POR DEFINIR / BLOQUEADO | PolicyUndefined; não materializa SQLite/Markdown |
| 020 | Derivados | derivative_status | PARCIAL / POR DEFINIR | Apenas etiqueta de estado; FTS/rebuild ausentes |
| 021 | Apresentar | present | PARCIAL | Strings; sem Folha/reabertura/estado persistente |
| 022 | Falha | failure | PARCIAL | Classifica flags; não prova segurança do retry nem registo |
| 023 | Reconciliar | reconcile | PARCIAL | Recebe booleans de evidência; não lê/verifica recibos e estado real |
| 024 | Propor eliminação | deletion_proposal | PARCIAL / POR DEFINIR | Pedido em memória; sem resolução real/retencão/backup |
| 025 | Autorizar | authorize_deletion | PARCIAL | Alvo e existência; origem/atualidade/uso único não demonstrados |
| 026 | Eliminar | delete_authorized_original | POR DEFINIR / BLOQUEADO | PolicyUndefined; eliminação não executada |

## Portões globais

| Verificação | Estado |
| --- | --- |
| Fontes/baseline e histórico | EXISTE; integridade conferida por script |
| Suite fornecida (34 testes) | PASS local; evidência em auditoria |
| Contrato completo IMP-001 | PARCIAL; não fechado |
| T1–T10 e E2E-01–15 completos | NOT RUN |
| M1–M14 integrados | NOT RUN |
| GitHub anterior versus baseline 26/09 | CONTRADIZ em interface/Activepieces/IA; orientação reconciliada, originais preservados |

[Resultados reais](../auditoria/RESULTADOS.md) · [Pendências](PENDENCIAS.md).
