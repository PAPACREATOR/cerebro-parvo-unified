# Nexus — organização e próximas fases

Revisão de 01-10-2026. O código atual está na pasta `nexus/` do repositório público. Não está tudo instalado nem tudo integrado.

Inventário histórico dessa revisão. Para o estado revisto, começar pelo
[ponto de situação](PONTO-DE-SITUACAO.md): a conta Nexus foi depois demonstrada
em duas pastas, ODT→PDF foi integrado e o manifesto atual tem 31 ficheiros.
Os números/pendências do quadro abaixo não são nova inspeção do PC em 04-10.

## Inventário confirmado nesta revisão

| Componente | Instalado / presente | Integração e teste |
|---|---|---|
| Python 3.12 / Conductor 0.1.41 / JSON Schema 4.26 | Sim | Núcleo testado; manifesto de 20 ficheiros válido |
| Folha / Host | Sim | HTTP responde; janela antiga pode executar a versão anterior |
| Open Notebook 1.14 / SurrealDB | Sim | UI e health API respondem; circuito cognitivo já passou |
| Tiny Qwen3-4B Q4_K_M / llama.cpp b6500 | Sim | Health responde; ensaios cognitivos anteriores passaram |
| LibreOffice 26.8.0.3 | Sim | Conversões isoladas passaram; integração Nexus pendente |
| Zotero 10.0.3 | Sim | API de ensaio responde; referência real por testar |
| LanguageTool 6.9-SNAPSHOT / Java 21 | Sim | CLI integrada; 94 testes Nexus passaram na última alteração |
| Publisher / Office Professional Plus 2021 | Executável presente | Arranque, licença/ativação e exportação ainda não testados |
| Conta Windows Nexus / ACL | Não concluído | Conta não encontrada; diretório protegido não criado |
| Pinokio | pterm presente | Plano de controlo inacessível; não declarar apps prontas |
| Pesquisa web local | Pasta SearXNG encontrada no Pinokio | Instalação funcional e ligação Nexus não verificadas |
| ACE-Step / gerador de imagens | Não encontrados nas localizações verificadas | Não instalados por esta implementação; escolha/testes pendentes |
| Gmail / Facebook | Serviços externos | Contas não ligadas ao Nexus |

Estar instalado não significa estar configurado, testado ou integrado. Responder a health não prova um workflow. A GPU RTX 2080 tem 8 GB; 4112 MiB estavam ocupados na leitura. Música, imagens e Tiny devem ser ensaiados sequencialmente para medir memória.

## Organização simples no Windows

Manter as localizações existentes nesta fase, pois os lançadores e serviços ainda as referenciam. Organizar primeiro por função, com um ponto de entrada documental; só migrar após teste de arranque e restauro.

```text
Código publicado / nexus/
  ui/                         Folha
  laws/                       regras
  schemas/                    contratos JSON
  processes/                  workflows YAML
  adapters/                   ligações às ferramentas
  tests/                      testes
  docs/                       evidência e planos

Instalações Windows / Program Files/
  LibreOffice, Zotero, Java, Microsoft Office

Laboratório local / work/
  nexus-publicacao/           cópia atual do GitHub
  nexus-venv/                 Python do Host e Conductor
  open-notebook-upstream/     bancada e ambiente próprio
  native/                    executáveis locais e LanguageTool
  models/                    modelos, fora do Git
  notebook-database/          dados da bancada, não Canonical
  *-e2e/, *-tests/            ensaios e diagnósticos

Relatórios para a pessoa / outputs/
  inventário, mapas, resultados dos testes

Dados de cada execução / diretório escolhido pelo Host
  runs/                      input original, estado e diagnóstico
  creative/                  resultados candidatos
  canonical/                 versões aprovadas explicitamente
```

O Host usa `nexus/runtime/` por defeito, mas os ensaios atuais têm diretórios separados. Ainda não existe um cofre final de utilização diária unificado. Credenciais e modelos ficam fora do GitHub. Pastas diferentes, por si, não constituem isolamento de segurança.

## Fases pequenas e critérios de passagem

1. **Base operacional:** consolidar um lançador para a versão atual; impedir instâncias sobre os mesmos dados; concluir conta/ACL e testar tentativa de leitura/escrita proibida. Demonstrar cópia e restauro com hashes antes de chamar algo backup.
2. **LibreOffice:** documento artificial → Conductor → PDF → validar conteúdo/páginas → Creative. Testar ficheiro inválido, ferramenta ausente, timeout e preservação do original. Só depois avançar para documentos reais.
3. **Zotero e pesquisa:** uma referência de ensaio, exportação e proveniência; depois uma pesquisa com fonte permitida. Falha ou zero resultados devem continuar explícitos. Não sincronizar biblioteca real automaticamente.
4. **Publisher:** primeiro abrir documento artificial e exportar PDF local, usando a instalação existente; conservar `.pub` original. A ferramenta é opcional, sem dependência nuclear. Confirmar licença/ativação por uso real. Suporte do Publisher 2021 termina em 13/10/2026, segundo a Microsoft.
5. **Imagens:** comparar uma solução local adequada à RTX 2080; ComfyUI é candidato, não escolha fechada. Começar com uma imagem pequena, medir VRAM/tempo, guardar parâmetros e hash; testar falha por recursos. Sem nodes de terceiros desnecessários.
6. **Música:** ACE-Step é candidato a confirmar, não uma instalação concluída. Começar por 10–20 segundos de áudio, validar duração, formato, reprodução, memória e proveniência. O suporte anunciado a Windows/8 GB não substitui ensaio nesta GPU.
7. **Gmail:** primeiro ficheiro `.eml` local, sem login nem envio; depois autenticação OAuth e criação de um rascunho de ensaio. O scope `gmail.compose` inclui envio, portanto o token não constitui uma fronteira «só rascunhos»: o Host deve bloquear envio sem decisão vinculada ao destinatário, corpo e anexos. Testar token revogado, timeout e evitar reenvio cego após resultado incerto.
8. **Facebook pessoal:** primeiro preparar texto/imagens em Creative para publicação manual. Não reutilizar API de Páginas para perfil pessoal. A documentação Meta de posts respondeu 429 nesta consulta; permissões atuais e alternativa de partilha ainda precisam de confirmação antes de qualquer conector.
9. **Regressão de conjunto:** ligar apenas fases aprovadas; testar interrupção, reinício, limites de recursos, proveniência e bypass. Falha numa ferramenta não pode promover conteúdo nem alterar leis.

Criação em Creative não exige aprovação. Promoção a Canonical e envio/publicação externa são decisões distintas, ligadas ao conteúdo e destino. Gmail e Facebook continuam serviços externos, mesmo que o Host e a criação dos conteúdos sejam locais. Nenhuma conta foi ligada ou mensagem enviada nesta revisão.

## Fontes oficiais consultadas

- Publisher e fim de suporte: https://support.microsoft.com/en-gb/publisher/microsoft-publisher-will-no-longer-be-supported-after-october-2026
- Exportação Publisher: https://learn.microsoft.com/en-us/office/vba/api/publisher.document.exportasfixedformat
- Gmail rascunhos: https://developers.google.com/workspace/gmail/api/guides/drafts
- Gmail permissões: https://developers.google.com/workspace/gmail/api/auth/scopes
- ComfyUI requisitos: https://docs.comfy.org/installation/system_requirements
- ACE-Step upstream: https://github.com/ace-step/ACE-Step

## Limites da revisão

Foram revistos a estrutura atual, versões, executáveis, processos relevantes, respostas HTTP, manifesto e a evidência dos testes. Não se fez auditoria exaustiva do Windows nem nova certificação de todos os componentes. Nenhuma instalação pesada, migração de dados, eliminação ou novo serviço foi efetuado. A suite de 94 testes é a última regressão real; esta alteração é documental.
