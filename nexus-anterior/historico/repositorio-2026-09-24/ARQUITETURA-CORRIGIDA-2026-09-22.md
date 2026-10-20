# Cérebro Independente — arquitetura corrigida após releitura

Data do registo: 2026-09-22. Autor da conceção e autoridade de decisão: Pedro Alexandre Caldas Coelho. Estado: **decisões expressas do autor + análise documental; implementação não testada**. Este documento substitui as interpretações operacionais que falavam de um único SQLite, sem apagar as fontes e versões históricas.

## O que Pedro fixou agora

1. Há **dois cofres**. O criativo é o grafo/cofre do **Logseq Classic/File Graph**. O final é separado e só recebe uma versão concreta depois da aprovação humana.
2. O cofre criativo usa o que o Logseq já faz nativamente. Não se constrói nele um segundo editor, grafo, gestor de blocos, tarefas ou pesquisa de notas para imitar Logseq.
3. Há **dois SQLite distintos**: um **vive dentro do cofre final** e é parte da memória/lógica determinística do cérebro; o outro é **espelhado**. É falso descrever o SQLite interno como mera cache descartável do Markdown.
4. A pessoa **escreve normalmente e não precisa de saber o que é Markdown**. Não lhe são pedidos inputs, edição de ficheiros ou formatação em Markdown, YAML, SQL ou comandos de programação. O Markdown é um formato interno tratado pela implementação e não exposto no fluxo principal. A experiência pretendida é fluida, sem parede de botões.
5. A IA não é o núcleo. Fica inativa até uma chamada sob pedido ou necessidade concreta permitida pelas regras, com contexto limitado e sem autoridade para promover conhecimento. Activepieces executa fluxos e pesquisa; Zotero trata de fontes. Nenhuma dessas peças substitui a decisão humana.
6. O reaproveitamento de ResearchVault/Will, se aprovado e licenciado, é de **fragmentos pequenos selecionados por função**, cimentados por contratos e testes na base própria de Pedro; não é clonar dois produtos completos nem tornar a arquitetura dependente deles.

## Desenho funcional mínimo

```text
Pessoa escreve normalmente
          │
          ▼
Logseq Classic / cofre criativo
(funções nativas de escrita, blocos, relações e organização)
          │
          ├── manter apenas aqui / apagar por decisão humana
          │
          └── aprovar item + versão concreta
                       │
                       ▼
              Cofre final separado
              ├── Markdown tratado pelo sistema
              └── SQLite interno vivo: memória/estado/relações/regras
                       │
                       └── SQLite espelhado, sob contrato ainda a fechar

Internet → Activepieces/pesquisa → entrada bruta/candidata → cofre criativo
                           └── brainstorming só se o input/pedido o justificar
IA dormente → chamada pontual → proposta, nunca autoridade de escrita final
Fontes/Zotero → referências, sem promoção automática
```

O desenho **não afirma** que a base espelhada seja uma cópia integral, pública ou acessível à IA. Alcance, direção, atualização, permissões, cifragem e recuperação do espelho precisam de um contrato técnico; inventá-los agora adulteraria a decisão do autor. Também não pressupõe que qualquer conteúdo do SQLite interno seja reconstruível a partir do Markdown: a autoridade de cada classe de dados tem de ser especificada antes de testes destrutivos.

## Fluxos e limites

- **Escrita diária:** pessoa → Logseq. O Logseq oferece a superfície de escrita; o sistema faz a representação técnica em Markdown quando necessária. A pessoa não fornece Markdown como input.
- **Promoção:** conteúdo do criativo → pedido de decisão sobre item/versão → aprovação expressa → operação determinística e auditável → cofre final. Sem aprovação, fica no criativo; a pessoa pode mantê-lo só ali ou pedir apagamento. A aprovação não apaga automaticamente o original.
- **Entrada da internet:** resultado recebido → registo/triagem determinística e proveniência → candidato apresentado no fluxo criativo do Logseq. O material pode ser trabalhado, mantido só ali ou descartado pela pessoa. Nem receber, nem classificar, nem pesquisar é aprovação.
- **Brainstorming condicional:** dependendo do input e da intenção da pessoa, pode haver perguntas críticas/expansão ou simplesmente organização e leitura. Não forçar IA nem brainstorming em todas as entradas. Quando a IA é necessária, trabalha apenas com o contexto autorizado para a chamada; o resultado volta como proposta ao criativo.
- **Pesquisa:** tema/interesse autorizado → Activepieces e fontes → material bruto/candidato fora do final → revisão → eventual aprovação. Pesquisa não é um plugin de notas nem entrada automática no conhecimento final.
- **IA efémera:** pedido humano ou necessidade concreta não resolvida pelas regras → contexto mínimo → resultado registado/validado → proposta. Em F4, não recebe poderes de ação.
- **Determinismo:** a transição do núcleo deve depender de estado, eventos observados, regras e configuração versionados. Relógio, rede, modelos e respostas externas são entradas observadas a registar, não provas de que o mundo exterior seja determinístico.
- **Espelhamento:** o SQLite interno e o espelhado são duas bases físicas/lógicas. Uma falha de cópia não pode ser confundida com perda ou autorização de alteração do cofre final. A política de sincronização e o teste de recuperação ainda não estão aprovados.

## Antes e depois — sem reescrever a história

| Etapa | O que aparece nas fontes | Estatuto atual |
| --- | --- | --- |
| Exploração inicial | Dynalist para esboço hierárquico, Obsidian para notas Markdown, n8n e SQLite como peças maduras. | História da aprendizagem; não reinstalar Dynalist/Obsidian no produto por isso. |
| Descoberta do Logseq | Pedro identifica escrita por blocos, fluidez e modo de pensar mais próximo do seu. Já exige escrita normal, sem botões e sem preocupação com Markdown. | Logseq Classic/File Graph é o cofre criativo escolhido. |
| Formulações intermédias | Manuais v3/v7 e Plano Mestre descrevem cofre criativo separado e final `vault.db`/SQLCipher; assistentes sugerem outras camadas e funções. | Preservadas como versões, não como ordens atuais de instalação. |
| Texto Lego e correções expressas | Cofre final em Markdown; Pedro reafirma separação dos cofres e aprovação; depois corrige explicitamente que **há dois SQLite**, um interno no final e outro espelhado. | Esta decisão posterior prevalece. Não reduzir ambos a “índice do Markdown”. |

## Pontos por fechar antes de programar F2

1. Dentro do cofre final, que campos pertencem ao Markdown e quais ao SQLite interno? Quais são canónicos para cada tipo de informação? Não assumir duplicação total.
2. O espelho contém tudo ou apenas campos autorizados? É só leitura? Como se atualiza, verifica e revoga? Estas opções não foram decididas por Pedro neste registo.
3. Como recuperar uma falha entre aprovação, escrita Markdown, transação SQLite interna e atualização do espelho? Definir IDs estáveis, ordem, idempotência e reconciliação.
4. Como proteger e restaurar o cofre final inteiro, incluindo Markdown, base interna e espelho, sem confundir backup com espelhamento?
5. Como provar em teste de utilizador que a escrita normal não exige sintaxe Markdown nem uma interface de botões? Logseq nativo não garante sozinho toda a experiência imaginada; testar antes de prometer.

Não há, nesta data, teste executado de um ciclo completo Logseq → aprovação → cofre final (Markdown + SQLite interno) → SQLite espelhado. Este texto é a especificação conceptual corrigida, não certificação de produto funcional.

## Fontes e limites da releitura

Decisões diretas de Pedro nesta conversa de 2026-09-22; `F02-Conversa-Logseq.txt` (nomeadamente linhas 150–260); `F03-Conversa-Software.txt` (linhas 150–185 e 1858–1895); F01 v3, F05 v7, F12 e anexo Lego mais recente; Constituição/Arquitetura v0.2 e mapa de versões. Foram relidas passagens relevantes e documentos consolidados, **não** todos os 2 431 itens do acervo do disco D: nem a integralidade semântica de todas as conversas longas. As respostas de outros assistentes nas fontes são propostas históricas; as declarações posteriores de Pedro prevalecem.

Referências técnicas externas: [Logseq File Graph e DB Graph](https://github.com/logseq/docs/blob/master/db-version-changes.md), [tutorial oficial de blocos/referências](https://github.com/logseq/docs/blob/master/pages/tutorial.md), [execução durável do Activepieces](https://www.activepieces.com/docs/install/architecture/durable-execution), [backup consistente de SQLite](https://www.sqlite.org/backup.html).
