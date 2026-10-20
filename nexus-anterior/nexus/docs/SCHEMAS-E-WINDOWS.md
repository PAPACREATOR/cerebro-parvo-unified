# Schemas e Windows como hospedeiro

01/10/2026

## Correção demonstrada
INPUT: envelope de resultado com outcome/status. OUTPUT: aceitação apenas das combinações do processo verify. Lei: conflito/UNKNOWN/falha não são PASS. Dependências existentes: JSON Schema e pytest.

Antes: 12 FAIL e 6 PASS nos 18 testes específicos. O schema aceitava combinações contrárias à política YAML.
Correção: condicionais JSON Schema vinculam agreement a PASS, conflict/unknown a UNKNOWN, failure a FAIL. O ramo candidate não ganha autoridade nem aprovação. Manifesto de integridade atualizado para a alteração de desenvolvimento.
Depois: 69 testes Nexus PASS em 19,99 s, incluindo schemas válidos, política YAML e circuito Conductor real. Logs: work/schema-before.log e work/schema-after.log. O FAIL de recuperação após publicação Canonical continua aberto; estes PASS não o cobrem.

## Aproveitar o Windows
| Necessidade | Mecanismo existente | Prova necessária |
|---|---|---|
| Identidade de ferramenta | Conta padrão Nexus / token do processo | processo mostra SID esperado e não é administrador |
| Proteger cofres e código/leis | DACLs NTFS | ler/escrever proibidos recusados; permissões não alteráveis pela conta de ferramentas |
| Área de execução | pasta de trabalho autorizada por tarefa | ferramenta só recebe inputs previstos; outputs validados pelo Host |
| Limites e término de processos | Job Objects, sem breakaway permitido | limite real e término dos filhos ao terminar o job/Host; não equivale a sandbox de ficheiros |
| Auditoria de acessos quando necessária | SACL + auditoria Windows configurada | tentativa recusada produz evento; complementa proveniência Nexus |
| Trabalho especializado | executáveis instalados, PowerShell e APIs | saídas verificadas por contrato |

Fontes oficiais consultadas:
- https://learn.microsoft.com/en-us/windows/win32/secauthz/access-control-lists
- https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects

Não instalar serviço/base/framework para estas funções sem FAIL justificativo. Job Objects não conferem isolamento de rede, identidade ou filesystem por si só. Uma conta padrão não limita automaticamente todo o filesystem à pasta de trabalho: acessos herdados devem ser auditados. Porta loopback não autentica a conta Windows cliente. Nenhuma destas garantias deve ser anunciada antes do teste.

## Limites da prova
Esta correção valida coerência estrutural de estados, não veracidade do texto, independência das fontes nem segurança de uma IA. Wiki, isolamento efetivo da conta e cognição continuam pendentes. O Host mantém validação/gates; Conductor mantém execução. Não foi alterada a Constituição.
