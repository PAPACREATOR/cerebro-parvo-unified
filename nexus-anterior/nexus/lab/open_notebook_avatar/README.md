# Open Notebook — capacidade local de avatar

Extensão opcional validada contra **Open Notebook 1.15.0**, source checkout
`lfnovo/open-notebook@315d5255af2a5132aada41c94d5c3c5dc8e837aa`.
Não reconstrói podcast, outline, transcript, speakers, TTS ou mistura de áudio.
Usa o áudio de um episódio existente e um retrato fornecido pelo operador.

`episódio Open Notebook → áudio validado → SFD → Wav2Lip → FFmpeg → MP4 + proveniência`

## Contrato e autoridade

- A API recebe ID do episódio e nome de retrato, não URLs/comandos/caminhos de cofres.
- O ID resolve pelo `PodcastEpisode` nativo e pelo resolvedor contido de áudio.
- Retrato JPEG/PNG: 96–2048 px por dimensão, até 20 MB; um rosto detetável.
- Áudio até 100 MB e 3600 segundos; WAV/MP3 e outros formatos reconhecidos pelo FFmpeg.
- CPU/CUDA explícito; batch inteiro 1–32; timeout de inferência 900 segundos.
- Inferência separada das dependências do Open Notebook; sem shell ou cache pickle.
- Pesos são provisionados na instalação, com hashes fixados; renderização offline.
- Resultado é **UNTRUSTED / candidate**, nunca promoção/publicação ou aprovação.
- PASS do envelope é validação técnica, não aprovação da qualidade de sincronização.
- Repetição com os mesmos inputs/versões recupera o vídeo; alterações geram novo ID.
- Concorrência no mesmo job devolve JOB_BUSY; falhas não publicam um job parcial.
- Consulta/retorno apenas lê resultado/proveniência; não volta a chamar IA.
- Hashes detetam alterações contra a referência guardada; não são assinatura nem
  proteção contra um atacante que substitui simultaneamente referência e ficheiros.
- É uma fronteira de execução, **não uma sandbox de OS**. ACL/sandbox Windows,
  power loss, hardware e GPU exigem gates próprios.

Responsabilidades existentes: adaptação/importação de resultados, proveniência,
validação e integração. Não acrescenta módulo de autoridade ao Nexus.

## Instalação Windows preparada

Na pasta desta extensão:

```powershell
.\install-windows.ps1 -OpenNotebookRoot 'C:\Nexus-Lab\open-notebook' -ApiPython 'C:\Nexus-Lab\open-notebook\.venv\Scripts\python.exe'
```

Os caminhos são exemplos: fornecer a instalação real. FFmpeg e FFprobe têm de
estar no PATH do processo Open Notebook. O script cria um venv de worker isolado,
instala bibliotecas e pesos, instala o router com backup e configura apenas as
quatro variáveis desta capacidade. Reiniciar o Open Notebook depois.
`-Device cuda` instala Torch CUDA 12.4; Windows/GPU ainda requer teste real.
O script não instala/restabelece todo o Open Notebook nem gera o podcast.

## Instalação Linux ensaiada

```bash
python3.12 -m venv venv-avatar
venv-avatar/bin/python -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu
venv-avatar/bin/python -m pip install --only-binary=av -r requirements-worker.txt '.[mcp]' gdown==6.4.1
venv-avatar/bin/python provision_models.py /path/avatar-models
/path/open-notebook/.venv/bin/python -m pip install .
/path/open-notebook/.venv/bin/python install_router.py /path/open-notebook
```

No `.env` nativo, configurar:

```dotenv
OPEN_NOTEBOOK_AVATAR_ROOT=/path/portraits
OPEN_NOTEBOOK_AVATAR_OUTPUT=/path/avatar-videos
OPEN_NOTEBOOK_AVATAR_CHECKPOINT=/path/avatar-models/wav2lip.pth
OPEN_NOTEBOOK_AVATAR_PYTHON=/path/venv-avatar/bin/python
```

Guardar `s3fd.pth` ao lado de `wav2lip.pth`. Não dereferenciar o symlink do
executável Python de um venv: usar o caminho do venv preserva as dependências.
Colocar um retrato nessa pasta; não descarregar uma página HTML como fotografia.

## Rotas nativas

| Método | Rota | Efeito |
|---|---|---|
| POST | `/api/podcasts/episodes/{episode_id}/avatar` | Gerar/recuperar MP4 e proveniência |
| GET | `/api/podcasts/avatars/{job_id}` | Validar e devolver proveniência |
| GET | `/api/podcasts/avatars/{job_id}/video` | Validar e servir vídeo |

POST JSON: `{"avatar":"portrait.png","device":"cpu","batch_size":8}`.
As rotas herdam middleware de autenticação/limites do Open Notebook. Se a palavra-passe
nativa não estiver configurada, a autenticação nativa está desativada; a extensão
não cria uma segunda política. Não expor a instalação sem configuração adequada.
Ainda não existe botão novo no frontend; chamada pela API/MCP.

## MCP

Servidor stdio **adicional**, não alteração ao catálogo do MCP de terceiros:

```bash
venv-avatar/bin/python -m notebook_avatar.mcp_server
```

Tools: `render_podcast_avatar` e `get_podcast_avatar`. Usa origem fixa
`http://127.0.0.1:5055`, sem proxies/redirecionamentos. Configurar
`OPEN_NOTEBOOK_PASSWORD` no ambiente do servidor quando a API exigir autenticação.
O Kernel continua responsável por allowlist/autoridade/ingestão no Store.

## Testes

```bash
python -m pip install '.[test]'
PYTHONPATH=/path/open-notebook python -m pytest tests -q
```

Usar o Python do Open Notebook para a suite com autenticação/exceções nativas.
Os testes de fronteira usam FFmpeg real e substituem apenas o modelo aprendido;
essa suite não prova sincronização labial. O ensaio opt-in `tests/run_native_e2e.py`
usa Open Notebook, SurrealDB, SFD/Wav2Lip, FFmpeg, autenticação e MCP reais.
Argumentos: `--source-root`, `--python-api`, `--python-worker`, `--surreal`,
`--checkpoint`, `--audio`, `--portrait`, `--report` (pasta nova).
Usar apenas um checkout/DB de laboratório: o ensaio cria um episódio sintético.

A integração Nexus dispõe ainda de um gate separado:
`Kernel/Host → MCP stdio → fronteira OpenNotebook loopback → Creative → Human Gate → Canonical → restart`.
Esse gate testa o encadeamento e rejeições de respostas inválidas, mas a peer HTTP
é determinística e não substitui um teste do backend Open Notebook completo com
SurrealDB e modelo local físico.

## Licenças e fontes

- Código da extensão: licença do repositório Nexus, PolyForm Noncommercial 1.0.0.
- Open Notebook: MIT; lipsync 0.1.0 declara MIT, mas a documentação remete para
  restrições não comerciais dos modelos Wav2Lip. Não inferir direito comercial.
- Wav2Lip original/pesos: uso pessoal/investigação/não comercial; não redistribuídos aqui.
- FFmpeg, Torch, torchvision, SFD/face-alignment e restantes dependências mantêm
  as respetivas licenças. Instalação não transfere a licença Nexus para terceiros.
- Fontes: https://github.com/mowshon/lipsync ; https://github.com/Rudrabha/Wav2Lip ;
  https://github.com/1adrianb/face-alignment ; https://ffmpeg.org/ffmpeg.html .

Consultar o relatório versionado para a evidência histórica e o comentário de
baseline mais recente da PR #23 para o HEAD atual. PC físico/GPU e Open Notebook
completo + SurrealDB + modelo local no mesmo E2E continuam gates distintos.
