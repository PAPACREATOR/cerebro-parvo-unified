# Regra técnica — Python mínimo na Front Door

Data: 2026-10-04

## Regra

A Front Door não pode transformar-se num "cérebro Python".

Python só pode fazer cola determinística mínima:
- carregar configuração;
- validar schema;
- normalizar texto para matching;
- aplicar regex declarativas;
- construir/validar envelopes;
- chamar componentes existentes.

## Fora do Python

- prefixos: dados declarativos;
- regras de intenção: dados declarativos;
- processos: YAML;
- execução: JSON;
- conhecimento/pedido humano: Markdown;
- LanguageTool: adaptador existente;
- executores e ferramentas externas: processos delimitados pelo Kernel;
- estado/recovery/Human Gate: Kernel/Store.

## Proibido

- regras de negócio extensas hardcoded em Python;
- listas de intents duplicadas por vários módulos;
- lógica de autorização no parser;
- escolha de IA/backend no parser;
- reconstrução de estado por parser;
- novo framework Python quando uma peça existente resolve.

## Critério

Se uma alteração puder ser expressa como regra/configuração validada sem perder segurança, deve sair do Python.

O Python é infraestrutura de fronteira, não autoridade.
