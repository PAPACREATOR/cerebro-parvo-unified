# Nexus — instalação isolada para aceitação Windows

**Estado: CANDIDATO DE TESTE. Não é a versão final.**

Este pacote contém:
- `install-nexus-test-isolated.ps1`: instala uma cópia **isolada** do SHA registado em `candidate-head.txt`, sem substituir `C:\Nexus` nem `C:\Nexus-Tools`;
- `start-nexus-test-isolated.ps1`: abre a Folha real apenas depois de o teste de aceitação estar verde;
- `candidate-head.txt`: commit integral imutável que será realmente instalado.

## Condições
Windows x64, **sessão normal não elevada**, Python 3.12, Git, acesso ao GitHub e PyPI para obter a cópia e as dependências mínimas `jsonschema` e `pytest`. Não executa `winget`, instaladores de terceiros, `install-nexus-complete.ps1`, sincronização sobre `C:\Nexus`, instalações de modelos ou serviços cloud.

## Instalar e testar
1. Obter o artefacto `nexus-windows-acceptance-PINNED` do workflow associado à PR #45, **apenas se o job de aceitação estiver SUCCESS**.
2. Extrair o ZIP numa pasta à escolha.
3. Abrir PowerShell normal (não Administrador), entrar na pasta extraída e examinar o código e o SHA.
4. Executar:

```powershell
powershell.exe -NoProfile -File .\install-nexus-test-isolated.ps1 -AuthorizeInstall
```

O instalador **recusa** sobrescrever instalações anteriores e não executa ações sem `-AuthorizeInstall`. A cópia fica por defeito em `%LOCALAPPDATA%\Nexus-Acceptance\revisions\<SHA>`; os relatórios ficam em `reports\<SHA>\acceptance.json`, com logs por etapa e XML pytest. Usa os testes existentes de autoridade, proveniência, recuperação, negações, Front Door, integração HTTP e verify em Windows, incluindo Creative → Human Gate → Canonical → restart. Todos usam dados sintéticos.

Se o estado final for `PASS_TESTABLE_CORE`, executar na mesma pasta do ZIP:

```powershell
powershell.exe -NoProfile -File .\start-nexus-test-isolated.ps1
```

O lançador verifica novamente SHA, origin, checkout limpo, relatório PASS e integridade. Os dados ficam em `%LOCALAPPDATA%\Nexus-Acceptance\data\<SHA>`. Abrir a Folha pelo navegador local quando o servidor a apresentar. A versão de produção permanece intocada.

## Critérios e limites
- `PASS_TESTABLE_CORE` **não significa produto final aprovado**.
- Writer/LibreOffice, livros e PDF em LPAC continuam **FAIL/NOT RUN** no candidato, até prova independente.
- OpenNotebook/SurrealDB/llama.cpp reais, instalações multimédia e PC físico exigem gates próprios. Não tratar fixtures como serviços instalados.
- Se o script falhar, preservar o relatório e enviar **apenas** `acceptance.json` e os logs sem credenciais ou dados pessoais. Não voltar a instalar no mesmo caminho; não eliminar/repor automaticamente o que já existe.
- Não fornecer privilégios administrativos para forçar um teste. Nunca usar `reset --hard` ou atualizar por cima da instalação anterior.
- Autoridade humana pré-execução e Human Gate para Canonical permanecem distintos.

## Validação no CI
A workflow da PR #45 executa o instalador verdadeiro num runner Windows descartável, usando o **mesmo SHA** do pacote produzido. Uma exceção de elevação é permitida somente ao runner e fica registada em `acceptance.json`; o pacote no PC recusa sessões elevadas. O PASS no runner **não substitui** PASS no Windows físico em conta normal.
