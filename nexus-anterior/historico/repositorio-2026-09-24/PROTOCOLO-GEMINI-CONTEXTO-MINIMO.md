# Protocolo para usar Gemini sem entregar a ideia inteira

Data: 2026-09-22. Proposta de segurança e método, a aprovar por Pedro Alexandre Caldas Coelho antes da primeira chamada real. Não foi feita chamada à API.

## Escolha técnica

Para minimizar divulgação, a opção preferida é uma **chamada direta à Gemini API a partir de uma área temporária isolada**, não ligar a chave ao Cursor para lhe dar acesso à pasta do projeto. O cliente local recebe apenas um texto aprovado; não tem ferramenta de leitura do repositório, cofre, anexos, rede genérica, terminal ou upload de ficheiros. O resultado fica em quarentena para Codex e Pedro analisarem. Uma chamada direta envia o pedido à Google; não existe forma de obter resposta cloud sem lhe transmitir o conteúdo desse pedido.

A [API oficial](https://ai.google.dev/api/generate-content) aceita uma chamada de texto `generateContent`. A [Google recomenda](https://ai.google.dev/gemini-api/docs/api-key) uma variável de ambiente para a chave; nunca incluí-la no pedido, no código, no terminal registado, em Git, em capturas ou neste chat. A chave antiga publicada deve ser substituída e desativada antes de qualquer ensaio. A nova chave fica sob controlo de Pedro em AI Studio/Cloud Console. Não instalar cliente, configurar conta ou chamar a API sem verificar custo, quota e o texto exato a transmitir.

## Fronteira de divulgação

**Pode sair após revisão:** pergunta sobre documentação pública/licença; exemplo sintético de Python; função matemática ou serialização genérica; teste de unidade com nomes fictícios; mensagem de erro reduzida sem caminhos, nomes ou dados privados.

**Não sai:** nome e narrativa do produto, Constituição inteira, arquitetura, regras de soberania, combinação de ferramentas, desenho dos dois cofres, extrator/organizador próprio, fontes históricas, dossier jurídico, acervo do disco D:, conversas, dados pessoais, nomes de utilizadores, segredos e código de integração que revele a solução completa. Partir o dossier em vários pedidos não conta como proteção: o conjunto poderia reconstruir a ideia.

## Fluxo obrigatório por pedido

1. Codex escreve um objetivo genérico e um prompt curto, com dados fictícios, fora da pasta do produto. Etiqueta `PUBLICO` ou `SINTETICO` e regista o que será transmitido.
2. Pedro vê o texto literal e aprova ou pede redução. Sem aprovação, não há chamada.
3. Confirmar em AI Studio que a chave substituta e o projeto estão no nível gratuito, modelo elegível e quota disponível. Não ativar faturação.
4. Enviar **só** o texto aprovado numa chamada, sem anexos, histórico de chat, repositório, ferramentas, function calling ou pesquisa ligada. Não repetir automaticamente em caso de erro/limite.
5. Guardar localmente pedido, modelo, data, estado e resposta, mas nunca a chave. Marcar a resposta como proposta não confiável; não executar comandos nela contidos.
6. Codex verifica licença, correção e compatibilidade arquitetónica. Cursor/Codex só incorporam manualmente a parte aprovada dentro de uma SPEC; testes locais determinam PASS/FAIL.

Exemplo seguro para F0, ainda sujeito a aprovação: “Em Python 3.12, mostra um exemplo genérico de testes pytest para uma função que serializa um dicionário JSON com chaves ordenadas, rejeita NaN e produz bytes UTF-8 estáveis. Usa apenas dados fictícios. Não assumes detalhes de uma aplicação.” Isto pede conhecimento comum sem revelar os contratos completos do Cérebro Independente.

## Limites honestos

Esta separação reduz a informação divulgada, mas não é uma garantia matemática de confidencialidade ou exclusividade. A [quota gratuita depende do projeto e modelo](https://ai.google.dev/gemini-api/docs/rate-limits). Os [termos Google para EEE](https://ai.google.dev/gemini-api/terms) aplicam a regra de uso de dados da secção Paid Services também à quota gratuita para utilizadores no EEE, mas pedidos continuam a passar pela Google e podem ter retenção limitada por segurança. Se o produto vier a disponibilizar API Gemini a utilizadores no EEE, os termos atuais exigem Paid Services; isso é decisão futura de distribuição, não desta fase de engenharia. Não se utiliza a chave via Cursor para contornar limites: o [Cursor encaminha pedidos BYOK pelo seu backend](https://prod.cursor.com/help/models-and-usage/api-keys) e BYOK não transforma Hobby em Agent ilimitado.
