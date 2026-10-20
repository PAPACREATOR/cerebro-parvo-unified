# Trabalho e ferramentas do GitHub

Pedro define finalidade, arquitetura e decisões normativas. O trabalho técnico segue microtarefas fechadas, revisão do código real e evidência reproduzível.

## Regra de execução

`contrato → micro-passo → teste direto → teste inverso/bloqueio → adversarial/limites → regressão do bloco → regressão total → E2E`.

Um FAIL é preservado e diagnosticado. Não se enfraquece o teste para obter verde.

## GitHub usado neste processo

- **Commits:** versões reversíveis e proveniência das alterações.
- **Pull request #23:** único ponto de continuação ativo do candidato atual.
- **Actions:** Linux e Windows conforme o gate; auditoria, Windows geral, Integration Stress, confinamento Windows e Avatar.
- **Issues:** lacunas e falhas específicas com critério de fecho.
- **Histórico:** decisões e implementações superseded permanecem acessíveis; limpar a árvore ativa não apaga evolução.

## Regras de coordenação

- conferir HEAD antes de editar;
- não assumir que PASS de um SHA cobre outro;
- não trabalhar sobre cópias locais paralelas sem necessidade;
- não reintroduzir Activepieces/Conductor/Spiff por leitura de documentos históricos;
- não alterar M1–M14 por conveniência de implementação;
- preservar FAIL → correção → PASS;
- usar dados sintéticos nos testes;
- não incluir segredos;
- distinguir desenhado, implementado, testado, integrado, aprovado e fisicamente validado no PC.

## CI e PC

CI prova apenas o âmbito executado no runner.

O PC físico fecha gates próprios:
- sincronização da única cópia;
- dependências reais;
- GPU/modelos;
- ferramentas instaladas;
- paths/permissões;
- relatórios locais.

Um PASS de CI nunca é convertido automaticamente em PASS do hardware pessoal.

## Ferramentas de programação

Codex/Copilot/Cline/Cursor podem implementar microtarefas delimitadas. Não lhes é delegada autoridade arquitetural nem decisão humana.

O runtime do produto continua local-first. GitHub é colaboração, histórico e evidência, não memória soberana do Nexus.
