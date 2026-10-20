# SPEC-F0-001 — Evento versionado e canónico

## Objetivo

Criar a menor base Python testável para representar um evento determinístico. Não implementar event log, estado, replay, IA, Logseq, Activepieces ou base de dados nesta tarefa.

## Entregáveis

- `pyproject.toml` com Python 3.12 e pytest como dependência de desenvolvimento.
- pacote `src/cerebro_independente/`.
- tipo imutável `Event` com, no mínimo: `event_id`, `event_version`, `event_type`, `tick`, `occurred_at`, `rules_version`, `payload`.
- serialização JSON canónica estável e função SHA-256 sobre os bytes canónicos.
- testes em `tests/`.

## Contratos

- `event_id` e valores temporais são fornecidos pelo produtor; o tipo não os gera.
- `event_version >= 1`; `tick >= 0`; campos obrigatórios vazios são rejeitados.
- `occurred_at` deve ter fuso explícito e ser normalizado para UTC na representação canónica.
- payload aceita apenas valores compatíveis com JSON; NaN e Infinity são rejeitados.
- mesma semântica, incluindo ordem diferente de chaves do payload, produz os mesmos bytes e hash.
- alteração de qualquer campo semanticamente relevante muda o hash.
- o código não lê relógio de parede nem usa aleatoriedade.

## PASS

- todos os testes pedidos passam localmente;
- há testes positivos, validações negativas e estabilidade do hash;
- o diff não contém rede, base de dados, IA ou funcionalidades fora do âmbito;
- `STATUS.md` regista comando e resultado real.

## FAIL

- geração implícita de UUID/data;
- serialização dependente da ordem de dicionário ou locale;
- aceitação de NaN/Infinity;
- testes omitidos/ignorados;
- alteração arquitetónica ou trabalho fora desta SPEC.

## Paragem obrigatória

Depois de apresentar resultados, parar e aguardar revisão. Não iniciar SPEC-F0-002 e não fazer commit.
