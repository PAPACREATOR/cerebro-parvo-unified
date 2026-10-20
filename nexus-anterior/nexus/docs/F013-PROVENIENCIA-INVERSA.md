> **Estado atual (06-10-2026):** contrato vigente de retorno e proveniência inversa. Referências a Conductor/Spiff abaixo pertencem à implementação histórica; o caminho ativo usa Host/Store + runner/MCP e deve continuar a provar retorno sem reexecutar ferramentas nem criar aprovação nova.

# F013 — proveniência inversa e retorno à Folha

04-10-2026, Europe/Lisbon. Pedido humano: testar no sentido inverso e conferir
as wikis. Âmbito: circuito `verify` e pacotes já guardados pelo Nexus Minimal.
Não instala capacidades nem altera a arquitetura.

## Contrato vigente

[Decisão de 30-09](../../DECISIONS.md): proveniência percorre resultado ↔ processo
↔ contexto/evidência ↔ fonte/pedido. A [wiki de ligação](REVISAO-CONTRATOS-WIKI.md)
exige navegar das conclusões à evidência; não transfere autoridade nem funde os
dois cofres. Nesta etapa verifica-se o encadeamento dos ficheiros já existentes.

INPUT: estado de execução, original, pedido JSON, candidato/result/proveniência
em Creative e, quando aprovado, pacote Canonical com decisão humana existente.
OUTPUT: leitura verificável na Folha ou bloqueio explícito, conservando ficheiros.
RESPONSABILIDADES: identidade, genealogia, fontes/relações e recuperação; Host e
Store já existentes. Não se cria outro motor, cofre, índice ou serviço de wiki.

Percurso inverso:

1. Canonical → decisão ligada ao conteúdo e ao pedido.
2. Canonical → mesma proveniência de Creative, acrescentando apenas decisão
   e referências do pacote aprovado.
3. Creative → conteúdo/result.json/evidência/execução conservados.
4. Proveniência → processo, referências esperadas e hashes.
5. Pedido → texto ou bytes do anexo original, sem confundir a instrução textual
   com os bytes efetivamente enviados à ferramenta.
6. Reinício → histórico e resultado pela API da Folha, sem repetir Conductor,
   ferramenta, IA ou web e sem criar outra aprovação.

PASS exige integridade do percurso; fonte ausente/alterada ou proveniência
divergente bloqueia a aprovação/leitura validada. Em recuperação de Canonical:
`BLOCKED/RECOVERY_REQUIRED`, nunca apagar nem regenerar evidência.

## FAIL observado antes da correção

O primeiro ensaio novo teve **29 failed, 3 passed, 2 skipped em 1.84 s** no Linux.
Os dois SKIP eram ensaios reais Windows explicitamente marcados, não PASS.

- Original/pedido/result.json alterados ou em falta ainda permitiam promover.
- Reinício podia atribuir PASS apesar de fonte/Creative danificados.
- JSON de proveniência válido com caminho/hash/processo/execução falsos podia
  ser conservado como aprovado; não basta rejeitar JSON malformado.
- Folha podia devolver conteúdo Creative alterado junto do estado PASS.
- Fonte alterada depois de obter ticket não bloqueava a confirmação.

Ao alargar o mesmo teste à listagem HTTP, **dois casos falharam**: o histórico
ainda mostrava PASS/HUMAN_REQUIRED apesar de a abertura já bloquear. A listagem
agora verifica a cadeia e apresenta BLOCKED sem reescrever os dados conservados.

A revisão cruzada encontrou outra falha: `approval.json` ou `provenance.json`
contendo `{}`/`null` bloqueava o histórico mas encerrava a ligação HTTP ao abrir
o resultado. Quatro casos novos reproduziram o erro. A verificação Canonical
agora normaliza estes erros para BLOCKED; o detalhe devolve HTTP 403 com JSON de
erro e conserva o ficheiro danificado.

Nenhum ensaio usou dados pessoais, conta externa, modelo ou acervo real.

## Correção mínima

Store verifica original e pedido; verifica candidato, resultado, referências e
metadados; confere equivalência da proveniência Creative/Canonical. A leitura
HTTP (histórico e detalhe) e preparação/confirmação humanas reutilizam estas verificações. Os caminhos
de proveniência são comparados com nomes esperados, nunca abertos livremente.

Pedidos novos registam `request_sha256`; resultados novos registam
`result_sha256` e `provenance_sha256` no estado. Assim uma alteração isolada na
evidência ou no trace também é detetada. Pacotes antigos continuam a ter
verificação estrutural, original e conteúdo; os hashes antigos ausentes não são
inventados. Não se atribui retroativamente prova criptográfica a esses metadados.

UNKNOWN e o Human Gate mantêm-se. Não há eliminação, promoção automática,
reexecução de providers, nova dependência ou aumento de permissões.

## Evidência desta revisão

- Linux após revisão cruzada: **1148 passed, 4 deselected em 10.25 s** na regressão aplicável.
  Foram excluídos dois ensaios reais Windows novos e dois mocks antigos de
  LibreOffice que dependem de `CREATE_NO_WINDOW`, inexistente em Linux. Tentativa
  prévia incluindo esses dois mocks: 113 passed, 2 failed, 2 skipped em 3.66 s;
  falharam na constante Windows, não no novo encadeamento.
- Manifesto: `INTEGRITY=PASS`.
- Testes inversos: 12 tipos de dano × aprovação/reinício; quatro mutações de JSON
  Canonical válido; alteração após revisão; leitura HTTP antes/depois de aprovação;
  retorno após reinício com provider proibido; cópia para outra raiz e leitura;
  compatibilidade com pacotes antigos; dois circuitos nativos texto/anexo.
- Regressão Windows desta revisão: **1194 passed in 56.15s**, sem falhas ou skips,
  Python 3.12.10, commit `2870e3366bf9a7baefe392193e375c1ddaabfc11`.
  `INTEGRITY=PASS`. [Execução e logs](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37162599479).
  Logs conferidos em 04-10-2026; inclui a normalização dos quatro erros HTTP.

Uma revisão intermédia anterior à normalização dos quatro erros HTTP passou
**1190 testes em Windows em 43.25 s**; não cobre a última correção.

Comando Linux usado:

```text
python -m pytest nexus/tests/test_store.py nexus/tests/test_vaults.py nexus/tests/test_adversarial.py nexus/tests/test_kernel_review.py nexus/tests/test_notebook.py nexus/tests/test_schema_consistency.py nexus/tests/test_multimedia.py nexus/tests/test_startup.py nexus/tests/test_reverse_flow.py nexus/tests/test_office.py -q -o pythonpath=. -k 'not test_office_failure and not test_office_timeout_kills_tree and not test_real_windows_result_back_to_original_and_folha_after_restart'
```

Windows: o workflow Nexus Windows executa toda a suite `nexus/tests`, incluindo
os dois ensaios reais novos. O teste entra por HTTP, executa Conductor/PowerShell,
aprova com confirmação sintética, percorre referências até aos bytes originais e
reinicia Host para voltar à Folha sem ferramenta. Não é teste visual do navegador.

Verificação adicional dos ficheiros de documentação: 25 Markdown em `nexus/docs`,
nove ligações locais a ficheiros e nenhuma ligação partida. Isto não valida
âncoras, links externos, instalações ou a verdade dos relatos históricos.

## O que falta para a wiki e o programa

Esta prova é rastreabilidade de um pacote, não a wiki relacional completa:
identidade estável de blocos, backlinks, relações entre projetos, contradições,
renomeações e espelho automático continuam por implementar/provar. Os dois hashes
do workflow verificam bytes; não são comparadores semânticos nem verdade factual.

A Folha ainda não apresenta navegação clicável pela proveniência; mostra o
resultado e o histórico. Um resultado explicitamente BLOCKED pode continuar a
apresentar material conservado para inspeção; a descarga PDF verifica os bytes do
artefacto, não promete validar toda a genealogia. Não interpretar esses acessos
como aprovação. O próximo contrato de wiki deve definir a leitura das fontes.

Os hashes novos vinculam o resultado e o trace guardados no pacote Creative.
Os ficheiros brutos `execution.stdout.json`/stderr são diagnósticos separados;
a alteração isolada desses logs não é detetada por esta cadeia de hashes.

A cópia/restauro usa um pacote sintético para outra pasta. Não valida estratégia
de backup do PC, disco externo, toda a instalação ou recuperação de todas as falhas.
Alterações coerentes de todos os ficheiros/hashes por alguém com os mesmos direitos
continuam fora desta proteção; conta Nexus/ACL permanece por ligar ao Host.

Open Notebook/tiny, Spiff e dependências que só estão no PC não foram modificados
nem novamente testados. O [ponto de situação](PONTO-DE-SITUACAO.md) distingue essa
instalação das provas do repositório. Não há percentagem de conclusão fundamentada.
