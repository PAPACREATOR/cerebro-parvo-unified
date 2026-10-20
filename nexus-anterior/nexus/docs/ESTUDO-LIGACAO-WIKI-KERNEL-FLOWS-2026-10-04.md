# Como o Kernel usa a wiki nos flows

> Nota de estado (04-10-2026): o transporte Conductor/context_flow.yaml descrito abaixo foi um laboratório e foi removido do código ativo. Mantêm-se os resultados sobre wiki derivada, FTS5, contexto limitado, proveniência e navegação bidirecional. A continuação ativa é Kernel Python + MCP.\n\n
04-10-2026. Estudo interpretado e primeira ligação experimental implementada.
Base local: `74f6857`; branch `lab-wiki-complemento-20261004`. Sem envio remoto nesta sessão.

## Conclusão técnica

Não é necessário dar à wiki um cérebro próprio. O Kernel usa-a como vista derivada dos resultados que o Store já conserva. Seleciona um conjunto de referências permitido, verifica os pacotes de origem, fixa versões por hashes e entrega ao flow apenas o contexto necessário. O novo resultado conserva as referências utilizadas e regressa como candidato.

A organização tem duas camadas: identidade/versão/proveniência ficam no armazenamento existente; pesquisa e navegação são derivadas e reconstruíveis. O laboratório anterior demonstrou volume sintético. Esta etapa testa a ligação aos pacotes reais do Store e ao executor Conductor da revisão já fixada no repositório.

## Aproveitamento concreto do código existente

| Ponto existente | Como é aproveitado | Limite observado |
|---|---|---|
| `Store.accept` | Guarda Markdown, resultado e proveniência de um processo registado | Não aceitar saída de flow experimental fingindo que veio do verify oficial |
| `Store.check_candidate` | Valida candidato, pedido, original e proveniência antes de recuperar contexto | Integridade não prova verdade factual |
| `Store.check_commit` | Valida pacote aprovado e decisão humana vinculada | Ler Canonical não aprova o resultado seguinte |
| `Host.authorize` | Deve continuar a verificar sessão antes de pesquisa/seleção exposta à Folha | Bridge atual é chamada interna de laboratório, não endpoint público |
| `conductor_runner.execute` | Executa o flow de transporte real sem provider de IA | Script com exit != 0 nem sempre gera exceção; validar envelope/resultado |
| `notebook.prepare_source` | Impõe limite real de 6000 caracteres no input atual | Não enviar arquivo inteiro nem truncar fontes silenciosamente |
| Human Gate existente | Continua a ser o único percurso de promoção | Laboratório não acrescenta mecanismo de aprovação |

## Circuito que já correu no laboratório

1. Criar pacotes sintéticos com **Store real**, incluindo candidatos e aprovação humana simulada apenas nos fixtures de teste.
2. Construir um índice FTS5 fora do Store, lendo apenas pacotes válidos. Pacotes inválidos são enumerados em `rejected`, não apagados.
3. Pesquisar literalmente dentro de IDs autorizados. O índice só sugere referências: os bytes de contexto voltam a ser lidos e validados no Store.
4. Preparar JSON com objetivo, IDs, processo de origem, hashes de conteúdo/proveniência/original, domínio de autoridade e conteúdo. Máximo oito fontes e 6000 caracteres serializados; overflow rejeitado.
5. Conductor real executa `context_flow.yaml`, que chama o inventário determinístico. Recebe o caminho do pacote temporário, não o caminho do cofre.
6. Validar a saída contra o contrato e guardar contexto + resultado + trace + manifesto numa experiência nova de laboratório. A classificação é `LAB_CANDIDATE`.
7. Navegar resultado → fontes com `reverse`; fonte → usos com `uses`. O retorno revalida hashes e origem, sem executar ferramenta, IA ou criar aprovação.

O flow atual demonstra transporte e rastreabilidade: não faz síntese semântica e não chama Open Notebook. O texto do contexto permanece dado não confiável; o inventário não executa comandos ou instruções nele contidos. Isto não é uma prova de resistência a prompt injection de um modelo futuro.

## O que significa organizar

- **Por processo:** cada referência conserva `process_id`; distingue verificação, interpretação e outras famílias já registadas.
- **Por origem e utilização:** cada novo ensaio conserva as referências utilizadas; é possível voltar à origem ou descobrir os usos dessa origem.
- **Por autoridade:** Creative é rotulado como candidato; Canonical mantém o vínculo à decisão humana original. O laboratório exclui Creative por defeito na pesquisa; o Kernel pode incluí-lo explicitamente num fluxo exploratório.
- **Por conteúdo:** FTS5 oferece pesquisa lexical; não faz classificação semântica, inferência ou comparação de verdade.
- **Por versão:** esta etapa fixa hashes do pacote existente. Se fonte/proveniência/autoridade mudar depois da seleção, o contexto é rejeitado e deve ser preparado novamente. Ainda não existe editor de histórico multiversão na bridge.

Não se deve fabricar automaticamente categorias temáticas, resolver contradições por votação nem transformar um padrão aprendido num flow autorizado. Esses resultados são propostas quando dependem de interpretação.

## Onde ligar depois na versão oficial

Antes da execução, o Host autenticado deverá selecionar o processo e o escopo. A bridge devolve um pacote verificado e limitado. O executor trabalha apenas nesse pacote. No retorno, o Host valida a saída e usa `Store.accept` com o ID e hash do **processo realmente executado**. Só depois atualiza a vista wiki. A aprovação segue o portão humano existente.

Essa ligação exige um contrato adicional: request/contexto estruturado e referências de contexto no resultado/proveniência. O schema atual `request.json` só tem process/text/filename/attachment; não aceita um campo arbitrário `context`. Não esconder metadados de autoridade dentro do texto para contornar o schema.

Próximo microprocesso concreto: definir o envelope de contexto aceito pelo Host e o vínculo do novo resultado aos hashes consultados, testar resultado aceito/saída inválida/restart/timeout antes de registar uma nova receita. Não acrescentar `context_flow.yaml` experimental à lista oficial sem essa revisão.

## Falhas observadas e respetiva interpretação

1. Primeiro teste de adulteração de `trace.json` escreveu `{}` sobre um trace que já era `{}`. O teste não alterava bytes; foi corrigido para alterar realmente o conteúdo. Não era falha de integridade do produto.
2. Primeira expectativa para script inválido assumia que Conductor lançava exceção. O script saiu com erro, mas o executor retornou um envelope. O teste passou a verificar a fronteira relevante: a bridge rejeita essa saída e não grava uma experiência válida. O Store oficial também valida resultados; não se demonstrou bypass de Canonical.
3. Ferramenta inexistente e timeout foram exercitados no motor real. Retorno não executa provider. Interrupção simulada durante gravação deixa ficheiros para inspeção e não publica manifesto válido.

A execução inicial de 1097 casos terminou com 1096 PASS e um FAIL de expectativa do teste; a evidência foi preservada. A execução final está no relatório de evidência associado.

## Limites

Tudo decorreu em Linux, com Store e Conductor reais e conteúdo sintético. Windows, Folha/HTTP nova, IA real, síntese editorial, concorrência entre processos, power loss e integração oficial continuam NOT RUN. Bloqueio cooperante do Store e argumentos limitados não são sandbox de sistema operativo.

Os hashes detetam divergência contra referências conservadas; não protegem contra quem altera coerentemente todos os ficheiros e referências. `uses` percorre as experiências do laboratório e pára perante experiência inválida; ainda não é um índice incremental de grande escala. Consulta lexical não mede relevância semântica.

## Ficheiros e reprodução

- `nexus/lab/wiki/kernel_bridge.py`: leitura, índice, seleção, gravação experimental e retorno.
- `nexus/lab/wiki/context_packet.py`: contrato limitado e inventário determinístico.
- `nexus/lab/wiki/context_flow.yaml`: flow real de laboratório.
- `nexus/lab/wiki/test_kernel_bridge.py`: positivos, negativos, adulteração, limites, falha e 1024 variantes parametrizadas de pesquisa/escopo/autoridade.
- `nexus/lab/wiki/evidence/kernel-20261004/`: evidência e ambiente.

Comando: `python -m pytest nexus/lab/wiki/test_kernel_bridge.py -q`.
Dependências: `nexus/requirements-test.txt`, em ambiente isolado. As dependências transitivas observadas ficam em `environment.txt`.

Nenhum ficheiro do núcleo, manifesto de produção, lei, schema oficial ou flow oficial foi alterado. Esta experiência é uma ligação parcial comprovada, não uma declaração de produto concluído.
