# Abrir no Visual Studio Code

Abrir `Cerebro.code-workspace` na raiz do clone. A extensão Python é recomendada, não instalada automaticamente. O editor fica apontado à `.venv` do projeto e aos testes do candidato. A configuração não executa comandos ao abrir.

No terminal do VS Code em Windows, a partir da raiz:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-auditoria.txt
.\.venv\Scripts\python.exe ferramentas/verificar_documentacao.py
Set-Location implementacao/candidata-2026-09-27
..\..\.venv\Scripts\python.exe -m pytest -q --color=no
```

Não reinstalar um ambiente já confirmado. Se a extensão não selecionar o ambiente, usar Python: Select Interpreter e escolher `.venv`. O ficheiro workspace está preparado; não foi aberto nem executado no computador de Pedro nesta sessão.

Código que esteja apenas no VS Code/local de Pedro ainda não foi inspecionado. Não substituir essa pasta pelo pacote: primeiro comparar versão, ficheiros e testes; preservar alterações locais. O código integrado aqui veio do ZIP revisto da Library.

Fonte: [Python settings reference](https://code.visualstudio.com/docs/python/settings-reference).
