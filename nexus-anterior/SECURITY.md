# Security Policy

## Reportar uma vulnerabilidade

Não publique segredos, tokens, dados pessoais ou detalhes exploráveis numa issue pública.

Para uma vulnerabilidade que possa expor dados, ultrapassar permissões, escrever em Canonical sem autorização, escapar da sandbox ou executar ações externas indevidas, contacte primeiro o proprietário do repositório através do perfil GitHub e forneça apenas a informação mínima necessária para estabelecer um canal privado.

## Âmbito prioritário

- bypass do Human Gate;
- escrita direta por ferramenta/IA em Creative/Canonical;
- path traversal;
- execução de comandos fora da sandbox;
- exposição de credenciais;
- injeção de autoridade em resultados UNTRUSTED;
- corrupção/replay incorreto do EventLog/SQLite/Markdown;
- escalada de permissões via MCP, adapters, ferramentas externas ou qualquer orquestração.

Não inclua credenciais reais em testes ou relatórios.
