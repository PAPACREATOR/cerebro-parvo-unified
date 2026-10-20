> **Estado atual (06-10-2026):** o objetivo cognitivo permanece, mas Conductor/interpret.yaml foram substituídos no runtime ativo por Host → adapter OpenNotebook → validação → Creative. OpenNotebook continua ferramenta externa e Tiny/IA continua sem autoridade. O E2E físico completo OpenNotebook+SurrealDB+modelo local no PC ainda é gate separado.

# F005 — ligação cognitiva
INPUT: texto UTF-8 até 6000 caracteres e configuração administrativa local.
OUTPUT: título, resumo e citações exatas, validados; candidato UNKNOWN em Creative.
LEIS: nenhum resultado IA aprova conhecimento; sem ferramentas para o modelo; original preservado; proveniência.
DEPENDÊNCIAS: Conductor e Open Notebook já instalados; Tiny já configurada; biblioteca padrão HTTP e JSON Schema existentes.
TESTES: resultado válido; JSON inválido/campos de autoridade; citação ausente da fonte; input vazio/grande/binário; config remota; circuito real sem Canonical.
LIMITES: validade estrutural e citações exatas não provam veracidade do resumo nem isolamento de OS. PDF/DOCX ainda não suportados neste ramo.


# Ligação cognitiva — primeira vertical

01/10/2026. Host → Microsoft Conductor → interpret.yaml → Open Notebook → Tiny Qwen3-4B → JSON validado → Creative: PASS num texto artificial, 10,07 segundos. Duas citações foram conferidas como trechos exatos da fonte. Canonical permaneceu vazio. Credencial temporária do run removida no final.

83 testes Nexus passaram em 20,96 segundos, incluindo respostas inválidas, campos de autoridade, citações inventadas, texto inadequado e configuração remota.

Creative recebe automaticamente resultados validados; não exige aprovação humana. O estado interno HUMAN_REQUIRED refere-se apenas à eventual promoção. A etiqueta da Folha foi clarificada para “Em Creative · por rever”. Publicar ou promover é outra ação, com versão/destino explícitos.

Limites: ensaio pela API do Host, sem teste visual da Folha nesta ronda; texto UTF-8 até 6000 caracteres; não é ingestão PDF/DOCX; wiki, integração das restantes ferramentas, isolamento Windows e testes prolongados permanecem pendentes. UNKNOWN é conservado: formato válido e citações exatas não provam que o resumo seja verdadeiro. Nenhuma nova biblioteca foi adicionada para este adaptador.
