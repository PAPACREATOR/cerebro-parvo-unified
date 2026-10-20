# Implementação ativa — 28-09-2026

Esta pasta é a linha de trabalho posterior ao candidato histórico de 27/09.

O código base de importação foi copiado sem alterar o candidato preservado. A primeira extensão própria é `cerebro/persistence.py`: writer recuperável comum a Creative/Canonical.

Protocolo implementado no componente:

`PREPARED (SQLite) -> ficheiro temporário + fsync -> os.replace -> hash verificado -> COMMITTED`.

Cobertura adicionada:

- escrita Creative;
- mesma mecânica Canonical;
- idempotência;
- operação reutilizada com payload diferente;
- alvo existente divergente;
- crash após PREPARED + resume;
- crash após replace + reconcile;
- COMMITTED com ficheiro desaparecido;
- PREPARED com conteúdo divergente;
- bloqueio de path traversal.

Limite: este writer ainda não está ligado ao `materialize()` do pipeline histórico nem ao Activepieces. É o substrato de G10/IMP-019, não o fecho integral do IMP.
