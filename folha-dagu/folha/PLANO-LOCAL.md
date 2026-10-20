# Nexus local — contrato e estado

## Percurso

Folha existente → PowerShell e SQLite FTS5 → templates YAML → Dagu → ferramentas → resultado na Folha.

O determinismo aplica-se à seleção por regras, aos parâmetros e à sequência de verificações. Não significa que uma ferramenta generativa produza sempre a mesma obra nem que um resultado concluído esteja editorialmente aprovado.

## Blocos a concluir

- Base local: Folha, sessão, rascunho, catálogo, biblioteca, guardar texto, integridade e PDF. Implementada e testada.
- Memória: conservar leis e autoridade Creative/Canonical; migrar o conhecimento com prova de integridade, sem apagar originais. Proveniência dos novos resultados em implementação; migração anterior pendente.
- Texto e investigação: fontes completas, Wikipedia e fontes verificáveis, comparação no Open Notebook, resultados intermédios guardados, prompts próprios de cada ferramenta. Primeira ligação Open Notebook em implementação.
- Livro: estrutura e expansão por capítulo. Cada capítulo passa, por esta ordem, por revisão de ortografia, revisão de pontuação e revisão de lógica e estrutura. Só depois de todos os capítulos revistos se faz a revisão do livro inteiro, para continuidade e coerência entre capítulos, seguida do prompt de capa. Ordem confirmada pelo utilizador em 19-10-2026; as restantes regras pessoais devem ser recuperadas, nunca inventadas.
- Filme: investigação → guião → prompts de cena/música → geração de música e clips → montagem FFmpeg → MP4 completo. O FFmpeg junta os clips do Deforum, ajustando formatos e sincronização conforme a receita.
- Podcast visual: aproveitar o podcast do Open Notebook e a ferramenta de avatar existente; conservar áudio, imagem, vídeo e proveniência. MoneyPrinterTurbo é uma ferramenta separada, não um componente confirmado do Open Notebook.
- Arranque local: substituir o lançador antigo do Nexus sem alterar as ferramentas e respetivos ambientes. O lançador antigo ainda inicia serviços necessários.
- Limpeza final: somente restos do núcleo antigo e temporários comprovadamente dispensáveis, depois dos percursos funcionarem. Ferramentas, modelos, memórias e dados pessoais ficam.

## Verificação das ferramentas em 19-10-2026

Open Notebook local responde. Há um perfil `Nexus PT local curto`, linguagem pt-PT, três segmentos, modelo de texto Qwen3-1.7B e voz Piper pt-PT configurados. Isto confirma configuração, não uma nova geração de podcast.

A API ativa do Open Notebook não anuncia rotas de avatar ou MoneyPrinterTurbo. O avatar existe como worker separado em WSL e há ficheiros de testes anteriores; a ligação pela Folha ainda não foi demonstrada.

Deforum/Forge anuncia a API local. FFmpeg 9.0.2 está instalado. As ferramentas continuam como estavam; a migração substitui o núcleo Nexus.

O modelo de texto local consultado dispõe de 8192 tokens de contexto e um slot. Os microprocessos devem respeitar a capacidade real e conservar as fontes completas, sem cortes silenciosos. Uma tarefa pesada de cada vez.

## Estado do GitHub antes da mudança para trabalho apenas local

A base foi enviada para `feat/folha-dagu-shell`, commit `e36103bf314ae0022b376693b652c8b108f07ea7`, PR draft #5. A PR #4 de segurança tem os testes Windows verdes e estava sem conflitos. O merge não foi executado: a revisão automática de autorização falhou por limite de utilização. Não foi contornado.

A instrução humana posterior determinou continuar apenas no PC. Não voltar a fazer push/merge como requisito deste plano sem novo pedido.
