# Arquivo do Nexus anterior — 20 de outubro de 2026

Arquivo de código pedido pelo proprietário, antes da migração para trabalho local com AIChat, macros YAML, Taskfile, Open Notebook, ferramentas especializadas, Markdown e SQLite FTS5.

- `nexus-anterior/`: 421 ficheiros versionados do PC, origem `PAPACREATOR/cerebro-parvo-`, commit `bcbd873a037d42ad8d2352b0c199e6078d4b9e55`.
- `folha-dagu/`: código Folha/Dagu, incluindo alterações locais ainda não publicadas, baseado em `e36103bf314ae0022b376693b652c8b108f07ea7` de `PAPACREATOR/cerebro-parvo-unified`.
- `integracoes-locais/`: scripts locais de instalação e ligação às ferramentas, conservados como referência.
- `manifesto.json`: hashes dos originais e das cópias arquivadas.
- `redacoes.json`: locais onde valores literais relacionados com credenciais foram removidos. Inclui marcadores e credenciais de testes, por precaução.

Este arquivo tem um histórico Git novo: não inclui os quatro commits locais antigos que poderiam transportar a credencial no seu histórico. O código foi preservado como fotografia do estado indicado, com as redações declaradas. Os repositórios remotos anteriores conservam o histórico que já tinham.

Não inclui credenciais locais, configurações privadas JSON, documentos pessoais, bases de dados, modelos, ambientes Python, caches ou ficheiros temporários. Os originais locais não foram modificados por esta preparação. Nenhuma pasta antiga pode ser apagada só com base neste ficheiro: é necessário verificar o arquivo remoto e preservar os dados e dependências das ferramentas.

O arquivo não é uma instalação nem uma declaração de funcionamento. As provas existentes e limitações constam de `folha-dagu/folha/ARQUIVADO.md`. A nova implementação local admite no máximo um script PowerShell de ligação; as macros AIChat e receitas Taskfile usam os mecanismos nativos das aplicações.