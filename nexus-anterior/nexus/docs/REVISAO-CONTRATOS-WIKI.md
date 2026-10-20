# Revisão — formatos, redundância, ferramentas e wiki

> Nota de estado (04-10-2026): este documento conserva a análise histórica. O runtime ativo já não usa Microsoft Conductor, Spiff nem YAML como motor. A execução atual é Kernel/Python; MCP é a fronteira de ferramentas. As conclusões sobre autoridade, proveniência e wiki continuam válidas.\n\n
01/10/2026. Análise de conformidade; sem alteração normativa.

Revisão de leitura, 04-10: conservar este relato histórico. A lacuna de schema
abaixo foi corrigida em [Schemas e Windows](SCHEMAS-E-WINDOWS.md), com
`test_schema_consistency.py`. A recuperação e ligação inversa atuais são
documentadas em [F013](F013-PROVENIENCIA-INVERSA.md). O requisito de wiki de
ligação mantém-se; a navegação pela proveniência ainda não está na Folha.

## Um contrato, três representações
Markdown descreve leis, conhecimento e decisões em linguagem humana. YAML define o processo executável, ferramentas permitidas, limites, ramificações e comparação. JSON transporta inputs, resultados, estados e evidência, validados por schema. Não são três cópias de segurança. A correspondência entre representações deve ser testada.

Exemplo: “Canonical exige aprovação humana da versão” (Markdown) → passagem pelo gate no processo → decisão ligada ao item/hash/destino (JSON) → validação pelo Host → escrita autorizada. Um campo approval_id inventado não é aprovação.

## Redundância
O workflow determina quando executar duas vias e como lidar com agreement/conflict/unknown/failure. Não exige duplicar todas as operações. Não permite votar uma hipótese para Canonical. Conservar outputs de ambas as vias e a decisão de comparação.

Implementação observada: verify.yaml chama SHA-256 Windows/.NET e Python/hashlib sequencialmente, compara e apresenta evidência. São implementações distintas do mesmo algoritmo, sobre o mesmo ficheiro e sistema operativo. Não são fontes independentes sobre a verdade do documento e não protegem contra falhas comuns de armazenamento/entrada. Paralelismo não é requisito para a validade desta comparação.

Mapeamento atual YAML: agreement→PASS; conflict→UNKNOWN; unknown→UNKNOWN; failure→FAIL.

## Lacuna reproduzida entre YAML e JSON
O schema result.json aceita status=PASS com outcome=conflict. O workflow atual produz UNKNOWN corretamente, mas a validação isolada do Host não impõe essa coerência. É uma lacuna de contrato, não uma aprovação sem humano demonstrada. Deve haver teste que rejeite a combinação incoerente e correção do contrato antes de abrir novas origens de resultados.

## Componentes
- Microsoft Conductor: executa o YAML. Não aprova conhecimento nem substitui as leis.
- Host: recebe, valida, autoriza, controla gates, preserva e apresenta.
- Open Notebook: bancada cognitiva substituível; recebe contexto permitido e devolve candidatos. Não é memória soberana nem isolamento de sistema operativo.
- LibreOffice, Zotero, pesquisa e outras capacidades: chamadas apenas quando o processo exige. IA não é necessária para conversão ou cálculo determinístico.
- Windows: processos, identidade, permissões, ficheiros e executáveis. A execução sob conta restrita e os acessos precisam de prova real.

## Wiki de ligação
A função está nas responsabilidades M1 (identidade), M3 (genealogia), M7 (relações), M8 (fontes) e M10 (recuperação). Liga documentos, blocos, conceitos, fontes, versões e projetos; permite navegar das conclusões à evidência e reconhecer contradições. Ligações sugeridas por IA são propostas, não normas.

Relações devem preservar identidade ao mover/renomear ficheiros. Uma ligação não promove o documento ligado, não transfere autoridade e não funde Creative com Canonical. Índices/grafos de navegação reconstruíveis não substituem fontes autoritativas. Não se escolhe uma nova aplicação wiki ou base vetorial sem necessidade demonstrada.

Estado: existe proveniência mínima no protótipo; a wiki relacional completa e a resistência das ligações a renomeações não estão demonstradas. Não chamar aos hashes atuais um comparador semântico ou relacional.

## Continuação conforme as leis
Orientação daquela revisão, anterior às correções ligadas acima:

Primeiro resolver o FAIL de recuperação já registado e a lacuna de coerência schema/processo. Depois isolamento Windows, restauro e integração das capabilities. Manter separados: requisito, código existente, teste executado e resultado. Os 51 PASS anteriores não cobrem as lacunas novas.
