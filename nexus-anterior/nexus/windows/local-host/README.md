# Fontes do Host local Windows

Este pacote preserva oito scripts que já funcionam em `C:\Nexus`, sem substituir
Kernel/Host/Store nem reintroduzir Conductor. Base do candidato:
`e3833856ed8ebc8947c4229344bab3be3f54654a`. A origem local, caminho de destino e
SHA-256 de cada ficheiro estão em `local-host-manifest.json`; os scripts são
cópias exatas das fontes revistas em 11-10-2026.
`.gitattributes` conserva os bytes destas fontes mesmo com `core.autocrlf=true`.

Inclui a entrada única `abrir-nexus.py`/`Abrir Nexus.cmd`, arranque de IA local,
OpenNotebook/Surreal WSL, pontes Piper/Forge e entrada Zotero. Não inclui
ambientes, modelos, perfis, configurações privadas, credenciais ou dados.

## Instalação sobre o PC existente

Executar primeiro a validação sem escrita:

```powershell
.\install-local-host.ps1 -ValidateOnly
```

A aplicação explícita usa `-AuthorizeInstall`; `-WhatIf` mostra o plano sem o
executar. O destino é exclusivamente `C:\Nexus`, porque os scripts preservados
usam esse caminho. O instalador valida o manifesto, hashes e caminhos sem
redirecionamentos. Ficheiros iguais não são escritos novamente. Para alterações,
faz backup de todos os originais e verifica os seus hashes antes da primeira
substituição; o relatório indica o caminho do backup. Cópia verificada não equivale
a restauro demonstrado. Uma falha durante a aplicação pode deixar parte dos
scripts atualizada; o backup e o manifesto permitem revisão/recuperação explícita.

O instalador não cria/altera ambientes, configuração, modelos, dados, políticas
Windows, atalhos de arranque ou serviços; não lança ferramentas. O atalho de
arranque já existente pode continuar a apontar para `C:\Nexus\abrir-nexus.py`.
Confirmar as pré-condições e o funcionamento depois da aplicação é um gate separado.

Pré-condições preservadas: Python Host em `ambientes/host`, registos/dados e
configuração existentes, ferramentas/modelos nos caminhos já configurados, WSL
`Nexus` com Piper e Surreal e configuração privada `configuracao/notebook.json`.
Os seus conteúdos não devem entrar no Git. A migração Surreal preservada só é
ativada ao arrancar o respetivo serviço e mantém o original; não é executada
pelo instalador deste pacote.

## Compatibilidade e limites

As pontes contêm marcadores públicos de encaminhamento local, anteriormente
testados pelos clientes. Estes valores não são segredos nem autenticação forte
da identidade Windows. Foram conservados para evitar uma migração silenciosa;
nenhuma chave privada foi copiada. Loopback, limites de pedido, allowlists e
controle de concorrência são preservados; não lhes atribuir proteção contra um
administrador ou processo com acesso aos mesmos ficheiros.

O estado READY guardado ou um HTTP200 não demonstra geração real. O supervisor
llama valida também os aliases; OpenNotebook ainda precisa de uniformização da
saúde/identidade. Os serviços nativos continuam ferramentas externas sem poder
de aprovar Canonical ou alterar políticas do Windows.

## Adaptação MoneyPrinterTurbo

`moneyprinterturbo/ace-step-local.patch` contém apenas o provider ACE novo e os
pequenos registos em `task.py`, `cli.py` e `webui/Main.py`. Base upstream fixada:
`68eb5a68b93cfe338198b3dfb151f6d5ec2fe4e5`; licença upstream incluída.
`base.json` identifica os quatro caminhos e hashes observados.

O patch não é aplicado pelo instalador dos scripts. Num checkout compatível,
conferir primeiro a revisão e `git apply --check` antes da aplicação. No PC já
adaptado, `git apply --reverse --check` verifica a presença das mesmas alterações
sem modificar código. Não guardar o `Main.py` inteiro, `config.toml`, backups,
áudio gerado ou ambientes neste pacote.

Não executar o configurador antigo de MoneyPrinterTurbo sobre a configuração
atual sem uma reconciliação: ele recria `config.toml` a partir do exemplo e pode
perder as ligações Piper/Forge/ACE. A preservação/configuração idempotente dessas
ligações, `TTS_BATCH_SIZE=1` do OpenNotebook e os testes reais são gates separados.

As alterações de segurança Windows requerem uma capacidade própria autorizada
pelo Host/Kernel e verificada depois da ação. Este pacote não a implementa.

## Evidência desta embalagem

Compilação sem execução dos seis scripts Python e oito verificações de validação
sem escrita passaram em PowerShell7 e Windows PowerShell5. Incluem ausência de
autorização, destino diferente, travessia de caminho e hash adulterado recusados.
A opção de Bypass foi usada somente no processo PowerShell5 de validação de
código revisto, sem alterar política persistente. A primeira invocação sem essa
opção foi recusada pelo AuthorizationManager; diagnóstico preservado. A pesquisa
de módulos herdada do PowerShell7 foi retirada apenas do processo filho PS5.
O patch ACE passou `git apply --reverse --check` no checkout instalado. Sintaxe e
hashes não substituem instalação, restauro ou testes funcionais, não executados
por este pacote. Os hashes dos ficheiros no índice Git devem ser conferidos depois
de o revisor os adicionar; nada foi adicionado ao índice nesta etapa.
