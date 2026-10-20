# Revisão para publicação — 01-10-2026

## Contrato

INPUT: implementação Nexus local, decisão humana para publicar código desta versão e manter PolyForm Noncommercial 1.0.0.
OUTPUT: pasta Nexus autónoma com instruções, contratos, código e testes; sem modelos, credenciais, cofres ou instalações pessoais.
LEIS: mesma autoridade humana, Creative automático, Canonical só com decisão explícita; nenhuma mudança de Constituição.

## Revisão e regressão

A cópia limpa do GitHub não continha `src/cerebro_independente/approval_binding.py`: cinco erros de recolha demonstraram que o Nexus dependia da versão antiga. O módulo próprio foi reutilizado em `nexus/approval_binding.py`, sem alterar o comportamento. O Host passou a importar o módulo local. Ficheiros do manifesto têm finais de linha LF fixados para sobreviver ao checkout Windows.

Comando: `python -m pytest nexus/tests -q -p no:cacheprovider -o pythonpath=.`
Resultado local Windows: **83 passed, 20.75 s, exit 0**. Inclui Conductor/PowerShell reais e falhas controladas. Não prova todos os componentes do laboratório.

## Estado por componente

| Componente | Evidência | Limite / próxima ação |
|---|---|---|
| Folha / Host / contratos | Implementados; testes HTTP e gate | Rever usabilidade completa |
| Microsoft Conductor 0.1.41 | YAML executa ferramenta Windows | Motor Python/CLI, sem aplicação gráfica |
| Redundância | Windows SHA-256 + Python; acordo/conflito/unknown/falha | Não é consenso semântico |
| Creative / Canonical | Gate, hash, rejeição de bypass e recuperação testados | Sem isolamento Windows por conta/ACL |
| Open Notebook / Tiny | Ensaio real anterior: 10.07 s, resultado UNKNOWN em Creative | Texto UTF-8; instalação externa não incluída |
| LibreOffice | Cinco conversões sintéticas ODT→PDF anteriores | Ainda não ligado à Folha |
| Zotero | API de biblioteca de ensaio respondeu | Importação/exportação real por validar |
| LanguageTool | Java e ferramenta instalados | Servidor falhou; CLI sem correções, por diagnosticar |
| Pesquisa web | Planeada | Sem circuito Host validado |
| Wiki / espelho / backup | Parcialmente desenhados | Identidade e restauro por demonstrar |
| Conta Windows Nexus | Script preparado | Criação e permissões ainda não concluídas |
| Desenho / música | Pedido aprovado para fase posterior | Só avançar após testes dos componentes anteriores |

## Consumo e execução local

Preferência humana: self-hosted e o mais leve possível. O circuito determinístico não necessita de GPU, Notebook ou modelo. A bancada cognitiva é opcional. Não iniciar imagem/música simultaneamente com Tiny sem medir recursos. Não acrescentar um serviço quando uma CLI existente cumpre o contrato.

## Segurança e alcance

A proteção atual é da aplicação. O mesmo utilizador Windows ainda pode alterar os ficheiros; tokens de sessão e hash não substituem ACL nem isolamento. A suite não constitui certificação de segurança. O original, as divergências e UNKNOWN são preservados. Nenhum conhecimento real foi promovido nesta publicação.

Os relatórios anteriores nesta pasta são evidência datada; não somar contagens de testes nem interpretar instalações como integrações. Mantém-se pendente a regressão E2E de todo o laboratório.
