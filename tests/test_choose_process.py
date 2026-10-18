# Simple tests for choose_process heuristics
from simple_server import choose_process

cases = {
    'Por favor, verifica este texto e revê o português.': 'proofread',
    'Converte para PDF o documento anexo.': 'convert_pdf',
    'Pesquisa na web fontes sobre fado e devolve referências.': 'web',
    'Importa referências do Zotero para este documento.': 'zotero',
    'Usa ACE-Step para orquestrar o workflow.': 'ace_step',
    'Render com Deforum Forge um storyboard.': 'deforium_forge',
    'Quero produzir um podcast visual com imagens e áudio.': 'visual_podcast',
}

for text, expected in cases.items():
    got = choose_process(text)
    print(f"{text[:40]!r} -> {got}")
    assert got == expected, f"Expected {expected}, got {got} for {text}"

print('choose_process tests passed')
