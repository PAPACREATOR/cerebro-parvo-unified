# Instruções correntes — Cérebro

Ler primeiro [STATUS](STATUS.md) e o [ponto de situação operacional](nexus/docs/PONTO-DE-SITUACAO.md), depois CEREBRO_CONSTITUTION.md, CEREBRO_ARCHITECTURE.md, DECISIONS.md e o contrato da tarefa. O [projeto auditado de 28/09](docs/PROJETO-FINAL-AUDITADO-2026-09-28.md) conserva a composição daquela data; não é uma ordem para reintroduzir Activepieces/Conductor no runtime candidato.

## Reconciliação operacional — 05-10-2026

A PR #23 e a branch `lab-open-notebook-avatar-20261004` são a continuação ativa. Kernel/Host/Store Python mantêm estado e política; a pessoa é autoridade máxima. MCP transporta; ferramentas externas devolvem propostas/evidência. Conductor/Spiff/YAML de execução foram retirados do ativo, conforme a PR #21 preservada. As referências a Activepieces abaixo aplicam-se à genealogia ou a integrações que o usem; não impõem uma dependência atual.

Manter um único documento de estado: `nexus/docs/PONTO-DE-SITUACAO.md`. Não recriar filas/handoffs removidos. Contratos, comparações, relatórios PASS/FAIL e histórico devem ser preservados. Antes de editar, conferir HEAD e comentários recentes; PASS anterior não cobre automaticamente um novo SHA. Limpeza documental não autoriza alterar arquitetura ou enfraquecer testes.

## Regra principal

Não defender uma tecnologia porque já foi escolhida. Comparar primeiro. Manter uma decisão apenas se continuar a ser a forma mais simples de preservar o comportamento exigido.

Aplicar sempre:

USE > ADAPT > CREATE.

## Autoridade

- A pessoa é autoridade final.
- Kernel/Host/Store governam e executam o runtime candidato; ferramentas externas executam apenas capacidades delimitadas.
- Open Notebook/tiny produz proposta/evidência; não decide autoridade.
- Ferramentas externas devolvem UNTRUSTED.
- Instrução humana atual prevalece sobre comportamento aprendido.
- Creative e Canonical têm autoridade distinta.
- Similaridade semântica nunca autoriza eliminação.
- Nenhuma ferramenta publica, apaga ou promove diretamente sem o portão aplicável.

## Implementação

- M1–M14 são responsabilidades/invariantes, não exigem 14 serviços.
- IMP-001–026 são contratos/testes da família de importação, não exigem 26 módulos.
- Preferir API/CLI/MCP/adapters finos de ferramentas maduras a código próprio.
- Não duplicar fora do Kernel regras que pertencem ao Core.
- Não criar adapter próprio quando uma interface estável existente resolve.
- Todo o processo deve ter explicação equivalente em linguagem natural.
- Open Notebook usa um único espaço cognitivo por defeito; contexto e sessão são delimitados por tarefa.
- A tiny recebe contexto temático, fontes permitidas, budget e schema de saída.
- SQLite não é um terceiro cofre; coordena eventos/IDs/relações/estado/índices.
- Markdown/formatos abertos materializam Creative/Canonical.
- Obsidian/Joplin/Logseq não são dependências obrigatórias.

## Método de trabalho

Implementar vertical slices curtas:

contrato -> implementação mínima -> testes positivos/negativos/adversariais -> regressão -> evidência -> PASS/FAIL/NOT RUN.

Separar sempre:

- desenhado;
- implementado;
- testado;
- integrado;
- aprovado.

Não transformar um PASS unitário em release.

Para G10 usar o desenho PREPARED -> materialização Markdown -> verificação de hash -> COMMITTED -> reconcile, mas não declarar fechado antes dos testes de crash/replay.

Não aceitar segredos em prompts, publicar automaticamente, dar auto-approve global ou aumentar permissões silenciosamente.

## Continuidade e testes — instrução humana de 04-10-2026

- Trabalhar no GitHub; Pedro executa os scripts no PC. Validação pessoal pendente
  não bloqueia implementação e testes que possam ser concluídos no repositório.
- Registar cada etapa em nexus/docs/PONTO-DE-SITUACAO.md: pedido, branch/commit,
  ficheiros, evidência, PASS/FAIL/NOT RUN, bloqueio e próximo passo.
- Para cada ligação alterada, testar ida (pedido -> execução -> resultado) e
  retorno (resultado -> processo/evidência -> fonte/pedido), além de erro,
  timeout/indisponibilidade quando aplicável, saída inválida e recuperação.
- Conferir que o retorno não repete ferramentas nem cria aprovação humana nova.
  Usar dados sintéticos e testar que falhas não promovem nem eliminam conhecimento.
- Declarar a cobertura e as exclusões; nenhum PASS parcial prova todas as ligações.
- Genealogia de 04-10: Conductor era o executor e o handoff da PR #7 relatava
  Spiff -> Conductor. A PR #21 documenta a substituição no candidato por Python.
  Não usar esta entrada histórica para repor executores removidos ou presumir
  que a instalação do PC já foi atualizada.
- Coordenar sessões por branches/PRs, preservando caminhos relativos e indicando
  commit de base e evidência. Espelhar código/documentação; excluir credenciais,
  ambientes, runtime e cofres. Consultar comentários recentes antes de editar.
