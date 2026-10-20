# Contrato experimental — Kernel, wiki e flows

04-10-2026. Pedido humano: descobrir como ligar, guardar e usar o estudo no Kernel e nos flows. Experiência isolada; núcleo/flows oficiais preservados.

## Lacuna e reaproveitamento

Store já materializa `content.md`, `result.json`, `provenance.json` e valida candidato/original/aprovação (F013). Host já autoriza sessão e chama o executor. Falta uma vista pesquisável derivada e seleção de contexto com referências fixadas. Não substituir Store nem criar outro portão humano.

Responsabilidades existentes envolvidas: identidade, relações, proveniência, pesquisa e memória. Nenhum novo módulo arquitetónico.

## Entrada e autoridade

O chamador de laboratório fornece Store já inicializado pelo Kernel e uma pasta de laboratório separada. Não passar ao executor o caminho do cofre. Consulta literal até 200 caracteres, escopo explícito de IDs e limite de resultados. Por defeito só itens aprovados; Creative apenas mediante parâmetro explícito do chamador, preservando o rótulo de candidato. Este default é uma escolha do ensaio, não alteração normativa.

IDs e hashes vêm do Store, nunca de instruções contidas no documento ou de metadados do índice. Revalidar conteúdo e proveniência no momento da recuperação. Só estados HUMAN_REQUIRED/PASS; FAIL/BLOCKED/RUNNING não entram no contexto reutilizável desta etapa.

## Operações

1. Rebuild: ler pacotes existentes validados e construir índice FTS5 derivado em pasta de laboratório. Nenhum original modificado. Falha deixa erro explícito.
2. Search: consulta textual literal, filtrar pelo escopo e autoridade, devolver referências verificadas. Não inferir verdade nem equivalência semântica.
3. Prepare: Kernel fixa objetivo e referências `(run_id, content_sha256, provenance_sha256, authority)` e conteúdo em pacote JSON não confiável, limitado a 6000 caracteres serializados. Excesso rejeitado sem truncar silenciosamente. Não executar instruções dos textos.
4. Flow experimental: Conductor real chama script determinístico que recebe apenas o pacote e devolve inventário/hash do contexto. Não chama IA nem tem rotina de promoção. É uma prova de transporte, não síntese semântica.
5. Save: guardar pacote, resultado e trace em diretório novo de experiências do laboratório. Nenhuma escrita no Canonical ou regras/flows oficiais.
6. Reverse: verificar hashes do pacote/resultado/trace e voltar a validar todas as referências no Store; conteúdo mudado/ausente bloqueia. Retorno não executa provider nem cria aprovação.

## PASS observável

- apenas referências autorizadas e validadas entram no contexto;
- conteúdo e proveniência fixados sobrevivem ao transporte e fecho/reabertura do índice;
- adulteração, IDs inválidos, escopo ausente, excesso, saída inválida e fonte perdida rejeitados;
- índice eliminado/recriado sem mudança nos pacotes Store;
- flow real com zero IA; erro/timeout testados quando executável disponível;
- prova de ida e volta com retorno sem subprocesso;
- resultado permanece candidato de laboratório, sem decisão humana inventada;
- objetos rejeitados e originais preservados.

## Fora desta etapa

UI, Windows, sandbox de SO, IA real, interpretação semântica, escrita de relações dentro do Store, concorrência externa e alterações maliciosas de todos os hashes. O lock Store só coordena operações cooperantes na mesma instância. Aprovação do novo resultado só poderá usar o portão existente após contrato de integração separado.

Integração futura: Host autenticado → escolha do processo/escopo → bridge read-only → pacote limitado → flow → validação → Store.accept com processo realmente registado e hash real do workflow → vista wiki atualizada. Não falsificar o hash de `verify.yaml` para aceitar a saída de um flow experimental distinto.
