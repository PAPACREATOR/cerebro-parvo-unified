# Fecho da fase conceptual — instrução para Codex

Data: 2026-09-23  
Estado: arquitetura congelada como hipótese; **não implementar ainda**.

## Conclusão desta fase

Há atualmente mais fundamento técnico para esperar uma versão funcional do Cérebro Independente do que para esperar impossibilidade técnica. Isto **não é validação experimental**.

Intervalos epistemológicos preliminares, não probabilidades estatísticas calibradas:

- Núcleo mínimo funcional: **85–95%**.
- Arquitetura completa tecnicamente funcional, admitindo correções: **70–85%**.
- Cumprimento simultâneo de toda a visão (baixo hardware, instalação simples, linguagem natural, adaptação humana ampla, Tiny LLM competitivo, recuperação, baixo consumo e sandbox): **55–70%** antes de protótipo/benchmark.

O baseline histórico global de aproximadamente **85% lógico-técnico preliminar** mantém-se. Não deve ser aumentado por literatura ou compatibilidade conceptual.

## Cenário de trabalho

`ideia central funciona → algumas hipóteses/componentes falham ou custam demasiado → arquitetura é corrigida/simplificada → sistema funcional`

O risco dominante deixou de parecer “impossibilidade técnica” e passou a ser **complexidade excessiva**.

## Regra matemática de redução

Para cada componente `c`:

`ΔV(c) = V(Sistema com c) − V(Sistema sem c)`

Se remover `c` mantém todas as invariantes obrigatórias e não reduz o valor medido, `c` é candidato a eliminação.

Não presumir necessários:
- segundo SQLite;
- quatro comparadores A/L/S/G separados;
- Activepieces;
- Docker;
- qualquer LLM/modelo específico;
- separação física particular das memórias.

Todos devem justificar contribuição marginal por teste.

## Invariantes obrigatórias

Estas propriedades não podem ser compensadas por velocidade, RAM ou conveniência:

1. autoridade final humana;
2. promoção canónica requer aprovação humana;
3. `AIOutput = Proposal`;
4. IA é componente não confiável, substituível e em sandbox;
5. IA não escreve diretamente nas memórias, objetivos, regras ou permissões;
6. operações relevantes têm proveniência/auditoria/replay quando aplicável;
7. núcleo continua útil sem IA;
8. memória criativa persiste após consolidação;
9. canónico pode informar o criativo, nunca limitá-lo;
10. interface humana privilegia linguagem natural e esconde estrutura técnica;
11. adaptação à pessoa não pode transformar comportamento observado em objetivos soberanos;
12. instalação, manutenção e recuperação fazem parte da simplicidade.

## Próxima fase

Não continuar a perguntar “parece que funciona?”. Converter as hipóteses em testes.

Para cada hipótese/componentização medir:
- VALIDATE;
- CORRECT;
- INVALIDATE.

Campos sem dados devem permanecer **NÃO MEDIDO**. Não inventar resultados.

Prioridades experimentais:
1. 1 SQLite vs 2 SQLite;
2. ablações das 16 combinações A/L/S/G;
3. Python-only vs Python + Activepieces;
4. AppContainer/LPAC vs Docker sob a mesma carga e os mesmos ataques;
5. No-AI vs Tiny vs Tiny+contexto/arquitetura vs modelo maior;
6. memória simples vs Creative+Canonical;
7. instalação/recuperação em máquina limpa por utilizador não técnico;
8. benchmark de linguagem natural e adaptação a utilizadores diversos;
9. objective-drift/goal-traceability;
10. sandbox: filesystem, rede, credenciais, processos, escrita direta, GPU/CUDA e IPC.

## Regra para Codex

**Não implementar a arquitetura neste momento sem nova instrução explícita.**  
Usar este documento para preservar o estado da investigação e preparar especificações/benchmarks quando solicitado.

A pergunta da próxima fase é:

> Qual hipótese falhou, qual sobreviveu, quanto custou e qual é a arquitetura mínima suportada pelos dados?
