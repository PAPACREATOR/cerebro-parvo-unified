# Matriz de Testes

| ID | Comportamento | Teste | Estado | Último resultado | Observação |
|----|---------------|-------|--------|------------------|------------|
| C01 | Ingestão de ficheiro normal | Por localizar/criar | NÃO TESTADO | — | Revalidar no HEAD atual |
| C02 | Preservação byte-a-byte | Por localizar/criar | NÃO TESTADO | — | Inclui binário e Unicode |
| C03 | Hash da entrada e verificação final | Por localizar/criar | NÃO TESTADO | — | Hash não pode substituir verificação de bytes |
| C04 | Estado PREPARED antes da escrita final | Por localizar/criar | NÃO TESTADO | — | Persistência observável |
| C05 | Ficheiro temporário + fsync | Por localizar/criar | NÃO TESTADO | — | Sem mocks de I/O |
| C06 | os.replace atómico + fsync do diretório pai | Por localizar/criar | NÃO TESTADO | — | Validar por filesystem real |
| C07 | COMMITTED só após verificação final | Por localizar/criar | NÃO TESTADO | — | Nenhum sucesso antes |
| C08 | Crash antes do commit | Por localizar/criar | NÃO TESTADO | — | Processo real/interrupção real |
| C09 | Crash após replace antes de COMMITTED | Por localizar/criar | NÃO TESTADO | — | Reconcile obrigatório |
| C10 | Replay/reconcile idempotente | Por localizar/criar | NÃO TESTADO | — | Repetição sem duplicar efeitos |
| C11 | Proveniência sem alterar conteúdo | Por localizar/criar | NÃO TESTADO | — | Histórico íntegro |
| C12 | Original nunca apagado | Por localizar/criar | NÃO TESTADO | — | Eliminação bloqueada no MVP |
| C13 | Ficheiro vazio | Por localizar/criar | NÃO TESTADO | — | Caso limite |
| C14 | Unicode | Por localizar/criar | NÃO TESTADO | — | Bytes preservados |
| C15 | Binário arbitrário | Por localizar/criar | NÃO TESTADO | — | Sem decode implícito |
| C16 | Ficheiro grande | Por localizar/criar | NÃO TESTADO | — | Limites reais |
| C17 | Ficheiro inexistente | Por localizar/criar | NÃO TESTADO | — | Falha explícita |
| C18 | Path traversal ../ | nexus/tests/test_paths_100k.py + teste específico por validar | NÃO TESTADO | — | Não herdar PASS anterior |
| C19 | Symlink malicioso | Por localizar/criar | NÃO TESTADO | — | Segurança |
| C20 | Colisão/alteração de hash | Por localizar/criar | NÃO TESTADO | — | Detetar adulteração |
| C21 | Concorrência | Por localizar/criar | NÃO TESTADO | — | Sem corrupção |
| C22 | Permissões restritas | Por localizar/criar | NÃO TESTADO | — | Falha segura |
| C23 | Core + persistência E2E | Por localizar/criar | NÃO TESTADO | — | Ponta a ponta |
| C24 | Regressão completa | python -m pytest ... | NÃO TESTADO | — | Só marcar após execução real |
