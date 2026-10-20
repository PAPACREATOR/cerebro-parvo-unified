# Nexus — ensaios de comportamento

Data: 30/09/2026.

## Resultado
46 testes do Nexus passaram em 19,34 segundos, incluindo os testes anteriores e 11 casos adicionais. A regressão anterior do repositório terminou com 1103 PASS e 4 SKIP em 100,29 segundos.

## Ensaios adicionais
- 200 pedidos malformados, gerados com semente fixa 9302026: todos bloqueados sem criar execuções ou Canonical.
- Nomes com caminhos e caracteres de controlo: bloqueados.
- Conteúdo binário, Unicode e texto a ordenar aprovação: conservados como dados; sem promoção automática. Este teste não é um ensaio de resistência do modelo a prompt injection.
- 16 pedidos simultâneos, com execução controlada de teste: apenas um admitido.
- 16 confirmações simultâneas com a mesma autorização: uma única aprovação no armazenamento temporário de teste.
- Conteúdo alterado entre revisão e confirmação: aprovação bloqueada.
- Interpretação sem configuração cognitiva: BLOCKED, input conservado, Canonical vazio.

## Análise
O Host mantém os limites testados, recusa pedidos malformados e impede reutilização da mesma autorização. A execução concorrente foi ensaiada com uma ferramenta controlada; o circuito real Conductor/Windows também continua coberto pelos testes existentes. Não houve alterações ao código de execução nesta ronda, apenas novos testes.

Limites: os ensaios não provam segurança contra um processo com acesso de escrita aos mesmos ficheiros ou contra um administrador Windows. A Tiny não está configurada, por isso não foi avaliado comportamento de IA real. O arranque integrado e a recuperação de todas as formas de interrupção ainda não estão integralmente demonstrados.
