# Wiki de instalação Nexos — estado verificado

**Começar pelo [ponto de situação revisto](PONTO-DE-SITUACAO.md).**

## Revisão das ligações — 04-10-2026

[F013 — proveniência inversa](F013-PROVENIENCIA-INVERSA.md) testa a ligação de um
resultado aprovado até ao pedido/original e o retorno à API da Folha após reinício,
sem executar outra vez o provider. Falhas foram reproduzidas e corrigidas; a
regressão nativa Windows desta revisão ainda aguarda execução. A wiki relacional,
backlinks e espelho automático continuam pendentes. Os relatos de C:\Nexos abaixo
conservam a inspeção anterior; não significam que o PC foi atualizado por este PR.

## Entrada
Pasta: C:\Nexos. Atalho no ambiente de trabalho: Nexos.
Aplicação em aplicacao/nexus; dados da Folha em dados; documentação em documentacao.
16 controlos da instalação passaram: Folha, reutilização do Host, sessão,
verificação determinística, revisão de português, ODT→PDF, download e bloqueios.
O Canonical da instalação permaneceu vazio.

## Fundação
- Constituição e contratos: nexus/laws e nexus/schemas.
- Processos executados pelo Microsoft Conductor: nexus/processes.
- Primeira família: nexus/families/multimedia/som.md e imagem.md.
- Som e Imagem têm contrato e leitura testados; geração ainda não integrada.
- Sem aprovação humana explícita não há promoção para Canonical.

## Localizações reais
Nem todas as dependências foram deslocadas: o Python/Conductor, os modelos e
os serviços Notebook continuam no laboratório anterior. O atalho depende desse
Python. Não apagar essa pasta. LibreOffice e Java permanecem em Program Files.
A pasta Nexos é um ponto de entrada funcional, ainda não um pacote portátil.

## Pendências
- Configuração secreta do Open Notebook não copiada para a nova instalação.
- Isolamento da conta Nexus comprovado em duas pastas, ainda não ligado ao Host.
- Som/imagem: instalar e medir ferramentas, depois integrar.
- Zotero, web, Publisher e contas externas não têm circuito integrado comprovado.
- Backup/restauro e wiki espelhada automaticamente continuam por demonstrar.

Estado de testes não equivale a perfeição, segurança completa ou conclusão.

## Bancada cognitiva
Prompt literal v2: 6/6 ensaios sintéticos passaram no laboratório existente.
A configuração com credencial continua fora da nova pasta Nexos.
