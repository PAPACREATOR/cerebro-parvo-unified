# Folha local com PowerShell e Dagu

A Folha recebe o pedido. O PowerShell consulta o catálogo SQLite FTS5 e seleciona um template por regras explícitas,
preenche apenas os caminhos controlados e valida o YAML com o Dagu. O Dagu executa
os microprocessos e chama as ferramentas. A Folha mostra o resultado e permite
descarregar o texto ou PDF. Não há modelo de IA na seleção ou na geração do YAML.

## Interface preservada

`ui/index.html` e `ui/style.css` são cópias exatas da Folha existente em
PAPACREATOR/cerebro-parvo-, commit `18c228b0c5d2b322f71e9cfd346ddaf5e00a3d9e`.
Git blobs: HTML `f9e528012240efd0f5f6dc35212687b8ed159bdb`,
CSS `bce0e71880dcde58e7cc1ab747503f7522f4b66e`.
O JavaScript foi adaptado para envio direto, resultados, histórico e rascunhos.
Não apresenta as antigas aprovações intermédias. O HTML conserva os diálogos
originais, mas este percurso não os utiliza. Concluído significa execução
terminada, não aprovação artística ou editorial.

## Pedidos disponíveis

- `guardar texto: o texto a conservar` ou `@@ o texto a conservar`
- `verificar integridade de ficheiro` com anexo até 2 MB
- `converter para pdf` com anexo DOCX, ODT, RTF, TXT ou DOC até 2 MB
- `Quero converter este documento para PDF` com o mesmo tipo de anexo
- `procurar na biblioteca: música` ou `pesquisa na biblioteca sobre música`

O corpo de texto é conservado literalmente após o prefixo. Pedidos ambíguos,
negações e operações sem template são recusados antes da execução. Não há
classificador por pontuação nem tentativa de adivinhar comandos.

Os templates estão em `templates/`. Cada operação tem um YAML com os seus
passos. A conversão verifica o original, chama o LibreOffice, verifica que o
original não mudou, confirma o cabeçalho PDF e apresenta o resultado e SHA256.
Não promete comparação visual nem validade editorial do documento.

## Arranque e instalação

Requisitos verificados: Windows, Windows PowerShell 5.1, Dagu 2.21.0, SQLite 3.54.1 com FTS5 e LibreOffice.
O servidor usa apenas .NET/PowerShell e escuta em `127.0.0.1:8091`.
O LibreOffice é chamado através de `soffice.com`, com perfil separado e temporário.
O Python, Node e os antigos módulos Nexus não participam no funcionamento.
Node e Playwright são usados apenas nos testes.

Executar `Install-Folha.ps1 -SqliteExe CAMINHO_SQLITE` instala na conta Windows e cria o atalho Folha.
O atalho inicia o servidor local e abre a sessão no navegador.
Também é possível executar `Start-Folha.ps1 -OpenBrowser` diretamente.
Os parâmetros permitem escolher pasta de dados, porta e caminhos do Dagu.

Dados de utilização ficam em `%LOCALAPPDATA%\FolhaDagu`, fora do repositório.
Cada pedido conserva JSON de entrada, anexo original, YAML preenchido, estado,
registos e resultados. O `launch-url.txt` contém a sessão local e não deve ser
publicado. A sessão é renovada no arranque; pedidos sem sessão ou de outra origem
são recusados. Um reinício nunca volta a executar automaticamente um pedido.
Pedidos interrompidos ficam por verificar, com os registos conservados.

## As duas pastas e o índice

A pasta `templates/` contém as receitas. A pasta de dados contém `biblioteca/`,
com subpastas `wikis/`, `fontes/` e `regras/`. Um único `indice.sqlite3` contém
dois índices FTS5, `templates_fts` e `biblioteca_fts`. Antes de cada pedido, o
Shell confere os ficheiros e reconcilia adições, alterações e remoções no índice.
Essa reconciliação não apaga os ficheiros originais. Links de pastas não são seguidos.

Os comentários `# nexus-title`, `# nexus-terms`, `# nexus-match`,
`# nexus-attachment` e, quando necessário, `# nexus-extensions` descrevem o
catálogo dentro do próprio YAML. FTS5 encontra candidatos; expressões completas
determinam qual receita corresponde. Duas correspondências são ambíguas e não
executam nenhuma receita. O pedido nunca é tratado como SQL ou código Shell.

Os YAML continuam a ser código local autorizado: a pesquisa de fontes não pode
gerá-los ou substituí-los. O pedido conserva o SHA256 do template utilizado.

A biblioteca indexa texto UTF-8 `.md`, `.markdown` e `.txt`, até 2 MB por ficheiro.
Outros formatos precisam de extração de texto antes de serem pesquisáveis. Cada
pesquisa procura todas as palavras indicadas e devolve até 20 documentos com o
texto integral, sem recortes. Pesquisas com mais de 40 palavras distintas são
recusadas explicitamente. FTS5 não compreende semanticamente português irrestrito.

Guardar texto e concluir uma conversão/verificação arquiva o texto ou relatório
em `biblioteca/wikis/`. Pesquisar não arquiva outra cópia dos resultados, evitando
que as pesquisas se multipliquem dentro do próprio índice. As regras fornecidas
pelo utilizador são copiadas de `defaults/regras/` apenas se o ficheiro de destino
ainda não existir. Não são uma implementação dos workflows criativos futuros.

A conversão não tem um limite geral de duração. A conclusão depende do processo
real. Os limites de espera nos testes servem apenas para detetar falhas no teste.
Modelo, contexto, RAM e VRAM serão definidos e verificados por integração criativa.

## Validação

Com uma instância isolada de teste em funcionamento:

```text
node folha/tests/integration.mjs CAMINHO_DOS_DADOS_DE_TESTE
node folha/tests/browser.cjs CAMINHO_DOS_DADOS_DE_TESTE
powershell -File folha/tests/index.ps1 -TestDirectory PASTA_DE_TESTE
```

O segundo teste requer Playwright e Microsoft Edge. Os testes verificam a
seleção por regras, sessão/origem, conservação de UTF-8 e de texto semelhante a
código, SHA256 independente, conversão real por LibreOffice, descarga do PDF,
interface sem aprovações intermédias e recuperação do rascunho/anexo.

Ainda não estão ligados nesta versão os workflows de pesquisa web,
Open Notebook, escrita criativa, música ou vídeo. Não são simulados nem devolvem
sucesso fictício. A instalação local do Dagu mantém-se independente desta Folha.
