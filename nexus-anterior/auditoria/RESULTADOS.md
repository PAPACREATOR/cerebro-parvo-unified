# Evidência da reconciliação — 27-09-2026

## Testes executados

Suite original do pacote revisto: **34 passed**, exit code 0, Linux/Python 3.12.14, pytest 8.3.5. Execução repetida sobre a cópia que vai para o repositório. [Saída real](testes-fornecidos-2026-09-27.txt). Testes e código do pacote não foram alterados.

A primeira tentativa com o Python geral não tinha pytest e não executou testes. Foi criado um ambiente isolado e instaladas dependências fixadas; só o resultado posterior conta como execução. O TEST_RESULTS do pacote é preservado como fonte histórica, não usado como substituto desta execução.

## Alcance

Os testes exercitam funções mínimas de contrato e casos negativos. Não demonstram Folha, integração Activepieces, sandbox/IA, persistência conjunta, crash real, Windows, três memórias/comparadores nem M1–M14 completo. A função de reconciliação recebe indicadores de evidência; o teste desses indicadores não prova recuperação do disco.

Não foram escritos novos testes nem corrigido código do produto nesta reconciliação. A revisão de IMP-001 identificou falta de cobertura do contrato detalhado; fica PARCIAL, sem autorização de avanço. IMP-019/G10 e IMP-026 continuam bloqueados.

## Preservação e documentação

O manifesto permite verificar byte-a-byte os 35 ficheiros anteriores, as três fontes Markdown e os nove ficheiros do candidato. O script também verifica links locais da orientação ativa. Fontes/histórico preservados podem conter referências antigas a ficheiros que nunca estiveram neste repositório; não se apresentam como documentação disponível.

GitHub Actions reproduz integridade e suite fornecida. O seu estado efetivo deve ser consultado na execução, nunca inferido da presença do YAML.
