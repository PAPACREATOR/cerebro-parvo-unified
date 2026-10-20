> **Estado atual (06-10-2026):** o texto abaixo conserva a evolução e os FAILs anteriores. O runtime atual já usa fronteira nativa Windows/AppContainer LPAC + Job Object para os processos lançados pelo Host, com gates reais de confinamento/autoridade em Windows 2022/2025. Provisioning externo continua deliberadamente bloqueado e não deve ser confundido com confinamento de runtime já provado.

# F008 — isolamento Windows (PENDENTE)


## Conferência do código atual — 05-10-2026

Runtime revisto: dcef003. Os parágrafos seguintes conservam o percurso de 01-10 e o PASS limitado das duas pastas; Conductor/interpret.yaml são referências históricas, substituídas no candidato por Python/MCP.

O Host atual ainda lança `subprocess.Popen` na identidade corrente; o servidor MCP e os adaptadores seguem essa execução. Não há ligação ao `Start-Process -Credential` deste ensaio, nem Job Object aplicado ao lançamento. O novo gate hostil real produziu 22 acessos proibidos ALLOWED e 2 controlos PASS. O [ponto de situação](PONTO-DE-SITUACAO.md) contém SHA, logs e limites.

O contrato continua a exigir execução restrita pelo Windows nos bastidores, mantendo a Folha simples. O utilizador aprova o que a autoridade exige; não gere manualmente permissões a cada tarefa. Uma conta dedicada e ACLs em duas pastas não provam rede, separação entre tarefas, restrição da bancada/modelo ou confinamento de todos os diretórios. A aprovação humana não concede automaticamente direitos gerais à tool.

Prioridade humana reforçada em 01-10-2026. O workflow interpret.yaml já está implementado; a fronteira de conta Windows não.

INPUT: conta padrão Nexus, área de trabalho atribuída por tarefa, ferramentas de leitura/execução, cofres e leis pertencentes ao Host/humano.
OUTPUT: testes reais demonstram escrita na área de trabalho e acesso negado aos cofres/leis pela identidade da ferramenta. Host entrega somente contexto permitido e valida outputs.
LEIS: IA sem autoridade; conta padrão sem administração; Human Gate só no Host; nenhuma migração de conhecimento sem restauro verificado.
DEPENDÊNCIAS: Windows LocalUser, ACL NTFS, processo com credenciais explícitas. Não inventar serviço permanente.

## Passos e testes

1. Criar conta padrão com palavra-passe introduzida pela pessoa na janela Windows; nunca em chat/log/Git.
2. Preparar área de ensaio com sentinelas sintéticas. Verificar SID e ausência no grupo Administradores.
3. Executar processo realmente como Nexus; provar escrita no diretório atribuído e bloqueio de leitura/escrita dos cofres e alteração de ferramentas/leis.
4. Tentar alcançar outra execução e dados fora do pacote; uma conta dedicada por si não garante isolamento entre execuções nem de rede. Registar limites e corrigir perante FAIL.
5. Só após PASS ligar a execução restrita ao Host/Conductor. Token de sessão e credenciais dos cofres não entram no processo.
6. Repetir para Notebook/Tiny: se continuarem na conta humana, o isolamento completo continua por provar.
7. Testar timeout, cancelamento, reinício e recuperação. Preservar os dados atuais até cópia/restauro demonstrado.

Estado atual: script interativo preparado, conta não criada na última verificação. Nenhum PASS de isolamento anunciado. O manifesto de hashes e os gates existentes não bloqueiam escrita direta por processos com os direitos do utilizador.

## Revalidação pedida — 01-10-2026

Cognitivo na cópia atual: PASS em 10.57 s; interpret.yaml executado por Conductor; Open Notebook/Tiny retornaram JSON candidato UNKNOWN, duas citações exatas, Canonical vazio e credencial temporária removida. A existência deste workflow foi confirmada no índice Git.

Isolamento: **FAIL reproduzível**. Um filho Python -I com process_environment do Host leu e alterou uma sentinela sintética numa pasta de cofre de ensaio. Mesmo utilizador mantém os seus direitos de ficheiros. Não foi tocado conhecimento real. A conta Nexus continua ausente na verificação. Próximo trabalho: corrigir esta fronteira, sem avançar para capacidades adicionais.

Este FAIL de requisito não desaparece com os 109 PASS da regressão existente: a suite cobre o comportamento implementado, não comprova isolamento de OS.

## Configuração nativa parcial — 01-10-2026

Conta padrão Nexus criada e membro de Users, sem associação direta a Administradores. Área sintética C:\ProgramData\NexusMinimal criada. Inspeção das DACL: herança protegida; Nexus Modify em work, ReadAndExecute em tools/laws; vaults sem ACE para Nexus. Host/humano, SYSTEM e Administradores mantêm controlo. Nenhum cofre existente foi migrado.

O teste por processo com credenciais ainda não produziu probe-result.json nem isolation-result.json. Serviço Secondary Logon estava ativo; não foram encontrados eventos CodeIntegrity recentes na consulta. A causa da interrupção ainda não está demonstrada; aguarda-se a mensagem da janela interativa. Não redefinir palavra-passe nem repetir criação cegamente.

**Estado: CONFIGURADO PARCIALMENTE / TESTE EFETIVO PENDENTE.** DACL inspecionada não é PASS de acesso negado. Host e Notebook continuam sem integração com a conta restrita.

## Diagnóstico dos lançamentos — 01-10-2026

Repetição com diagnóstico automático: Start-Process -Credential devolveu InvalidOperationException «O parâmetro está incorreto». Não há prova de password errada nem execução do filho. Não redefinir credenciais.

Alternativa nativa Agendador/S4U, tarefa temporária e RunLevel Limited: Register-ScheduledTask devolveu HRESULT 0x80070005 (Acesso negado), tanto com SID como nome explícito da conta. Foi confirmado admin=true, FullLanguage e serviço Schedule ativo. Não foi reduzida segurança/ACL nem desativada política. S4U evita password guardada, mas não deve ser confundido com firewall nem isolamento geral de rede.

Scripts test-isolation.ps1 e test-isolation-s4u.ps1 preservam o diagnóstico e não recriam a conta. **Continua FAIL de lançamento / isolamento efetivo NOT RUN.** A inspeção das ACL é válida; o percurso de execução restrita do Host ainda não foi ligado. Próximo diagnóstico deve identificar a causa Windows do erro de lançamento e da recusa de registo antes de novas tentativas. Não declarar estes scripts como instalação pronta.

## PASS real — duas pastas, identidade Nexus — 01-10-2026

Causa demonstrada do erro de lançamento com credenciais: o comando codificado anterior tinha **3216 caracteres**, acima do máximo de **1024** de CreateProcessWithLogonW. O teste mínimo usa comando de **610 caracteres**, sem alterar política de execução, ACL global, UAC ou antivírus.

Script: windows/test-two-folders.ps1. Resultado real:

- identidade do filho confere com o SID da conta Nexus: PASS;
- escrita na pasta allowed: PASS;
- leitura de protected/sentinel.txt: UnauthorizedAccessException;
- escrita de protected/sentinel.txt: UnauthorizedAccessException;
- sentinela protegida verificada pelo processo humano e intacta: PASS.

**O mecanismo nativo conta padrão + ACL NTFS está demonstrado em duas pastas sintéticas.** A recusa anterior do Agendador não precisou de ser contornada: ele não é necessário para este lançamento. Não foi instalada nova dependência nem concedida administração à conta.

Limites: ainda falta ligar a identidade restrita ao Host/Conductor e aos diretórios reais de trabalho. Notebook/Tiny continuam por rever sob a mesma fronteira. Este PASS não prova isolamento de rede, separação entre execuções, Job Object, backup ou restauro. Não migrar cofres reais antes dos testes. Os scripts longos anteriores ficam como evidência histórica de FAIL; usar o teste curto daqui em diante.

Fonte do limite nativo: https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-createprocesswithlogonw
