# Revisão do núcleo — 01-10-2026

## Alcance

Leitura de Host, armazenamento, aprovação, contratos, servidor HTTP, interface, quatro workflows e adaptadores; revisão da evidência e novos testes adversariais. Não equivale a auditoria formal nem a prova de ausência de falhas.

## Falhas reproduzidas e corrigidas

Seis testes novos falharam antes das correções (6 failed, 0.53 s): overflow numérico JSON positivo/negativo; manifesto vazio aceite; input alterado aceite com proveniência antiga; resultado cognitivo PASS aceite pelo Host; erro de limpeza mantendo o bloqueio de execução adquirido.

Correções mínimas: rejeitar floats não finitos; exigir inventário completo do manifesto e incluir UI; verificar hash do original antes de receber o resultado; impor UNKNOWN/candidate nos processos interpret/proofread/convert_pdf e uma chamada cognitiva em interpret; libertar o bloqueio mesmo quando a limpeza falha, sinalizando BLOCKED. Resultado PDF volta a passar pelo schema depois de acrescentar o hash.

Regressão: **115 passed, 21.47 s, exit 0**. Nenhuma nova dependência.

## O que continua por resolver

- **Alta prioridade: isolamento Windows.** FAIL reproduzido com leitura/escrita sintética pela mesma identidade. Script nativo preparado em windows/setup-isolation.ps1; não atribuir PASS antes de executar como Nexus e conferir o relatório. Também será necessário ligar esta identidade ao Host e à bancada.
- **Instâncias simultâneas:** bloqueio atual é por objeto Host; duas instâncias sobre os mesmos dados não estão impedidas. O arranque da segunda pode marcar como interrompida uma execução da primeira. Usar uma só instância por diretório até implementar bloqueio de ficheiro nativo e testá-lo.
- **Estado parcialmente escrito/corrompido:** JSON inválido em state.json pode impedir arranque/listagem. Recuperação de Canonical tem testes, mas não há ainda quarentena geral de estados danificados.
- **Processos e recursos:** um crash abrupto do Host pode deixar descendentes vivos; timeout não equivale a Job Object com kill-on-close. Saída capturada do Conductor e ligações HTTP locais ainda não têm todos os limites de recursos demonstrados.
- **Cofres e credenciais:** Hash/manifesto não são raiz de confiança contra o mesmo utilizador. Credencial temporária pode sobreviver a crash do Host; exige limpeza segura/reconciliação na próxima etapa de isolamento.
- **Interpretação:** input textual junto de anexo é conservado, mas a ferramenta recebe apenas os bytes do anexo. Contexto/instrução devem ter contrato explícito; não alegar intenção arbitrária executada. Modelo/transformation são configuração externa administrável.
- **PDF:** deteção de formato é básica; filtro de pacote não garante ausência de todo conteúdo ativo. DOCX e interface visual completa ainda por testar. Usar documentos de ensaio confiáveis até isolamento.
- **Proveniência:** processo, input e output rastreáveis, mas versões/hashes de todas as ferramentas externas e configuração cognitiva ainda não estão integralmente fixados por execução.
- **Backup/wiki:** restauro completo, identidade relacional e espelho permanecem pendentes.

## YAML e Windows

interpret.yaml existe no Git e circuito atual passou novamente em 10.57 s, com UNKNOWN em Creative, Canonical vazio e credencial temporária removida. A falha de isolamento foi reproduzida fora do YAML. YAML controla a sequência; ACL/identidade Windows devem restringir direitos. Testar ambos separadamente e depois o conjunto.

O núcleo é um protótipo útil, com correções verificáveis. Não está certificado, completamente isolado ou pronto para executar documentos hostis.
