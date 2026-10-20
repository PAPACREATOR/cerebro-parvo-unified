# Nexus Minimal — auditoria e plano de implementação

Data: 2026-09-30. Pedido vigente: especificação Nexus Host Minimal fornecida por Pedro nesta conversa, seguida de «quero que cries isso».

## Precedência

O histórico passou por Logseq, Joplin/grasp/Activepieces e dois SQLite. A decisão final recebida estabelece Windows → Folha → Host Python mínimo → Microsoft Conductor → ferramentas → JSON validado → Creative → humano → Canonical, com Open Notebook/IA local quando necessário. Esta decisão do autor prevalece para o novo protótipo. Os documentos antigos e as alterações locais são preservados.

## Auditoria inicial

- Repositório local confirmado: PAPACREATOR/cerebro-parvo-, HEAD b98be9b; contém trabalho não cometido anterior a esta sessão.
- Inventário de 96 Markdown fora de fontes reservadas; inventário não significa leitura integral. Foram lidos as instruções aplicáveis, arquitetura de 24/09, decisões, cabeçalhos de continuidade/estado e código das fronteiras reutilizáveis.
- Núcleo anterior: eventos, codec, ledger/replay SQLite, TTL, regras, comparação, risco, vínculo de aprovação, projeção e parsers Joplin. Não há Host/Folha/Conductor/Open Notebook integrado.
- Reutilizar HumanDecision e promotion_allowed: vinculam item e SHA-256. São funções puras; autenticação e escrita durável continuam a precisar de implementação.
- A camada Joplin/grasp e os SQLite não entram no circuito novo; conservar código/testes como histórico reutilizável, sem apagar ou migrar acervo.
- Python 3.12, PowerShell, jsonschema e pytest disponíveis. Conductor ausente. Nenhum serviço Open Notebook/modelo local foi confirmado.
- Consulta PyPI encontrou conductor-cli 0.7.0, diferente da versão 0.1.41 do repositório Microsoft. Usar código oficial fixado em 11dcc41ed3df78f0806127cc901822fe8758294b, licença MIT.

## Plano apresentado antes de código

1. F001: contrato de execução real Conductor, workflow apenas script e PowerShell. Input: ficheiro artificial; output: hash e estado JSON. Proibir provider de IA e verificar falhas de processo.
2. F002: leis e schemas; input JSON estrito, output validado, integridade, proveniência e Creative. Testar JSON inválido, campos extra, resultado vazio, processo desconhecido e interrupção.
3. F003: Folha local e gate. Texto/anexo → resultado candidato → decisão explícita sobre hash exato. Testar bypass, decisão falsa, conteúdo alterado, reinício e repetição.
4. F004: duas vias independentes (PowerShell/Get-FileHash e Python/hashlib), comparação declarada no YAML, ramos agreement/conflict/unknown/failure conservados.
5. F005: adaptador Open Notebook real, modelo local explicitamente escolhido, apenas texto delimitado e resultado estruturado. Não inventar serviço nem simular integração concluída.
6. Regressão, demonstração local, instruções de arranque, relatório de critérios e limites.

Cada F terá SPEC, testes, execução e evidência antes da seguinte. Não introduzir motores, bases de dados ou serviços além dos componentes pedidos. Instalação do Conductor isolada no workspace, sem alterar Python global. O Human Gate é uma fronteira da aplicação; não equivale a sandbox Windows contra programas que executem com a mesma conta.
