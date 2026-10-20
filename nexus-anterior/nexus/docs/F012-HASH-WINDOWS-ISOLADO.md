> **Estado atual (06-10-2026):** este documento preserva o diagnóstico histórico de PowerShell/Conductor. O hash independente e os gates Windows continuam parte da regressão, mas o executor ativo é Python/MCP e a fronteira nativa foi posteriormente validada.

# F012 — hash Windows no ambiente reduzido do Host

03-10-2026. Correção de execução M14; preserva leis, contratos e autoridade.

## Falha e diagnóstico

A suite no runner Windows passou os testes diretos de Conductor, mas a tarefa
`verify` pela Folha terminava BLOCKED. O diagnóstico do Host registou timeout de
15 segundos em `hash_windows`.

Probes sintéticos confirmaram: a entrada era recebida, a criação do SHA-256 e o
cálculo terminavam; o bloqueio surgia em `ConvertTo-Json` no ambiente reduzido.
O mesmo processo devolveu o hash correto com JSON de campos fixos por .NET.
Os probes localizam a chamada bloqueada; não identificam a sua rotina interna.

A hipótese de cache privada não resolveu a falha e foi retirada. Os probes
temporários permanecem na história Git; foram substituídos por regressões.

## Contrato e alteração

Entrada: caminho UTF-8 por stdin, num processo Windows sem perfis ou credenciais
herdados, usando o ambiente controlado do Host e CREATE_NO_WINDOW.

Saída: JSON com status PASS/FAIL, SHA-256 hexadecimal ou null e capability
`windows.dotnet-sha256`. A exceção concreta de leitura é conservada em stderr;
o JSON de falha contém uma mensagem fixa. O Host conserva os diagnósticos.

`check.yaml` e `verify.yaml` continuam a usar SHA-256 Windows/.NET. O resultado
é escrito por Console.Out: apenas tokens JSON fixos e o digest hexadecimal são
concatenados. Nenhum texto fornecido pela pessoa é interpolado no JSON nem no
código PowerShell. Não há descoberta de cmdlets para serializar estes campos.

Timeouts, ambiente reduzido, comparação independente Python, schemas, Creative
e portão humano mantêm os contratos existentes. A capability devolve evidência;
não recebe autoridade de promoção. Sem nova dependência ou permissão.

## Regressões

`test_windows_hash_environment.py` executa os dois contratos em PowerShell
nativo com o mesmo ambiente do Host e sem consola. Compara com hashlib para
texto, bytes 0–255, ficheiro vazio e nomes com acentos, espaços, apóstrofo, & e $;
ficheiro ausente deve devolver JSON FAIL e diagnóstico. O E2E HTTP existente
verifica Folha → Conductor → hash Windows/Python → Creative → gate → Canonical,
incluindo tentativas de bypass.

```text
python -m pytest nexus/tests/test_windows_hash_environment.py nexus/tests/test_host.py -q -o pythonpath=.
python -m pytest nexus/tests -q -p no:cacheprovider -o pythonpath=.
```

Windows é a plataforma obrigatória destes oito testes de hash. Um SKIP em Unix
não é PASS. O runner não substitui a validação da instalação pessoal de Pedro,
nem verifica as alterações Spiff/Conductor que continuam apenas no seu PC.

## Resultado verificado

Runner Windows/Python 3.12.10, commit `8b8100c7b72c83c07bd4770afb2693750b2b45a4`:
**1154 passed, 28.14 s**, integridade PASS, sem falhas ou skips na suite.
[Execução e logs](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37158002429).
Inclui os oito casos nativos de hash e o E2E HTTP existente. Muitas variantes
são testes de contrato; não correspondem a tarefas completas diferentes.

O ensaio anterior delimitou o bloqueio: BEFORE_JSON apareceu, AFTER_JSON não;
a variante com JSON fixo devolveu PASS no mesmo ambiente reduzido.
[Prova comparativa anterior](https://github.com/PAPACREATOR/cerebro-parvo-/actions/runs/37157671178).

PASS desta correção e dos contratos cobertos. Instalação pessoal, Tiny/Open
Notebook, conta/ACL, Spiff local, restauro completo e produto final continuam
fora desta prova. A arquitetura e as permissões não foram reabertas.
