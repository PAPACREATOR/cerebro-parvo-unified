# F009 — primeira família Multimédia

> Estado atual (04-10-2026): o transporte Microsoft Conductor/YAML desta fase foi removido do runtime ativo depois dos testes de equivalência. O contrato de dados e a evidência histórica foram preservados. A leitura atual é Nexus-owned, em Python determinístico.

## Contrato
INPUT: Markdown UTF-8, até 100 KB, com metadados iniciais entre `---`.
Campos obrigatórios: tipo=proposta, familia=multimedia, tribo=som ou imagem,
dominio=creative, lab=windows. Campos adicionais são rejeitados.
OUTPUT: JSON com nome_ficheiro, dados_yaml e notas_markdown.

O leitor atual é `nexus/adapters/constitutional.py`: parser estrito e limitado,
sem execução de YAML, sem tags, anchors, listas, duplicação de chaves ou campos
de autoridade. O documento nunca concede capacidades, aprovação ou acesso a
Canonical.

## Evidência
O contrato mantém 100 casos válidos, 900 casos inválidos e as fronteiras
históricas. A migração para parser Nexus-owned acrescentou stress de 5.000
casos válidos e 3.000 inválidos/adversariais. A comparação com o parser antigo
Conductor permanece no histórico Git, não no código ativo.

## Limites
Esta família continua a ser contrato de objetos multimédia, não autoridade nem
motor de geração. Som/imagem só entram por capabilities explicitamente ligadas
ao Kernel. Nada neste Markdown promove automaticamente para Canonical.
