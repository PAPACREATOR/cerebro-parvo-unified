# Matriz de compatibilidade — runtime candidato atual

“Compatível” significa que a ferramenta pode satisfazer a capability. “PASS” exige integração/teste específico.

| Capability | Implementação atual/preferida | Integração | Estado |
|---|---|---|---|
| Interface principal | Folha Nexus | HTTP/local | candidato funcional |
| Kernel/autoridade | Host/Store Python | interno | testado |
| Transporte de tools | MCP Nexus-owned | stdio | testado |
| Creative/Canonical | Store + Human Gate | interno | testado |
| Proveniência inversa | Store/Host/Folha | interno | testado |
| Confinamento de processos lançados | Windows native boundary/LPAC/Job | nativo | testado em CI Windows |
| Cognição | OpenNotebook | HTTP delimitado pelo Host | boundary/E2E controlado; físico completo pendente |
| Revisão linguística | LanguageTool CLI | adapter/MCP | integrado; PC físico a reconfirmar |
| Writer → PDF | LibreOffice Writer headless | adapter/MCP | integrado e limitado |
| Writer editorial completo | LibreOffice Writer/UNO ou formato ODF controlado | adapter futuro | NÃO IMPLEMENTADO |
| Referências | Zotero Desktop | Local API | pendente |
| Música | ACE-Step 1.5 | localhost/API externa | health contract; provisioning físico pendente |
| Imagem | Forge | localhost/API externa | health contract; checkpoint/licença pendentes |
| Vídeo/avatar | FFmpeg + Wav2Lip | worker externo | contratos testados; GPU/modelo físico pendente |
| STT/TTS | provider local substituível | adapter futuro | pendente |
| Web | capability explícita | adapter/provider | não núcleo |
| Pesquisa exata | Kernel/Store/FTS quando aplicável | interno | parcial por família |
| Pesquisa semântica | capability opcional | provider substituível | não autoridade |
| Relações | Kernel/proveniência | interno | parcial |

## Fronteiras obrigatórias

1. humano é autoridade final;
2. ferramenta/IA não promove Canonical;
3. output externo é UNTRUSTED/candidate;
4. Creative preserva alternativas/contradições;
5. Human Gate controla promoção;
6. replay não reinvoca IA/Web para fabricar passado;
7. trocar provider não altera leis;
8. ausência/timeout/UNKNOWN nunca contam como PASS.

## Genealogia

Activepieces, Memory Provider, Pinokio/ComfyUI, Spiff e Conductor foram estudados como alternativas/etapas. Consultar `DECISIONS.md` e `historico/`; não são requisitos do candidato atual.
