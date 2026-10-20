# Plano de instalação e verificação

Instalar por necessidade e testar cada bloco antes do seguinte. Não instalar toda a arquitetura de uma vez.

## I0 — Inventário e segurança — PASS

- Ferramentas existentes inventariadas.
- Pasta do projeto e fontes protegidas.
- Sem billing ou serviços pagos.

## I1 — Ferramentas de desenvolvimento — em validação

- Python 3.12.10: encontrado.
- Node.js 26.7.0: encontrado.
- MinGit 2.55.0.windows.5: instalado de forma portátil, hash oficial e assinatura válidos.
- Visual Studio Code 1.138.0: instalado de forma portátil, assinatura Microsoft válida.
- Cline 4.1.19: instalado.
- GitHub Copilot 1.388.0: instalado a partir do pacote oficial do Marketplace.
- Ambiente virtual Python: criado; pytest ainda não instalado nem testado (pacotes descarregados não equivalem a instalação).

## I2 — Fornecedores de programação — requer verificação

- Cursor Hobby: instalar, autenticar e confirmar o plano gratuito antes de escrever código.
- GitHub Copilot Free: autenticar a conta GitHub apenas se for usado para revisão pontual num ambiente oficialmente suportado; não supor que funciona dentro do Cursor.
- Gemini API: chave antiga exposta no chat deve ser substituída antes de qualquer teste; usar só contexto mínimo aprovado e chamada direta isolada, se Pedro escolher esta ajuda. Não é pré-requisito de F0.
- Não ativar faturação, consumo adicional ou auto-approve global.

## I3 — Repositório e rollback

- Repositório Git: inicializado.
- Primeiro commit: pendente de email Git confirmado por Pedro.
- Checkpoints do Cline: históricos; Cline está inativo.

## I4 — Ferramentas do produto — ainda não instalar

Logseq Classic/File Graph, SQLite/FTS5, Activepieces, ferramenta de backup e outros componentes só entram quando a fase correspondente tiver versão, licença, caminho de integração e teste de instalação definidos. SQLCipher não é requisito do cofre final Markdown; proteção em repouso continua por decidir e testar. Instalação antecipada não conta como progresso.

## Critério para começar a primeira SPEC técnica

Python/pytest e testes de controlo devem estar verificados, e o escritor escolhido deve abrir o projeto com aprovações manuais e exclusões ativas. Primeiro commit continua dependente de identidade Git autorizada por Pedro. Não é necessário chamar Cline ou Gemini para iniciar a SPEC-F0-001. O objetivo corrigido e confirmado por Pedro é o protótipo técnico até **F4 (IA efémera)**, não a fase 4 funcional antiga.
