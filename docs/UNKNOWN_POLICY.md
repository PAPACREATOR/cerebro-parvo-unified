Siga GitHub.

Avança apenas com PRs pequenos, independentes e reversíveis.

Regra principal — TUDO-OU-NADA:
Antes de executar qualquer trabalho, o runner deve verificar as capacidades essenciais do sistema.
Se faltar alguma capacidade essencial, não tentes uma solução parcial, não uses alternativas improvisadas e não continues.
Deves abortar imediatamente com estado UNKNOWN.

UNKNOWN não é erro nem falha:
UNKNOWN significa “não tenho prova suficiente de que consigo executar esta tarefa”.
É o comportamento correto e seguro.
Nesse caso, o sistema deve devolver instruções claras em português simples, explicar o que falta e guardar o trace completo em run_dir.
Nunca transformes UNKNOWN em FAIL nem tentes contornar a verificação.

Fluxo obrigatório:
1. Receber o pedido e criar ./runs/{run_id}/ com request.json.
2. Escolher o runner correto: scripts/runner.sh em Linux/macOS ou windows/runner.ps1 em Windows.
3. Criar lock no run_dir para evitar execuções concorrentes.
4. Gravar runner.log.
5. Verificar capacidades essenciais antes de qualquer execução.
6. Se faltar algo essencial: devolver UNKNOWN, instruções amigáveis e trace completo.
7. Se tudo estiver OK: executar o processo, gravar artefactos e devolver OK.
8. No fim, remover o lock e devolver o código de saída correto.

Códigos de saída:
- 0 = OK: artefacto gerado, metadados e hash gravados.
- 2 = UNKNOWN: falta capacidade essencial ou o pedido é ambíguo. Não é falha.
- 1 = FAIL: erro real durante a execução, com logs e failure.json para diagnóstico.

Regras de segurança:
- Não alteres a arquitetura nem o formato do envelope JSON.
- Não faças merge automaticamente.
- Não apagues ficheiros.
- Não instales dependências globais.
- Não modifiques o arranque do Windows sem me mostrares primeiro o plano.
- Não uses soluções ad hoc para contornar capacidades em falta.
- Cada PR deve ter testes. Corre os testes que não exigem binários antes de considerares a tarefa concluída.

Como deves comunicar comigo:
- Não presumas que eu sei programar.
- Explica tudo em português simples.
- Antes de alterar, mostra-me o plano.
- Depois de alterar, diz: o que mudaste, que ficheiros tocaste, que testes correste, se passaram e o que pode ter ficado afetado.
- Se algo ficar UNKNOWN, explica exatamente o que falta e o que eu preciso de instalar ou confirmar.

Isto formaliza a regra de que UNKNOWN é uma paragem inteligente e controlada, não um problema a "resolver à força".
