# Avatar no Open Notebook — laboratório de 04/10/2026

Pedido de Pedro: corrigir o bloco duplicado, instalar bibliotecas, integrar avatar com FFmpeg no Open Notebook e testar extensivamente.

Entrega na branch `lab-open-notebook-avatar-20261004`, sobre PR #22 / `b0b95076c94b4752db8955744e3fe4ed8e4fcb68`. O código ativo do Nexus e main não foram alterados. Open Notebook ensaiado: v1.14.0, commit `30c7e2a63e43b7f270fc2c638f0b6246934a53f4`.

## Resultado concreto

Implementadas três rotas nativas de geração, consulta e download de avatar, herdando autenticação nativa; worker isolado SFD/Wav2Lip/FFmpeg; dois tools MCP stdio adicionais; instaladores e provisionamento de pesos verificados por SHA256. O áudio é o do episódio existente. Não se reconstrói o motor podcast/TTS.

O bloco original descarregava HTML como fotografia, usava assinatura de `LipSync.sync` incorreta e tinha código duplicado/truncado. A extensão usa retrato local validado e chama a API real `sync(face, audio_file, outfile)`. Adapta os pesos oficiais com `weights_only=True`, evita cache pickle/torch.compile, fixa modelos offline, preserva os executáveis de venv, valida caminhos, impõe limites, isola subprocessos e publica vídeo/proveniência atomicamente.

Dependências efetivamente instaladas e verificadas no laboratório Linux: Torch 2.5.1+cpu, torchvision 0.20.1+cpu, lipsync 0.1.0, av 14.0.1, face-alignment 1.5.0, extensão e MCP; ambiente nativo Open Notebook separado. `pip check` PASS nos dois ambientes. FFmpeg/FFprobe 6.1.1. SurrealDB real 2.2.1.

## Evidência e limites

| Ensaio | Resultado | O que prova |
|---|---|---|
| Suite final da extensão | 165 PASS / 0 FAIL / 0 SKIP, 11,93 s | Fronteiras, erros, limites, concorrência, retry, alteração de modelos, autenticação nativa, integridade, FFmpeg real; modelo aprendido substituído nesta suite |
| Aceitação nativa offline | PASS, render 5,06 s, MP4 0,52 s | Open Notebook + SurrealDB + SFD/Wav2Lip CPU + FFmpeg reais |
| Aceitação nativa com áudio repetido | PASS, render 8,01 s, MP4 3,76 s | Segundo circuito real com amostra de fala repetida, duração de entrada 3,87225 s |
| Regressão geral Nexus em Linux | 1319 PASS / 14 FAIL / 7 SKIP, 27,71 s | Não permite declarar PASS global; código ativo idêntico à base |
| CI Ubuntu | 165 PASS / 0 FAIL / 0 SKIP, 11,40 s | Contratos com FFmpeg e autenticação nativa reais |
| CI Windows | 165 PASS / 0 FAIL / 0 SKIP, 11,46 s | Mesma suite em runner Windows; modelo aprendido substituído |
| GPU/instalador no PC de Pedro | NOT RUN | Não confundir runner de testes com instalação física |

As duas aceitações nativas persistem episódio sintético, rejeitam auth/payload inválidos, geram e descarregam vídeo, conferem hashes em sentido inverso, repetem o mesmo job, usam MCP real, reiniciam API e recuperam proveniência; rejeitam vídeo adulterado e recuperam após restauração. Não geram TTS. A imagem de teste é astronauta NASA via skimage; fala fornecida pelo próprio upstream Open Notebook. O vídeo foi inspecionado visualmente, sem métrica quantitativa de sincronização.

[Evidência estruturada](../lab/open_notebook_avatar/evidence/summary.json), [JUnit](../lab/open_notebook_avatar/evidence/avatar-tests.xml), [aceitação offline](../lab/open_notebook_avatar/evidence/native-offline.json), [aceitação longa](../lab/open_notebook_avatar/evidence/native-longer.json). Os hashes e duração identificam os outputs testados; pesos e vídeos não são redistribuídos no repositório.

Os 14 FAIL gerais ficam identificados individualmente na evidência: dependência Windows/SystemRoot, fixtures/transportes MCP e patches antigos de LanguageTool/Office. Não foram corrigidos nesta extensão. Integridade do host existente verificada; não substituir hashes oficiais para aceitar outputs de laboratório.

Falhas durante desenvolvimento preservadas na evidência: av sem wheel compatível, ambiente/PYTHONPATH nativo, dereferência de venv para Python de sistema, colisão de fixture e execução de testes enquanto o worker era alterado. Foram corrigidas e a suite final foi executada sobre fonte estável.

## Repetição e instalação

Consultar [README](../lab/open_notebook_avatar/README.md), `requirements-worker.txt`, `install-windows.ps1`, `provision_models.py` e `tests/run_native_e2e.py`. O runner nativo exige checkout/DB de laboratório e caminhos explícitos de API, worker, SurrealDB, pesos, áudio, retrato e pasta de relatório nova. O workflow Linux/Windows cobre contratos e FFmpeg; não descarrega modelos nem prova GPU.

Ainda não existe botão no frontend. API/MCP funcionam. Resultado continua `UNTRUSTED/candidate`, sujeito a revisão humana; não existe promoção automática no Store. Não prova integração Folha/Kernel/Creative/Human Gate, instalação física, OS sandbox, ACL Windows, crash/power loss ou qualidade final. Wav2Lip tem restrições de uso pessoal/investigação/não comercial.

Próximo gate: executar instalador no checkout Windows de laboratório, validar episódio real e qualidade, depois rever integração limitada no Kernel. Não integrar em main por este relatório.

## Fecho de CI remoto

[Run 37233045607](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37233045607): os dois jobs terminaram SUCCESS sobre commit `ca8b034e1fd68cfdc78ba1368485c5b054472a65`. Logs conferidos: 165 PASS em cada OS, sem skips. [Índice de evidência CI](AVATAR-CI-2026-10-04.json) contém IDs e hashes dos ZIP JUnit. Esta atualização é apenas documental; fonte executada inalterada. PR de entrega: [#23](https://github.com/PAPACREATOR/cerebro-parvo-/pull/23).

## Sincronização posterior — 23h Lisboa

PR22 foi fechada sem merge por outra sessão. A entrega avatar é reaplicada sobre PR21 atual `0753f573f2dee739a4e43a5e255a4999319cc605`, mantendo as versões novas MCP/tiny intactas. Proveniência histórica acima permanece; os 14 FAIL Linux referem a base antiga, não são resultado da combinação nova. Regressão nova PENDING até CI. Não integrar antes de conferir esta combinação.

Fecho da nova combinação: [Auditoria SUCCESS](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37238792619), [Nexus Windows SUCCESS](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37238792589): core140, blocks1068, all1350, practical12 PASS; [Avatar SUCCESS](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37238792600): 165 PASS Windows/165 PASS Ubuntu. SHA testado569c3a1de720ac6e7ed509ea566c1f6b3f02a1bf. Evidência em [AVATAR-SYNC-CI-2026-10-04.json](AVATAR-SYNC-CI-2026-10-04.json). Não somar suites sobrepostas. PC/GPU/Kernel-avatarE2E permanecem NOT RUN.
