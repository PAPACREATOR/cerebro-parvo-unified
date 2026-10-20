# Ferramentas gratuitas e coordenação da equipa

Data da pesquisa: 2026-09-22. Autor da conceção e decisor: Pedro Alexandre Caldas Coelho. Este documento separa factos das fontes, estado testado nesta máquina e propostas de trabalho. Não altera a arquitetura do produto.

## Resultado essencial

| Recurso | O que permite | Limite ou condição | Estado local |
| --- | --- | --- | --- |
| Cursor Hobby | Editor, Composer e Agent com pedidos limitados, sem cartão | A quantidade de pedidos não é prometida aqui; observar o contador na conta | Instalador oficial assinado descarregado; aplicação e login não verificados |
| Chave própria Gemini no Cursor | Modelos Gemini suportados para pedidos de chat | Não substitui a subscrição nem torna o Agent Hobby ilimitado; Tab usa modelos do Cursor | Não configurada nem testada |
| Gemini API Free | Chamadas gratuitas a modelos elegíveis | Limites por projeto, modelo, minuto, tokens e dia; verificar em AI Studio | Chave antiga exposta no chat; não reutilizar |
| GitHub Copilot Free | Sugestões e chat/agent limitados em superfícies oficialmente suportadas | Até 2 000 sugestões mensais; utilização de chat/agent limitada; não é quota transferível para Cursor | Extensão descarregada no VS Code portátil; autenticação não verificada |
| Codex | Especificação, revisão, testes independentes e diagnóstico | Não há comunicação automática direta garantida com Cursor | Disponível nesta tarefa; F0 ainda não executada |

## O que a chave Google realmente faz no Cursor

O Cursor [aceita chaves da Google](https://prod.cursor.com/help/models-and-usage/api-keys) em Settings → Models para modelos Gemini da Google AI API. A própria documentação diz que as chaves personalizadas funcionam com modelos de chat, não com a conclusão Tab. Diz também que a chave é transmitida ao backend do Cursor em cada pedido para composição final do prompt, embora não seja guardada nos servidores depois do pedido. Os dados seguem também os termos do fornecedor escolhido; não presumir que o Privacy Mode do Cursor cobre a Google através de BYOK.

O [plano Hobby](https://cursor.com/pricing) continua com pedidos de Agent limitados. Na [resposta da equipa de suporte num caso de Hobby + chave Gemini](https://forum.cursor.com/t/cursor-free-plan-how-to-choose-gemini-model-with-byo-api-key/156175/3), o modo gratuito só dava seleção Auto, mesmo com chave própria. Isto é evidência de que BYOK não desbloqueia Agent ilimitado nem escolha livre de modelos. Como produto e regras mudam, confirmar na aplicação instalada com uma tarefa fictícia antes de planear capacidade.

## API Gemini: quota, segurança e uso em Portugal

Os [limites oficiais](https://ai.google.dev/gemini-api/docs/rate-limits) são definidos por projeto, não por número de chaves, e dependem do modelo e do nível da conta; o valor atual deve ser lido no AI Studio. Criar outra chave no mesmo projeto não multiplica a quota. Não associar faturação nem ativar plano pago sem decisão expressa de Pedro.

Os [termos da Google](https://ai.google.dev/gemini-api/terms) distinguem o uso gratuito geral da exceção para o Espaço Económico Europeu: para utilizadores no EEE, Suíça e Reino Unido, as regras de uso de dados da secção Paid Services aplicam-se também à quota gratuita. Portanto, a afirmação genérica anterior de que o conteúdo gratuito é usado para melhorar produtos **não se aplica automaticamente a Pedro em Portugal**. Isto não elimina trânsito por fornecedores, retenção limitada de segurança, nem substitui revisão contratual para dados confidenciais. Os mesmos termos exigem Paid Services para disponibilizar uma aplicação baseada na API a utilizadores no EEE; uso interno de desenvolvimento e distribuição do produto são situações diferentes.

A chave publicada anteriormente nesta conversa deve ser tratada como comprometida. A [orientação oficial da Google](https://ai.google.dev/gemini-api/docs/api-key) é criar uma substituta, desativar a antiga e auditar utilização; nunca pôr a nova chave em chat, ficheiro de projeto ou Git. Fazer a gestão diretamente em AI Studio/Cloud Console. Nenhuma chave foi aqui guardada ou testada.

## Copilot Free e coordenação

O [Copilot Free](https://docs.github.com/en/copilot/get-started/plans) é uma quota separada da do Cursor. O GitHub indica até 2 000 sugestões mensais e acesso limitado a chat/agent, sujeito ao contador atual da conta. A [lista oficial de IDEs suportados](https://docs.github.com/en/copilot/get-started/quickstart-for-using-github-copilot-in-your-ide) não inclui Cursor; por isso não instalar uma extensão por contorno nem prometer Copilot dentro do Cursor. Se Pedro quiser utilizá-lo, será num contexto suportado e com tarefa de revisão isolada, sem editar enquanto Cursor escreve.

**Via mais simples, sem instalar outro editor:** entrar na própria conta GitHub e abrir [github.com/copilot](https://github.com/copilot). A [instrução oficial](https://docs.github.com/en/copilot/how-tos/manage-your-account/get-started-with-a-copilot-plan) diz que Copilot Free permite conversar aí; se pedir ativação, selecionar o plano gratuito e confirmar que a conta mostra `Free`. Usar perguntas públicas ou fragmentos genéricos aprovados, sem carregar o repositório privado, fontes, arquitetura ou chaves. Isto cria um segundo parecer, não um canal automático de engenharia nem acesso ao disco local. A extensão anteriormente descarregada para VS Code não está autenticada; o website não depende dessa extensão.

O [Copilot Pro custa US$ 10 por mês](https://docs.github.com/en/copilot/get-started/plans), antes de eventuais impostos/conversão, e aumenta os créditos/limites e opções de modelos. Não são “10 euros” garantidos, nem esse pagamento cria comunicação direta Codex↔Copilot ou substitui os testes. Recomendação operacional: usar Free para revisão pontual, observar o limite real e só ponderar Pro se houver um bloqueio concreto. Nenhuma compra está autorizada por esta nota.

Papéis propostos para a primeira SPEC: Pedro decide e aprova custos; Codex fecha âmbito e critérios PASS/FAIL; Cursor, se instalado e com quota, é o único escritor; Copilot pode analisar uma alteração de código **depois** da escrita, se estiver autenticado num ambiente suportado; Codex revê o diff e repete testes; Pedro autoriza a fase seguinte. A comunicação é por ficheiros de SPEC, STATUS, resultados e revisão — não existe aqui canal automático Codex↔Cursor confirmado. Se a quota do Cursor acabar, parar e replanear; não trocar silenciosamente de escritor.

## Portas de verificação

1. **F-1 / ferramenta:** instalar e abrir Cursor, confirmar Hobby, ativar Privacy Mode, manter aprovação manual, verificar `.cursorignore` e os limites mostrados na conta. Não abrir acervo reservado para pedidos de IA.
2. **F-1 / chave:** substituir a chave exposta. Só depois, se necessário, experimentar chave nova com texto fictício e confirmar qual modelo/modo foi usado, que contador desceu e que a Google continua no nível gratuito. Não usar o dossier como teste.
3. **F0-001:** executar apenas `tasks/SPEC-F0-001.md`, guardar diff, comandos e códigos de saída; Codex repete os testes. Falha bloqueia a próxima SPEC.
4. **Depois de F0:** preparar as restantes SPECs por fase. Pesquisa de plugins, licenças, extração do cofre inicial e integração de Logseq/Activepieces são trabalhos próprios posteriores, não algo resolvido pela existência destas ferramentas gratuitas.

## Estado da arquitetura e documentação

Existe uma **linha de base coerente**, não um fecho integral: Constituição 0.1, arquitetura consolidada, plano F-1/F0–F9, decisões e primeira SPEC. Ainda faltam validação por implementação e testes, contratos detalhados de fases futuras, catálogo/licenças definitivas de plugins, desenho verificável do extrator/organizador inicial e testes reais da interface. Não apresentar a documentação atual como prova de produto concluído ou de exclusividade jurídica.
