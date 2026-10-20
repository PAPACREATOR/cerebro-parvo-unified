# Comparação documental — alvo F4 técnica

**Nota posterior — 2026-09-22:** esta comparação conserva o estado à data da sua revisão. A correção vigente de Pedro fixa dois cofres separados, final com Markdown + SQLite interno vivo e outro SQLite espelhado; utilizador escreve normalmente no Logseq criativo. As afirmações antigas de um único SQLite espelho/estado e as menções a SQLCipher como requisito não são operacionais; ver Constituição e Arquitetura v0.3.

Revisto em 2026-09-22. Pedro Alexandre Caldas Coelho confirmou expressamente: a fase 4 pretendida é a **F4 do Plano Mestre (IA efémera)**. Esta auditoria não altera Constituição/Arquitetura e não certifica código, licenças, autoria ou funcionamento.

## Proveniência e cobertura

- Anexo recebido e arquivado como `fontes/recebidas-2026-09-22/F12-Plano-Mestre-Nexus.txt`, 41 016 bytes, SHA-256 `00416720EEFD0F05420A5FA6CB6B6174CC507BCB8F473A12CA67BF79D093E5EE`. É colagem de conversas e propostas; data de receção conhecida, datas originais dos excertos não certificadas.
- Comparados os documentos de orientação da raiz, duas tarefas, 11 documentos numerados e quatro notas/minutas jurídicas. O acervo integral de `fontes/` e as 2 431 entradas inventariadas de D: **não** foram relidos semanticamente nesta revisão.
- Precedência: decisão atual explícita de Pedro sobre âmbito; Constituição/Arquitetura para invariantes; SPEC fechada para execução; textos históricos como evidência de evolução, não instrução automática.

## Diferenças e tratamento

| Tema | Diferença entre fontes | Tratamento atual |
| --- | --- | --- |
| Numeração | `documentacao/04` define fase 4 funcional = quatro módulos; F12 define F4 = IA efémera. O plano operacional anterior adotou a leitura errada. | **F4 técnica** confirmada por Pedro; plano funcional preservado como histórico, quatro módulos fora do requisito atual. |
| “Protótipo” | F12 só chama completo ao sistema F8/F9; Pedro quer protótipo em F4. | Chamar **protótipo técnico limitado F4**, nunca Alpha completo. |
| F0 | F12 acrescenta versionamento, pureza e idempotência, mas um excerto usa `dedup_id` derivado do payload e outro `eventId`. | Manter `event_id` central conforme Constituição/SPEC; hash de payload isolado pode suprimir duas ocorrências legítimas iguais. Dedup externo F3 tem contrato próprio. |
| F2 | F12 separa Working Memory/Logseq/Vault; fluxograma colado contém “delete Logseq” ambíguo. | Não interpretar como apagar dados do Logseq. TTL aplica-se à memória temporária; originais preservados. |
| Instalação | F12 sugere instalar todos os componentes antes de F0; plano de instalação atual é faseado. | Verificar cada componente antes da fase que o usa, com versão/licença/teste. Diferença de sequência, sem mudar arquitetura. |
| Entrada inicial | Pedro exige extrator/organizador para Markdown e regras; F12 não o detalha. | Dependência transversal de onboarding, uma vez por fonte, sem renumerar o motor. Cobertura por formato testada, originais preservados. |
| F3 | Staging, hash, proveniência, isolamento e outbox/retry em F12. | Compatível; Activepieces não escreve no Vault. |
| F4 | IA opcional, sem capacidade, contexto mínimo, output validado, replay sem nova chamada. | Compatível. Reproduz-se o **resultado registado**, não uma geração idêntica garantida. Auditoria não autoriza contexto confidencial em claro. |
| F5–F9 | Sandbox, proatividade, domínios, stress e Alpha. | Backlog histórico, sem implementação autorizada nesta etapa. |
| Certeza | F12 contém percentagens especulativas e frases “matematicamente rigoroso”/“imune”. | Não são previsões calibradas nem garantias. Aceitação requer testes reais com escopo e resultados. |
| Nome | F12 diz Nexus. | Cérebro Independente é o nome atual; Nexus histórico. |

## Estado e faltas para F4

GitHub privado ainda não criado/ligado; Cursor/pytest não confirmados; sem código F0 validado. Faltam versões/licenças exatas de Logseq, SQLCipher, Activepieces, Restic e runtime/modelo; amostras artificiais do extrator; SPECs F0–F4 executadas com regressão e PASS/FAIL. A chave Google antiga apareceu no chat e precisa de rotação antes de qualquer chamada API. Não houve login, compra ou teste do produto nesta revisão.

O F12 foi arquivado sem editar o original. Em divergência futura, registar data, fonte, decisão de Pedro e efeito. Não reescrever documentos históricos como se sempre tivessem concordado.
