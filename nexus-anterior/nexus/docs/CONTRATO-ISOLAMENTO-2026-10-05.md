# Isolamento de ferramentas — contrato e gate de aceitação

Pedido humano de 05-10-2026: nenhuma ferramenta/IA pode mexer no Kernel, no circuito Creative/Canonical ou fora do espaço autorizado; instalação não concede autoridade sobre o Windows.

## Autoridade e âmbito

Este contrato verifica invariantes existentes de isolamento, autoridade humana e proveniência; não cria módulos nem redesenha M1–M14. Kernel/Host/Store recebem e validam resultados. A pessoa define o âmbito autorizado. A ferramenta só deve receber os inputs selecionados e escrever no espaço de trabalho/output atribuído. Criar um resultado não autoriza alterar código, leis, cofres ou ficheiros pessoais.

Resultados legítimos podem entrar em Creative pelo writer do Host. Isso é diferente de a ferramenta escrever diretamente no cofre. Canonical continua sujeito a decisão humana. Não prometer literalmente zero leitura de bibliotecas do Windows: carregar um executável exige leituras do sistema; o requisito de confinamento aqui é impedir alterações não autorizadas e acesso a dados não fornecidos.

## Dois níveis de prova

1. Aplicação: sessão, schema, allowlist MCP, ticket de aprovação, alteração de candidato, persistência e recuperação. Testes existentes em test_adversarial.py, test_vaults.py e test_mcp_client.py.
2. Sistema operativo: ferramenta comprometida não consegue alterar Kernel/cofres/outros ficheiros, mesmo ignorando schemas. Novo gate separado em nexus/security_tests/test_confinement_gate.py.

PASS do primeiro nível não prova o segundo. Hashes detetam alterações; não retiram direitos de escrita. -I, cwd, ambiente reduzido e localhost não são sandbox de ficheiros.

## Ensaio reproduzível Windows

O teste chama Host._run real com um pedido verify criado pelo Store. Na fronteira subprocess.Popen substitui exclusivamente o payload do worker por um programa de ensaio; mantém cwd, env, flags e identidade escolhidos pelo Host. Não altera o runtime nem finge bloqueios de I/O. A substituição modela uma ferramenta permitida mas comprometida, não demonstra que a interface aceite código arbitrário.

Todos os alvos são sentinelas artificiais numa área temporária marcada:

- cópia conceptual de Kernel (não modifica o código do repositório);
- pastas Creative e Canonical de um Store descartável real;
- pasta artificial irmã da instalação, representando dados externos;
- diretório de trabalho atribuído pelo Host, como controlo positivo.

São 20 tentativas de alteração proibida (quatro áreas × criar/sobrescrever/apagar/renomear/criar pasta), duas tentativas de leitura não autorizada nos cofres e dois controlos: escrever no trabalho permitido e rejeitar envelope inválido. Total: 24 testes. O processo tenta agir antes de devolver um envelope inválido: rejeitar a resposta não pode desfazer uma escrita já permitida pelo SO.

PASS exige DENIED por acesso negado e sentinelas intactas; ficheiro inexistente, erro de execução, timeout ou ausência de relatório não contam como proteção. Não usar xfail, skip ou continue-on-error para tornar este gate verde. O workflow guarda JSON e JUnit mesmo com FAIL.

Comando (Windows, Python 3.12 e requirements.txt + pytest 9.1.1):

```powershell
python -m pytest nexus/security_tests/test_confinement_gate.py -q -o pythonpath=.
```

Workflow: Nexus Windows Confinement Gate. É separado da regressão funcional para tornar a ausência de isolamento visível, sem a esconder num PASS funcional. Não é teste no PC de Pedro nem prova universal contra todas as formas de evasão.

## Inspeção da baseline 46a1090

- host.py usa subprocess.Popen na identidade corrente; não seleciona token restrito, AppContainer, conta isolada ou máquina virtual.
- setup-isolation.ps1/test-isolation.ps1/test-two-folders.ps1 são ensaios NTFS separados; não são chamados pela fronteira de execução do Host.
- install-media-tools.ps1 pode chamar winget para Git/uv e uv python install 3.10; o script não fixa todas as caches/perfis sob ToolsRoot. Portanto não cumpre demonstravelmente a promessa de só escrever na pasta de instalação.
- O teste novo não executa instaladores de terceiros nem escreve no registo/serviços/arranque do Windows. Esses vetores, rede, subprocessos descendentes, links/junctions e toda a instalação física continuam NOT RUN nesta etapa.

## Critério de avanço

Se houver acesso proibido, registar FAIL real e bloquear a declaração de isolamento. Não passar à instalação no PC como se fosse segura. A correção terá de aplicar uma fronteira de SO à execução real (e separar instalação de execução), repetindo estes ataques e os gates restantes. Não corrigir com prompts, permissões mais largas, sleeps ou apenas redirecionamento de caches.

O desenvolvimento de testes em laboratório está autorizado. Criar contas/permissões no PC, alterar políticas Windows ou instalar programas no PC não foi executado por esta tarefa.

## Releitura do percurso de execução — 05-10-2026

O código publicado em dcef003 foi conferido desde Host/Store/arranque até runner, MCP, adaptadores, comandos avatar e instaladores Windows. O resultado real do gate é 22 acessos proibidos ALLOWED e 2 controlos PASS. O detalhe operacional fica no [ponto de situação único](PONTO-DE-SITUACAO.md).

A direção já definida é aproveitar a segurança Windows para fazer cumprir as regras do Nexus. Kernel/Host/Store validam; mecanismos nativos restringem a execução; a Folha mantém linguagem normal. A arquitetura conceptual não é reaberta por esta revisão. Contas, ACLs e limites técnicos são infraestrutura interna; ações que exigem autoridade humana continuam a ser apresentadas de forma compreensível.

A instalação e a execução da bancada/modelo têm de ser verificadas separadamente. Ambiente reduzido, perfis por tarefa, grupos de processo, allowlist MCP e hashes conservam utilidade, mas nenhum destes controlos já presentes muda sozinho os direitos de ficheiros da identidade corrente. Scripts sintéticos de conta/ACL existentes são evidência de um mecanismo, não integração automática no Host.
