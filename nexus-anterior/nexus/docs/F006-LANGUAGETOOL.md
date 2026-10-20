> **Estado atual (06-10-2026):** LanguageTool continua capability externa local. A implementação ativa é Kernel/Host → runner/MCP → adapter LanguageTool → relatório candidate/UNKNOWN em Creative. As referências a Conductor abaixo documentam o ensaio histórico de 01-10.

# F006 — revisão linguística local

INPUT: texto UTF-8 até 6000 caracteres; configuração administrativa com caminhos absolutos para Java e o JAR LanguageTool já instalados.
OUTPUT: relatório candidato de sugestões em Creative; original intacto; UNKNOWN, zero chamadas de IA.
LEIS: sem aplicação automática de correções, sem promoção automática, proveniência e Human Gate existentes.
DEPENDÊNCIAS: Java e LanguageTool existentes; CLI local. Nenhum serviço adicional.
TESTES: erro ortográfico pt-PT conhecido, texto sem alerta, resposta inválida/incompleta, executável ausente, timeout, entrada vazia/binária, circuito Host→Conductor→CLI→Creative, Canonical vazio, regressão.

## Decisão de implementação

O servidor HTTP local falhou ao criar a ligação interna Java. A CLI executa e deteta erros reais sem esse servidor; usar a CLI simplifica a integração. Não alterar políticas de segurança Windows.

Um resultado sem sugestões não prova que o texto esteja correto. O exemplo «Os documento está pronto.» não foi sinalizado pelo LanguageTool instalado. Preservar esta limitação; não alterar o texto automaticamente.

## Evidência — 01-10-2026

Regressão: `python -m pytest nexus/tests -q -p no:cacheprovider -o pythonpath=.` → **94 passed, 20.56 s, exit 0**. Os novos testes negativos usam respostas/falhas controladas.

Ensaio real separado: Host → Microsoft Conductor → proofread.yaml → Java/LanguageTool → JSON validado → Creative: **PASS, 14.97 s**. «Isto é um ezemplo.» originou sugestão «exemplo». Resultado UNKNOWN; zero chamadas IA; bytes originais conservados; Canonical vazio; aprovação com ticket inventado: BLOCK.

LanguageTool 6.9-SNAPSHOT e Java Temurin 21 já instalados. CLI com limite de heap 512 MB e timeout 45 segundos. Sem serviço HTTP. Português com e sem newline: erro ortográfico detetado em ambos; texto correto sem alertas; concordância do exemplo acima não detetada. Estes quatro ensaios demoraram entre 8.03 e 8.38 segundos cada.

A opção aparece na Folha; o circuito desta ronda foi exercitado pela API do Host. Validação visual desta opção ainda pendente. Não há deteção de todos os erros nem avaliação exaustiva do português.
