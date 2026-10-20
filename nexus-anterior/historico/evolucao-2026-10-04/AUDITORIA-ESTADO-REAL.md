# Auditoria do estado real — Nexus

30/09/2026

## Comprovado
- 51 testes Nexus passaram em 19,93 segundos. Incluem circuito Conductor/Windows, contratos, gates, concorrência, conservação de originais e candidatos, conflitos/UNKNOWN e falha simulada antes de publicar Canonical.
- Última regressão do código preexistente: 1103 testes passaram, 4 ignorados. Não foi repetida nesta auditoria porque só se acrescentaram testes Nexus desde essa execução.
- 13 ficheiros conferidos pelo manifesto de integridade.
- LibreOffice e Zotero instalados pelas distribuições oficiais, com hash dos instaladores validado pelo winget.
- LibreOffice: cinco conversões ODT→PDF produziram ficheiros com assinatura PDF; input inexistente falhou sem artefacto. Ainda não é validação visual ou semântica do PDF, nem integração pela Folha.
- Open Notebook: acesso sem autenticação recusado; acesso autenticado aceite; contrato inválido recusado.

## Limitação reproduzida
Um processo filho, com o ambiente reduzido usado pelo Host, conseguiu ler um ficheiro sintético acessível à mesma conta Windows. Portanto, ambiente reduzido e allowlist não equivalem a sandbox de filesystem. Creative/Canonical têm separação lógica e gate na aplicação, mas não foi demonstrado isolamento de escrita por identidade Windows/ACL. Não expor acervo real a código arbitrário sob a alegação de que já existe isolamento.

O manifesto verifica alterações em ficheiros listados, mas não é raiz de confiança contra quem possa alterar o próprio manifesto e código sob a mesma conta.

## Incompleto
- Tiny: nenhum modelo configurado.
- Workflow interpret.yaml: inexistente. O ramo cognitivo bloqueia sem configuração; não foi demonstrado E2E cognitivo.
- Zotero: instalado; arranque, biblioteca de teste, API e bibliografia ainda não ensaiados.
- Pesquisa web: usada nesta conversa para documentação; não integrada como capability Nexus.
- LibreOffice: testado isoladamente; não integrado ainda ao workflow/Host.
- Arranque integrado de todos os componentes e recuperação de todas as janelas de crash: pendentes.
- Restauro de backup dos cofres e resistência a corrupção de disco: não demonstrados.
- Documentos históricos mencionam SQLite interno e espelho. Não foram adicionados ao Nexus Minimal; qualquer requisito pendente tem de ser conciliado com a especificação atual, sem introdução implícita de componentes.

## Conclusão
Existe uma base determinística funcional e testes úteis. Não existe ainda prova do conjunto completo, da cognição nem de isolamento dos cofres perante processos da mesma conta. A frase “as permissões impedem o agente de aceder aos cofres” não pode ser usada para o estado atual. Próximo trabalho: concluir ensaios das ferramentas em dados artificiais e definir/verificar a fronteira Windows antes de dar capacidades ao modelo.
