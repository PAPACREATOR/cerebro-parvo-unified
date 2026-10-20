# Matriz de controlo Nexus

01/10/2026. Cada linha distingue regra, prova e trabalho pendente.

Quadro histórico. Evolução posterior: [conta Nexus em duas pastas](F008-ISOLAMENTO-WINDOWS.md)
demonstrada, ainda sem ligação ao Host; [ODT→PDF](F007-LIBREOFFICE.md) integrado;
[circuito cognitivo textual](F005-COGNICAO.md) demonstrado no laboratório,
ainda sem configuração da nova entrada. Ver [ponto de situação](PONTO-DE-SITUACAO.md)
e [proveniência inversa](F013-PROVENIENCIA-INVERSA.md) antes de usar as pendências
antigas desta tabela como estado atual. Não houve nova inspeção do PC.

| Etapa | Entrada | Regra/validação | Saída/destino | Evidência atual |
|---|---|---|---|---|
| Receber | Texto/anexo | Schema, tamanho, processo permitido | Original conservado | Testado |
| Executar | Pedido autorizado | Conductor/YAML, ferramentas delimitadas | JSON | Circuito verify real testado |
| Comparar | Duas evidências | Acordo/conflito/unknown/falha | Candidato | Comparação de bytes testada; semântica/relacional pendentes |
| Validar | JSON | Estado coerente com outcome | Creative | Schema corrigido; regressão incluída |
| Aprovar | Versão apresentada | Sessão, ticket, confirmação, hash, destino | Canonical | Gate testado com decisões sintéticas |
| Recuperar | Pacote Canonical e estado após interrupção | Conferir aprovação, hash e proveniência existentes | COMMITTED ou BLOCKED/RECOVERY_REQUIRED | Correção passou; pacote corrupto é conservado e bloqueado |
| Proteger cofres | Processo de ferramenta | Conta Windows e ACL | Acesso mínimo | Pendente: conta Nexus ainda não criada |
| LibreOffice | ODT de ensaio | Artefacto PDF e falha sem input | PDF | Cinco conversões isoladas; integração no Host pendente |
| Zotero | Perfil separado local | Consulta/API e utilizador válido | JSON bibliográfico | Quatro probes PASS; biblioteca vazia, referência/importação/exportação pendentes |
| Open Notebook | Pedido autenticado | Autenticação/contrato | Resultado cognitivo candidato | API testada; Tiny e workflow cognitivo pendentes |
| Web | Consulta autorizada | Fontes, data, limites | Evidência candidata | Pesquisa usada pelo assistente; capability Host pendente |
| Wiki | IDs/fontes/versões/relações | Sem transferência de autoridade | Navegação do conhecimento | Proveniência mínima; wiki completa pendente |
| Backup | Cofres e proveniência | Restauro e hashes | Cópia recuperável | Pendente |

## Recuperação corrigida nesta ronda
A publicação concluída de Canonical seguida de falha na atualização do estado é reconciliada no reinício, verificando o pacote de aprovação existente. Não cria decisão humana nova. Dano no conteúdo, aprovação ou proveniência mantém os dados e bloqueia para recuperação. Esta verificação não autentica ficheiros contra alguém com permissão de os reescrever todos; isolamento Windows continua necessário.

Regressão Nexus: 73 PASS em 20,06 s (work/recovery-fixed.log). A prova refere-se às janelas de falha cobertas pelos testes; não prova recuperação de toda a corrupção possível.

## Sincronização
A sincronização entre ferramentas ainda não foi implementada. Perfil Zotero de ensaio sem conta cloud e sem autosync. Não se deve confundir API acessível com fluxo de dados integrado. As capacidades devem regressar por validação/Creative; nenhum sincronizador pode promover Canonical.

## Reanálise
Reavaliar a matriz quando houver alteração, nova capability ou falha. Conservar o FAIL anterior e a evidência da correção. A tabela ajuda a detetar lacunas; não é motor de execução nem substitui os testes.
