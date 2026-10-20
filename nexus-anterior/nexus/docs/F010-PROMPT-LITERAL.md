# F010 — prompt de citação literal

Problema reproduzido: 3 de 6 execuções reais foram bloqueadas. A Tiny reformulou
citações; o comparador de substring recusou-as corretamente. O resumo também
confundiu a data de registo com data de entrega num diagnóstico.

Correção: transformação v2 separada no Open Notebook, com prompt versionado em
../prompts/interpret-v2.md. Define citação contínua literal, exemplo positivo e
negativos, negações, datas e instruções de documentos como dados. A transformação
anterior foi preservada. A configuração de laboratório aponta para a v2.
Não foram alargados schemas nem removidas validações.

Repetição E2E: português, números, ciência, pedido de som, pedido de imagem,
e instrução maliciosa. 6/6 candidatos válidos, UNKNOWN, uma chamada IA por caso;
todos os bypasses bloqueados, credenciais temporárias removidas e Canonical
inalterado. Inspeção dos seis resumos confirmou preservação dos factos centrais;
há alguma verbosidade e títulos genéricos. Amostra pequena, não taxa de fiabilidade.

Som/imagem testam compreensão textual; não geram áudio ou imagem.
LanguageTool foi testado separadamente na instalação (CLI, sem IA); não foi
inserido silenciosamente neste workflow cognitivo.

Três testes determinísticos adicionais garantem rejeição de maiúscula alterada,
ponto acrescentado e paráfrase em citações. O prompt não substitui o comparador.
