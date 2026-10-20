# Plano ativo — F-1 a F4 do Plano Mestre

Decisão de Pedro Alexandre Caldas Coelho em 2026-09-22: “fase 4” significa **F4 técnica (IA efémera, sem capacidade de agir)** do anexo F12, não a fase 4 funcional dos quatro módulos. Fonte arquivada: `fontes/recebidas-2026-09-22/F12-Plano-Mestre-Nexus.txt`. Nexus é nome histórico; o atual é Cérebro Independente. **Correção posterior:** Constituição e Arquitetura estão em v0.3: dois cofres e dois SQLite distintos; o alvo F4 não foi renumerado.

O alvo é um **protótipo técnico limitado até F4**. O “Alpha completo” da fonte histórica exige F5–F9; não o declarar em F4. Os quatro módulos do plano funcional não são requisito de F4. A interface final, IA com ações, domínios e produto comercial ficam fora deste âmbito.

## Método e equipa

Cada tarefa: SPEC fechada → implementação mínima → testes executados → evidências → revisão independente → PASS/FAIL decidido por Pedro. Repetir a regressão anterior em cada fase. Codex prepara contratos e revê; Cursor Hobby é o único escritor automático previsto por tarefa, se houver acesso/quota. Copilot Free e Gemini só podem dar apoio pontual com contexto aprovado, sem escrita concorrente. Não fazer compra, commit, push ou avançar fase automaticamente.

| Fase | Entrega mínima | Verificação de saída |
| --- | --- | --- |
| F-1 — fundação | Inventário, versões, Python/testes, Git local e GitHub **privado**. Verificar Logseq Classic/File Graph, SQLite/FTS5, Activepieces, Restic e runtime IA antes da fase que os usa, com licença e teste isolado. SQLCipher deixou de ser requisito do cofre final; proteção do Markdown em repouso é decisão de segurança separada. | Ambiente reproduzível; backup/restauro de dados artificiais; nenhum segredo ou dado pessoal no Git. A fonte propõe instalar tudo de início; o sequenciamento atual é por necessidade, sem omitir testes. |
| F0 — motor | Event versionado, State, relógio lógico, Transition pura, EventLog, hash chain, snapshot, replay e idempotência central por `event_id`. | 10 000 eventos controlados com hash igual após replay/restart; snapshot intermediário; duplicados, inválidos, corrupção e crash testados. 100% refere-se **à suíte definida**, não a garantia universal. |
| F1 — cognição sem IA | Working Memory/TTL, regras, comparação, scoring, routing, pendências e Gate 0–3 (`ALLOW/DENY/ASK`). | Cenários artificiais de risco, prioridade, conflito, TTL e replay; **zero chamadas IA** nesta fase. |
| F2 — memórias | Usar Logseq Classic/File Graph nativamente em grafo artificial; pessoa escreve normalmente, sem input Markdown. Cofre final separado com Markdown gerido pelo sistema **e SQLite interno vivo**; **segundo SQLite espelhado**. Fechar primeiro autoridade por campo e contrato do espelho, sem pressupor que o interno é cache. Exige SPEC nova antes de implementação. | Item/versão só entra no final após aprovação expressa; sem aprovação permanece no criativo, podendo Pedro mantê-lo só ali ou pedir apagamento. Repetição da decisão é idempotente; falha entre ficheiro, base interna e espelho é reconciliada; original não é apagado automaticamente. |
| F3 — exterior | Activepieces → staging/quarentena → hash/proveniência/dedup → evento Core, com outbox/retry e confirmação. | RSS/webhook/HTTP sintéticos, repetições, falhas e reinício; sem perda silenciosa nem escrita direta no Vault. |
| F4 — IA efémera | AIRequest/AIContext/AIResponse/AIProvider desacoplados do modelo; chamada só **sob pedido explícito da pessoa** ou para um **evento concreto necessário** que as regras não resolvem. Não chamar em cada evento/tick. Contexto mínimo, capacidades vazias, saída estruturada validada convertida em evento; contexto da chamada terminado/revogado após uso. | Conjunto inicial de 100 tarefas determinísticas + 100 generativas artificiais; medir IA desnecessária, testar alucinação, saída inválida e fornecedor offline. Replay reutiliza **AI_RESULT gravado**, sem voltar a chamar o modelo. Registar modelo/versão e hashes sem segredos em claro. |

## Dependência transversal: extrator inicial

O extrator/organizador corre uma vez no início **por fonte** e termina. Antes de colocar dados pessoais: inventariar formatos, copiar para staging, converter o subconjunto suportado para Markdown, preservar originais/anexos, calcular hashes, registar proveniência e falhas por item e retomar sem duplicar. Entrada no cofre criativo segue regras de importação decididas por Pedro; **entrada no cofre final exige sempre aprovação expressa do item/versão**. “Qualquer formato” é meta de catálogo expansível, não suporte universal demonstrado. Pedro escolhe o lote real depois dos testes artificiais. Isto não renumera F0–F4.

## GitHub privado

O remoto recebe apenas código, SPECs e documentação revista para partilha. Excluir `fontes/`, `juridico/`, acervo D:, memória interna, bases, runtime, backups, chaves e dados pessoais. Antes do primeiro push, confirmar proprietário, visibilidade `private`, lista exata de ficheiros e histórico do commit. Privado não equivale a NDA, patente ou exclusividade perante GitHub. O remoto e o push **ainda não foram criados** nesta sessão.

## Critério “protótipo F4”

F-1–F4 com PASS documentado nos testes definidos; vertical local com dados artificiais; núcleo determinístico utilizável com IA desligada; limitações e licenças registadas. Não confundir com Alpha F9, segurança F5 ou domínios F7.
