# F-1-001 — Instalação e verificação do ambiente

## Objetivo

Confirmar que o ambiente mínimo consegue criar um projeto Python isolado, instalar pytest e executar um teste local trivial. Não implementar o Cérebro Independente.

## Ações

1. Criar `.venv` com Python 3.12.
2. Atualizar pip dentro da `.venv`.
3. Instalar pytest apenas na `.venv`.
4. Registar versões de Python, pip e pytest.
5. Criar o teste temporário apenas em `work/` ou executar uma verificação sem adicionar código ao produto.
6. Confirmar que o teste passa.

## PASS

- `.venv` existe dentro do projeto e está ignorada pelo Git.
- Python da `.venv` é 3.12.x.
- pytest executa e um teste de controlo passa.
- nenhum ficheiro de produto foi criado.

## FAIL

- instalação global de pacotes Python;
- billing, cloud ou conta paga;
- alteração da arquitetura;
- início de F0.

## Paragem

Registar resultado em `STATUS.md` e parar.
