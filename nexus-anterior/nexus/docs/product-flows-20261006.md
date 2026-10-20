# Nexus Local — percursos de produto e gates — 2026-10-06

Este documento regista a continuação técnica sem alterar a arquitetura congelada.
Não cria novas autoridades, módulos M1-M14, invariantes ou rotas públicas do Host.

## Regra transversal

A sequência comum é:

1. pedido humano;
2. Front Door determinístico;
3. seleção/validação das fontes aplicáveis;
4. comparação determinística quando há resultados independentes;
5. conflito => preservar e bloquear decisão automática;
6. acordo => entregar apenas ao especialista necessário;
7. resultado externo/IA => candidato sem autoridade;
8. Human Gate continua a ser a única promoção possível.

OpenNotebook NÃO é passagem obrigatória de todos os fluxos.

## Pesquisa web

Destino: pesquisa/fontes/proveniência.

Fluxo:
pedido -> parser -> pesquisa -> fontes -> hashes/proveniência -> comparação ->
resultado de pesquisa candidato.

Não passa automaticamente pelo OpenNotebook.
OpenNotebook só recebe posteriormente um conjunto de fontes já escolhido quando outra
função precisar de síntese/estrutura especializada.

Estado público do Host: ainda não existe processo `web`; deve ficar BLOCKED até ser
integrado sem alterar a política congelada.

## Escrita / livro

Destino: texto + molde LibreOffice existente.

Fluxo:
pedido -> fontes escolhidas -> escrita/revisão em microtarefas -> comparação/verificação ->
molde Writer existente -> ODT/PDF candidato.

OpenNotebook não é obrigatório para escrever ou pesquisar.
Pode ser chamado depois apenas para uma função especializada explicitamente pedida.

Já existe prova real do mecanismo Writer com molde fixo, páginas espelhadas,
viúvas/órfãs, keep-with-next e exportação PDF. O teste não redesenha estilos.

## Podcast

OpenNotebook é apropriado aqui como bancada especializada.

Fluxo:
pedido -> fontes escolhidas/verificadas -> pacote delimitado -> OpenNotebook ->
outline/transcrição/episódio -> áudio candidato -> revisão humana.

Nenhum conflito de fontes deve chegar ao Notebook.
Nenhum episódio tem autoridade Canonical.

## Podcast visual

Fluxo:
pedido -> fontes escolhidas/verificadas -> OpenNotebook -> podcast/áudio ->
imagem/avatar fornecido -> Wav2Lip -> FFmpeg -> MP4 candidato.

A fronteira existente do avatar:
- inputs contidos;
- hashes;
- output candidate;
- authority UNTRUSTED;
- sem promoção automática.

## Vídeo / documentário

Fluxo:
pedido -> pesquisa/escrita/fontes -> comparação -> pacote factual delimitado ->
OpenNotebook para guião/storyboard -> Forge para imagens de cenas ->
MoneyPrinterTurbo para montagem -> FFmpeg -> MP4 candidato.

MoneyPrinterTurbo:
- ferramenta subordinada;
- pin: 68eb5a68b93cfe338198b3dfb151f6d5ec2fe4e5;
- não é memória, cérebro ou autoridade;
- reutiliza o FFmpeg já instalado pelo Nexus;
- percurso documental sem TTS automático;
- sem áudio: vídeo silencioso para acabamento no Clipchamp;
- com áudio fornecido: usa custom-audio e Whisper apenas para legendas.

## Música

Destino: ACE-Step.

Entrada humana desejada:
- tema;
- letra ou indicação para criar letra;
- estilo;
- opcionalmente duração/BPM/tom/compasso.

Microtarefas:
1. resolver tema;
2. preparar letra estruturada;
3. preparar caption de estilo sem conflitos;
4. validar consistência letra/caption;
5. gerar parâmetros ACE-Step;
6. enviar ao ACE-Step;
7. guardar áudio como candidato;
8. comparar versões se forem geradas múltiplas;
9. escolha final é humana.

ACE-Step suporta nativamente caption + lyrics + duração/BPM/key/time-signature/language.
O Host público ainda não tem processo `music`; testes devem confirmar BLOCKED, nunca
fabricar PASS.

## Testes adicionados nesta fase

`nexus/tests/test_product_flows_5000.py`
- vídeo: 5.000 casos direcionais;
- podcast: 5.000;
- podcast visual: 5.000;
- livro: 5.000;
- música: 5.000;
- web: 5.000.
Total: 30.000 casos.

`nexus/tests/test_product_system_50000.py`
- 50.000 casos combinados;
- pedido humano;
- preservação byte-a-byte;
- comparação bidirecional de fontes;
- conflito impede entrega ao especialista;
- OpenNotebook apenas para vídeo/podcast/podcast visual;
- livro/música/web não são enviados ao Notebook por defeito;
- tentativa de autoridade em resultado externo é rejeitada;
- promoção continua ligada à decisão humana e ao hash exato do candidato.

O CI tem um job dedicado:
`Product flows — 6x5000 + whole system 50000`.

## Regra de evidência

Estes testes são determinísticos e verificam contratos/limites.
Não equivalem a 5.000 renders físicos de GPU, 5.000 podcasts reais ou 5.000 músicas
geradas. Renders físicos e chamadas reais são gates separados e devem ser declarados
como tal.

Nenhuma rota, lei ou estrutura congelada foi alterada para criar estes testes.
