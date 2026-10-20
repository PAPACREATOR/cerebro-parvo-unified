# 11/10/2026 — server.js → Host Python e índice FTS5 sem segunda autoridade

Estado: **integração implementada na PR #55, com CI Linux/Windows; instalação física no PC do utilizador por validar. Não declarar concluída sem gates verdes no mesmo SHA.**

## Decisão

Conservar o `server.js` como *gateway HTTP local, opcional e sem estado*. A Folha comunica com o gateway, que encaminha os bytes de cada pedido para o `nexus/app.py` ativo; este autentica sessão e chama o Host/Store existentes. O gateway **não é injetado no Kernel**, não importa Store, não cria tickets, não seleciona ferramentas, não interpreta texto, não aprova e não grava memória.

```text
Folha (nexus/ui/app.js; sessão emitida pelo Python Host)
  → [opcional] server.js / Express / 127.0.0.1, sem armazenamento
  → nexus/app.py / 127.0.0.1, verifica Host, Origin e X-Nexus-Session
  → Host + Kernel / contratos + políticas + runtime Windows delimitado
  → Store (input original, Creative, Canonical, decisão humana, proveniência)
                      ↑
          FTS5 = índice derivado, reconstruível e sem autoridade
```

O lançamento oficial direto da Folha por `nexus/app.py` continua válido sem Node. O gateway é uma opção de desenvolvimento/apresentação, não dependência do produto Windows.

## Verificação da solução no código existente

- `nexus/app.py` oferece `/api/search` (POST autenticado e só leitura), `/api/interpret`, `/api/prepare-run`, `/api/confirm-run`, `/api/runs`, `/api/runs/<id>`, `/api/pdf/<id>`, `/api/prepare` e `/api/approve`. Impõe Host/Origin loopback e sessão emitida pelo Host.
- O Host gere a execução e a aprovação, enquanto o Store conserva entrada original, hashes, resultados, proveniência, Creative e Canonical. Uma confirmação de execução não é uma aprovação de Canonical.
- O novo `server.js` encaminha status, cabeçalhos e corpo de resposta; não permite `/api/run` de diagnóstico; não tem `Map()` de memória nem `generateSimplePdf`; está ligado só a `127.0.0.1`.
- `nexus/ui/index.html` regressa aos bytes originalmente selados. `nexus/ui/app.js` aceita na Folha `?? pesquisar termo` (só Canonical) e `?? pesquisar rascunhos termo` (Creative explícito). `nexus/app.py` e `nexus/integrity.json` foram atualizados; **Kernel, Host, Store e parser não foram modificados**.
- O arranque opcional precisa de uma porta Python fixa e `NEXUS_BACKEND_PORT` compatível. A sessão só pode ser a emitida pelo Python; a URL simples do gateway **não emite** sessão. Reutilizar a sessão não equivale a partilhá-la com ferramentas externas.
- Se a porta Python não responder ou a sessão for recusada, o gateway falha fechado e não faz trabalho de substituição.

## Memória única e FTS5 — código já existente

O laboratório `nexus/lab/wiki/kernel_bridge.py` já implementa um `WikiBridge(store, lab_root)` com:

1. `rebuild()`: lê pacotes do Store, verifica conteúdo e proveniência, recria SQLite/FTS5 em diretório separado;
2. `search(query, allowed_ids, include_creative=False, limit=8)`: escopo de IDs obrigatório, consulta literal parametrizada, limite e revalidação do conteúdo pelo Store; por defeito apenas Canonical;
3. `prepare`/`revalidate`: pacote com ID, autoridade e hashes de conteúdo, proveniência e input;
4. `save_experiment`/`reverse`/`uses`: evidência experimental; não cria aprovação e não escreve Canonical.

**Três memórias lógicas, uma autoridade:** trabalho transitório; processos/regras versionados; conhecimento persistente Creative+Canonical. O SQLite/FTS5 não é um novo cofre nem uma quarta memória: é uma *vista materializada* da memória existente, descartável e reconstruível. O original e a proveniência permanecem nos ficheiros geridos pelo Store.

Reutilizar o laboratório, e não copiar o SQLite do Sir Thaddeus: o Sir Thaddeus documenta uma separação útil entre contrato de memória e armazenamento FTS5, mas inclui políticas de permissões `Session`/`Always` inadequadas à confirmação humana por operação do Nexus.

## Integração FTS5 da Folha — contrato real

- A Folha chama exclusivamente `POST /api/search` com `{"query": "termo", "include_creative": false, "limit": 8}`. O comando na folha, sem botões adicionais, é `?? pesquisar termo`. Para ver *também* rascunhos, tem de escrever `?? pesquisar rascunhos termo`; o marcador Creative nunca se confunde com Canonical.
- A sessão `X-Nexus-Session` é a mesma emitida pelo Host, para requisições diretas ao Python ou encaminhadas pelo Node. O gateway Node só encaminha os bytes e recusa `/api/run`; não cria tickets, executa ferramentas ou escreve Store.
- O `nexus/app.py` autentica pelo Host, exige esquema exato e limites de consulta, e deriva IDs autorizados de `Host.list_runs()`, que faz verificações do Store. Os resultados de pesquisa têm run_id, autoridade, processo, pequeno excerto, SHA-256 do conteúdo e SHA-256 da proveniência.
- **Autoridade:** só `HUMAN_REQUIRED` está em Creative. A única promoção possível é via `POST /api/prepare` seguido de `POST /api/approve` com decisão humana válida. O Store verifica ticket, ID, hash do candidato e proveniência. Apenas após esta etapa o estado é `PASS`, entra em Canonical e aparece na pesquisa padrão.
- A implementação reutiliza **sem copiar** `nexus/lab/wiki/kernel_bridge.py`. Como o Host exige manifesto exato e o laboratório não faz parte desse conjunto fechado, `nexus/app.py` compara SHA-256 dos dois módulos laboratoriais a valores fixos antes de lhes dar acesso ao Store. O próprio `app.py` está selado em `nexus/integrity.json`.
- O índice é armazenado num diretório irmão `<store>-fts5-index/wiki.sqlite`, fora dos cofres e do repositório. A pesquisa revalida o resultado contra bytes originais e proveniência. Os dados de laboratório e SQLite **não** substituem o Store; reconstrução serve para invalidar ou recuperar o índice derivado.
- O contrato preserva as redundâncias justificadas: **hashes no Store**, **revalidação de snapshots do WikiBridge**, **manifesto do Host**, **validação dos módulos laboratoriais no Python**, **ticket humano de revisão** e **escopo de pesquisa Canonical/Creative**. Não há motores de aprovação paralelos.
- O índice contém cópias pesquisáveis de conteúdo e deve herdar proteção local do utilizador. Não sincronizar `wiki.sqlite` com o telemóvel; sincronizar objetos/fontes aprovados e reconstruir localmente.
- O índice usa os testes laboratoriais existentes; o uso em produção requer testes no Windows físico, incluindo ACL, interrupção de energia, recuperação após índice corrompido e integração com arranque normal.

## Testes e evidência

A PR inclui suites de Node e Python com Store real mas dados temporários, sem iniciar ferramentas externas:
- `nexus/tests/test_memory_search_http.py`: Canonical por defeito, inclusão Creative explícita, autenticação obrigatória, operadores FTS5 tratados como texto, rejeição de payloads inválidos, reconstrução após mudanças, adulteração de conteúdo, ausência de promoção via pesquisa e circuito **Creative → revisão → recusa → aprovação humana via Host → Canonical → FTS5 → verificação inversa no Store**.
- `nexus/tests/test_gateway_real_host.py`: Folha/Node → API Python → Host e Store → FTS5 → retorno a Node, com rascunhos separados de conteúdo aprovado e sem promessas de aprovação.
- `nexus/tests/gateway_transport.test.cjs`: limites de confiança HTTP, loopback, sessão, Host/Origin, PDF, sem estado próprio no Node.
- `nexus/tests/folha_search_smoke.cjs`: interpreta comandos `?? pesquisar` e `?? pesquisar rascunhos` e verifica ausência de chamada de execução.
- `nexus/lab/wiki/test_kernel_bridge.py`: regressões laboratoriais de FTS5, hashes, origem e pesquisa.

A workflow `Nexus Optional AI Studio Gateway` repete testes em Linux e Windows; as restantes workflows do produto incluem regressões Windows, Front Door, integração e confinamento. **Apenas integrar a PR no `main` quando todos os gates exigidos estiverem verdes no mesmo HEAD.** Um resultado PASS em CI não equivale a validação de instalação no PC físico do utilizador.

## Limitação não escondida

O gateway Node permanece opcional: primeiro iniciar `python -m nexus.app --no-browser --port <porta>`, apontar `NEXUS_BACKEND_PORT` para essa porta e usar a sessão emitida pelo Python. O comando `npm start` sozinho não inicia o Host e nunca deve fabricar uma sessão. O índice FTS5 é uma vista pesquisável de resultados provenientes do Store, não uma memória artificial gerada por modelo ou autorização implícita para ferramentas.
