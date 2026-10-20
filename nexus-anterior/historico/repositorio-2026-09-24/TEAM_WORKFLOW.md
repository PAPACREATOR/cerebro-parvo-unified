# Equipa e método de trabalho

## Papéis

- **Pedro Alexandre Caldas Coelho — proprietário e Gatekeeper:** confirma decisões estruturais, custos, publicação e passagem de fase.
- **Codex — engenheiro principal:** consolida contratos, prepara tarefas, verifica licenças, revê alterações, repete testes e diagnostica falhas.
- **Cursor Hobby (gratuito) — programador de implementação, sujeito aos limites do plano:** executa uma única SPEC pequena, com permissões limitadas, e para após apresentar resultados. O plano pago é apenas uma possibilidade futura, não uma condição para começar.
- **Cline — inativo:** permanece apenas como ferramenta instalada historicamente.
- **GitHub Copilot Free — revisor opcional, ainda não autenticado:** pode analisar uma alteração depois de Cursor parar, num ambiente oficialmente suportado. Não é segundo escritor nem extensão assumida para Cursor.

Nenhuma IA decide que o próprio trabalho está correto. Testes observáveis e revisão determinam PASS/FAIL.

## Ciclo obrigatório de cada tarefa

1. SPEC fechada com âmbito, entregáveis, PASS, FAIL e paragem.
2. Revisão da SPEC pelo Codex.
3. Implementação pelo Cursor.
4. Testes executados pelo Cursor.
5. Revisão de todos os ficheiros alterados pelo Codex.
6. Repetição independente dos testes pelo Codex.
7. Atualização de `STATUS.md` e `CHANGELOG.md`.
8. Decisão PASS/FAIL.
9. Só com PASS se prepara a tarefa seguinte.

## Regra de concorrência

Só existe um escritor automático por tarefa: Cursor. Codex pode inspecionar, mas não corrige silenciosamente antes de registar o resultado recebido.

Se a quota gratuita do Cursor acabar, parar e decidir o próximo escritor; a chave Gemini e a quota do Copilot não aumentam automaticamente a quota do Agent Cursor. Ver `FERRAMENTAS-GRATUITAS-E-EQUIPA.md`.

## Contexto permitido

Por defeito, ferramentas cloud recebem apenas a SPEC atual, os contratos consolidados e os ficheiros de código necessários. Fontes históricas, dossier jurídico, acervo do disco, chaves e dados pessoais ficam excluídos.
