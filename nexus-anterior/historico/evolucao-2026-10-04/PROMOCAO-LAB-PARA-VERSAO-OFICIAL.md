# Promoção do Nexus-Lab para nova versão oficial

Data: 2026-10-04

Decisão humana: o laboratório não serve para copiar alterações isoladas para a instalação antiga. O laboratório é a futura versão completa.

## Modelo

- `C:\Nexus`
  - versão anterior conhecida;
  - fica congelada;
  - não recebe experiências;
  - serve apenas de referência e rollback.

- `C:\Nexus-Lab`
  - local principal de construção, instalação, integração e testes;
  - recebe o trabalho novo completo;
  - pode ser recriado/testado sem contaminar a versão anterior;
  - contém a futura versão oficial quando todos os gates passarem.

## Fluxo

`GitHub -> C:\Nexus-Lab -> instalar/configurar -> testar microprocessos -> testar blocos -> testar Nexus completo -> testes práticos -> hardening -> PASS FINAL`

Depois do PASS FINAL:

1. tirar snapshot/hash completo de `C:\Nexus` antigo;
2. tirar snapshot/hash completo do `C:\Nexus-Lab` aprovado;
3. registar SHA Git, versões, dependências, ACLs e relatório final;
4. parar processos Nexus;
5. preservar a versão antiga para rollback;
6. promover o conteúdo aprovado do Lab como **nova versão oficial do Nexus**;
7. arrancar a nova versão e repetir smoke/regressão pós-promoção;
8. só depois marcar a promoção como concluída.

## Regra

Não fazer sincronização cega Lab -> Nexus durante desenvolvimento.
Não fazer cherry-pick de ficheiros individuais para a instalação antiga só para a manter atualizada.
O objetivo é terminar uma versão coerente no Lab e promovê-la inteira depois de aprovada.

## Gates antes de o Lab virar oficial

- arquitetura/leias intactas;
- integridade PASS;
- testes núcleo PASS;
- testes por bloco PASS;
- testes bidirecionais PASS;
- crash/restart/idempotência PASS;
- Human Gate PASS;
- proveniência PASS;
- capabilities externas PASS;
- segurança por processo PASS;
- regressão Windows real PASS;
- testes práticos Nexus completo PASS;
- snapshot/rollback demonstrado;
- hardening final PASS.

Estado atual: `C:\Nexus-Lab` ainda precisa de criação/execução real no PC.
