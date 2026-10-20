# Relatório de performance — shapes Conductor

Data: 2026-10-04
Escopo: benchmark experimental Windows CI; não altera arquitetura.

## Baseline funcional
Antes do P0, os 5000 casos Kernel -> Spiff -> Conductor -> Kernel passaram novamente.

## Resultados

### 5 set encadeados vs 1 set multi-values
- baseline mediana: 5.457 ms
- candidato mediana: 5.548 ms
- variação: -1.67%
- speedup: 0.984x

Conclusão: sem ganho relevante. Compactar só por performance não se justifica.

### 10 set sequenciais vs parallel
- baseline mediana: 10.501 ms
- candidato mediana: 10.991 ms
- variação: -4.67%
- speedup: 0.955x

Conclusão: parallel para operações internas muito baratas adiciona overhead. Não usar por defeito.

### foreach 100 set, concorrência 1 vs 20
- baseline mediana: 57.948 ms
- candidato mediana: 54.017 ms
- ganho: 6.78%
- speedup: 1.073x

Conclusão: concorrência ajuda pouco quando cada operação é muito barata. Só usar quando houver trabalho realmente paralelo/latência suficiente para justificar.

### subprocesso script vs set interno
- baseline mediana: 29.605 ms
- candidato mediana: 1.379 ms
- ganho: 95.34%
- speedup: 21.464x

Conclusão: evitar subprocessos para lógica determinística pequena. Compare/report/transforms simples devem ficar dentro do flow quando isso não reduz independência de métodos.

## Limites descobertos
- Conductor não permite step `wait` dentro de parallel.
- Conductor não permite step `script` dentro de parallel.
- `for_each.source` exige referência `agent.output.field`.
- Portanto não desenhar flows assumindo paralelismo arbitrário entre steps.

## Regra operacional provisória

1. manter subprocesso quando representa ferramenta/método realmente independente;
2. mover apenas lógica trivial de glue/compare/report para `set`/templating interno;
3. não usar parallel em trabalho interno barato;
4. usar foreach concorrente apenas quando houver ganho medido;
5. medir flow real antes de otimizar;
6. Kernel continua a impor limites externos.

## Implicação para verify.yaml

Candidato a testar:
- manter dois métodos de hash independentes (PowerShell/.NET + Python);
- avaliar se compare/report podem deixar de abrir subprocessos Python;
- não assumir que os dois hashes podem correr em `parallel`, porque `script` não é permitido nesse grupo no Conductor atual.

Logo a otimização útil provável é reduzir subprocessos de glue, não paralelizar scripts.
