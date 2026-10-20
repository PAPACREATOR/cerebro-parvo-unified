> **Estado atual (06-10-2026):** contrato de instância única continua vigente. Referências a Conductor/Spiff na evidência são históricas. O arranque atual pertence ao runtime Kernel/Host/Store Python e a regressão moderna é conferida pelos workflows Nexus Windows/Confinement.

# F011 — uma instância por memória Nexus

Contrato de implementação, 03-10-2026. Não altera a arquitetura.

## Falha observada

Na baseline `1e9e612`, um Host cria um pedido RUNNING. Construir um segundo
Host com o mesmo diretório muda esse pedido para FAIL, mesmo que o primeiro
continue vivo. A reconciliação de arranque não distingue crash de concorrência.
Falha reproduzida com dados artificiais; não foram usados cofres pessoais.

## Contrato

- Dono: arranque da aplicação; continuidade e integridade M13.
- Entrada: diretório local de dados e porta HTTP.
- Antes de criar Host/Store ou recuperar estados, adquirir um bloqueio exclusivo
  do sistema operativo no diretório resolvido.
- Se outra aplicação o detiver, sair com código diferente de zero e mensagem
  clara, sem alterar pedidos, cofres ou o endereço da primeira Folha.
- Diretórios diferentes podem ser usados simultaneamente.
- Manter o bloqueio durante o serviço HTTP e até acabar a tarefa ativa num
  encerramento normal. Libertá-lo também se o arranque falhar.
- Uma queda do processo liberta o bloqueio no OS. No arranque seguinte, a
  recuperação existente pode marcar como interrompido um pedido realmente órfão.
- Não usar existência do ficheiro ou PID como prova de processo vivo. O ficheiro
  de coordenação permanece no disco; não o apagar para desbloquear a aplicação.
- Sem nova dependência, IA, promoção, eliminação de conhecimento ou rede externa.

## Critérios de PASS

Dois processos reais: rejeição da segunda aplicação, estado e URL intactos;
diretórios independentes; reentrada após encerramento e kill; falha de arranque
liberta o bloqueio; encerramento normal aguarda a tarefa ativa; manifesto íntegro.

Windows usa `msvcrt.locking` com `LK_NBLCK`; Unix usa `fcntl.flock` não bloqueante
para permitir ensaio e regressão neste ambiente. Não se declara PASS Windows a
partir do ensaio Unix. Fontes: documentação Python 3.12 de
[msvcrt](https://docs.python.org/3.12/library/msvcrt.html) e
[fcntl](https://docs.python.org/3.12/library/fcntl.html).

## Limites

O bloqueio protege o arranque cooperante por `python -m nexus.app`. Não é ACL,
sandbox, isolamento de ferramentas, proteção contra edição manual, nem suporte
a memórias numa pasta de rede/sincronizada. O uso direto de Host/Store continua
a exigir que o chamador detenha a exclusividade. Uma versão antiga da aplicação
que ignore o bloqueio não participa neste contrato.

## Evidência desta alteração

Baseline lida: `main` em `1e9e6127564a9247e562029552f73d56a8b9d3a7`.
Ficheiros descarregados conferidos pelos hashes dos blobs Git antes da alteração.

- Antes da correção: teste de duas aplicações CLI **1 failed**. A segunda
  aplicação abriu normalmente e não terminou no prazo de 5 segundos.
  Reprodução independente: abrir o segundo Host mudou RUNNING para FAIL.
- Depois da correção, Linux/Python 3.12: **10 passed** nos testes de arranque.
- Regressão aplicável neste ambiente: **1097 passed**. Inclui os 10 testes de
  arranque; não somar as duas contagens. Inclui leitura real de Markdown pelo
  Conductor fixado, contratos, cofres, aprovação e recuperação.
- Manifesto de 31 ficheiros: verificação passou. Workflow Windows: YAML validado.
- Suite completa num runner Windows/Python 3.12.10: **1154 passed, 28.14 s**,
  com integridade PASS, no commit `8b8100c7b72c83c07bd4770afb2693750b2b45a4`.
  [Execução e logs](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37158002429).
  Inclui os 10 testes de arranque, o ramo `msvcrt`, a porta exclusiva e o E2E HTTP.
  A contagem inclui variantes de contratos; não são 1154 tarefas de utilização.
  Windows local e instalação de Pedro: NOT RUN por este executor.

O primeiro runner reproduziu também duas Folhas a partilhar uma porta Windows:
`SO_REUSEADDR` não garantia exclusividade. A aplicação agora reserva a porta
com `SO_EXCLUSIVEADDRUSE` antes de bind. O teste de porta ocupada e de libertação
da memória após falha passou. [Comportamento documentado pela Microsoft](https://learn.microsoft.com/en-us/windows/win32/winsock/using-so-reuseaddr-and-so-exclusiveaddruse).

A falha independente de `verify` encontrada pelo runner foi corrigida em
[F012](F012-HASH-WINDOWS-ISOLADO.md). A auditoria documental anterior falhava por
faltar M1–M14 no README; a referência vigente foi reposta, sem mudar arquitetura.
47 ficheiros históricos preservados e 89 ligações verificadas; suites histórica
e de persistência: 34 e 11 PASS, respetivamente. Não somar às suites Nexus.

Comandos reproduzíveis, a partir da raiz do repositório:

```text
python -m pytest nexus/tests/test_startup.py -q -p no:cacheprovider -o pythonpath=.
python -m pytest nexus/tests/test_store.py nexus/tests/test_vaults.py nexus/tests/test_adversarial.py nexus/tests/test_kernel_review.py nexus/tests/test_notebook.py nexus/tests/test_schema_consistency.py nexus/tests/test_multimedia.py nexus/tests/test_startup.py -q -p no:cacheprovider -o pythonpath=.
python -c "from nexus.host import verify_integrity; verify_integrity()"
```

## Continuidade com o PC de Pedro

As alterações Spiff/Conductor, Host, estilos e contratos que ainda estão apenas
em `C:\Nexus\repositorio` não foram descarregadas nem sobrescritas. Este trabalho
é uma branch baseada no GitHub, não uma instalação no PC. Comparar primeiro as
versões locais, preservar o trabalho não commitado e só então conciliar `app.py`,
a nova entrada de `host.py` e o manifesto. Não copiar um manifesto antigo sobre
um adaptador mais recente nem substituir a pasta de dados.

Estado: implementado e testado em Linux e runner Windows; integração no PC
pendente. Não constitui aprovação de release nem conclusão do produto.
