# Nexus Local — matriz estrutural Windows — 2026-10-07

## Estado

Este documento regista a revisão feita após dois FAIL físicos no PC Windows:

1. `winget`/Node devolveu MSI `1603`, apesar de `node.exe` e `npm.cmd` estarem funcionais.
2. O instalador exigia um runtime local legado específico, contrariando a decisão de manter o modelo local desacoplado e subordinado ao Kernel Python.

A correção não altera M1–M14, T1–T6, Creative/Canonical, Human Gate, MCP nem a Folha Única.

## Runtime local de modelos

O runtime local legado deixa de ser dependência do percurso ativo.

`llama.cpp` é tratado como ferramenta externa local e substituível, da mesma forma que FFmpeg ou LibreOffice. O Kernel continua Python-first e mantém toda a autoridade.

Serviços:

| Serviço | Bind | Porta |
| --- | --- | ---: |
| SurrealDB/OpenNotebook | 127.0.0.1 | 8000 |
| ACE-Step | 127.0.0.1 | 8001 |
| Forge | 127.0.0.1 | 7861 |
| OpenNotebook API | 127.0.0.1 | 5055 |
| Speaches/Kokoro | 127.0.0.1 | 8969 |
| llama.cpp linguagem | 127.0.0.1 | 18081 |
| llama.cpp embeddings | 127.0.0.1 | 18082 |

A porta 8001 chegou a ser considerada para linguagem durante a revisão, mas foi rejeitada porque já pertence ao ACE-Step. Nenhum commit funcional foi feito com essa colisão.

## Modelos fixados

Linguagem:
- repositório: `Qwen/Qwen3-1.7B-GGUF`;
- ficheiro: `Qwen3-1.7B-Q8_0.gguf`;
- revisão: `90862c4b9d2787eaed51d12237eafdfe7c5f6077`;
- SHA-256: `061b54daade076b5d3362dac252678d17da8c68f07560be70818cace6590cb1a`;
- alias local: `nexus-qwen3-1.7b`.

Embeddings:
- repositório: `Qwen/Qwen3-Embedding-0.6B-GGUF`;
- ficheiro: `Qwen3-Embedding-0.6B-Q8_0.gguf`;
- revisão: `d20cf9c16f82914a21dbd9c645f56895fb1d7750`;
- SHA-256: `06507c7b42688469c4e7298b0a1e16deff06caf291cf0a5b278c308249c3e439`;
- alias local: `nexus-qwen3-embedding-0.6b`.

O endpoint de embeddings usa `--embedding --pooling last --embd-normalize 2`, uma só slot e sem continuous batching. Ambos os servidores ficam exclusivamente em loopback.

## OpenNotebook

OpenNotebook 1.15.0 permanece fixado no commit já usado pelo Nexus.

A configuração passa a usar três credentials `openai_compatible` separados:
- linguagem -> `127.0.0.1:18081/v1`;
- embeddings -> `127.0.0.1:18082/v1`;
- TTS/Speaches -> `127.0.0.1:8969/v1`.

Separar credentials evita misturar modalidades e permite testar cada fronteira independentemente.

## MoneyPrinterTurbo

MoneyPrinterTurbo passa a apontar exclusivamente para a fronteira local OpenAI-compatible de llama.cpp.

O LLM configurado passa a ser o endpoint OpenAI-compatible local de linguagem:
- provider: `openai`;
- base URL: `http://127.0.0.1:18081/v1`;
- model: `nexus-qwen3-1.7b`.

No percurso documental Nexus, o guião continua a vir do OpenNotebook; MoneyPrinterTurbo é montagem subordinada e sem autoridade.

## Python e runtimes

- Nexus: Python 3.12.
- OpenNotebook 1.15.0: Python >=3.11,<3.13; Python 3.12 é compatível.
- Speaches pin usado pelo Nexus: Python 3.12.
- ACE-Step 1.5: Python >=3.11,<3.13; o LLM pesado interno continua desativado no alvo de 8 GB.
- Forge: Python 3.10 isolado pelo `uv`, sem contaminar o Python 3.12 do Nexus.
- MoneyPrinterTurbo: Python >=3.11 e usa o Python 3.12 do Nexus.
- LibreOffice/LanguageTool/Zotero: Java 17 permanece o runtime Java comum.
- Node: a compatibilidade final não é inferida apenas pela versão; `npm ci` + `npm run build` do frontend OpenNotebook continuam gate obrigatório.

## Zotero + LibreOffice

O instalador já não considera Zotero validado apenas porque `zotero.exe` existe.

Gate:
1. Zotero real;
2. LibreOffice real;
3. Java real;
4. `unopkg` real;
5. `integration\libreoffice\Zotero_OpenOffice_Integration.oxt` presente;
6. extensão registada no LibreOffice via `unopkg`;
7. pós-instalação volta a confirmar o registo.

## Regra winget

`winget list` deixou de ser prova suficiente.

Para pacotes com executável:
- se listado, o executável tem de existir e executar;
- se a instalação devolver código 0, o runtime volta a ser verificado;
- se o instalador devolver erro mas o runtime real existir e funcionar, o estado pode continuar com essa evidência;
- caso contrário, FAIL.

Isto preserva o FAIL real e evita falsos FAIL como o observado com Node.

## Gate estrutural 300.000

`nexus/tests/test_windows_stack_structural_300k.py` executa seis blocos de 50.000 casos:

1. serviço -> porta -> serviço, ida e volta;
2. endpoint loopback -> parse -> reconstrução;
3. modelo -> URL/revisão/hash -> modelo;
4. bindings cruzados instalador/OpenNotebook/MoneyPrinterTurbo/pós-instalação;
5. ataques de colisão de portas em ambas as ordens;
6. endpoints não-loopback hostis em ambas as direções.

Total declarado e verificado: 300.000 casos estruturais determinísticos.

Depois deste gate correm as suites normais `core`, `blocks`, `practical` e a regressão padrão. No PC, `test-post-install.ps1` repete o gate estrutural e só depois avança para os testes práticos e físicos.

## Limites de evidência

Os 300.000 casos não equivalem a 300.000 inferências, músicas, vídeos ou documentos físicos.

O pós-instalação é que prova no PC:
- inferência real no modelo de linguagem;
- embedding real e dimensão não vazia;
- CUDA real no Forge;
- ACE-Step import real;
- MoneyPrinterTurbo CLI real;
- Writer/LibreOffice real;
- Zotero OXT registado;
- MCP real e testes bidirecionais existentes.

Activepieces e Docling/PyMuPDF4LLM pertencem à arquitetura maior, mas não estão instalados por este branch de instalação neste estado. Por isso este documento não os marca como PASS físico nem estruturalmente integrado.
