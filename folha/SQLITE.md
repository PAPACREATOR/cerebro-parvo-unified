# SQLite usado na instalação local

CLI SQLite 3.54.1, pacote oficial Windows x64:
https://www.sqlite.org/2026/sqlite-tools-win-x64-3540100.zip

SHA3-256 do arquivo, conferido antes de extrair ou executar:
`e171f3993a992edf076746926dd52b5e2ebfabaee38818e74987e1d8112ab987`

Origem do hash: https://www.sqlite.org/download.html

O executável é colocado em `bin/sqlite3.exe` para testes e instalação; não é incluído no Git. Pode ser fornecido ao instalador através de `-SqliteExe`. O núcleo usa a CLI nativa; não depende de Python, Node ou de um servidor de base de dados.
