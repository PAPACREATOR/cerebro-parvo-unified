def choose_process(text: str) -> str:
    t = text.lower()
    # Media / rendering pipelines
    if any(k in t for k in ['visual podcast', 'podcast visual', 'podcast visual', 'podcast-visual']):
        return 'visual_podcast'
    # Zotero / bibliographic
    if any(k in t for k in ['zotero', 'referência', 'referencias', 'bibliografia', 'bibliográfico', 'citation', 'citação']):
        return 'zotero'
    # ACE-Step / Forge keywords
    if any(k in t for k in ['ace-step', 'ace step', 'ace', 'forge', 'aceforge']):
        return 'ace_step'
    # Deforum / rendering Forge
    if any(k in t for k in ['deforum', 'deforium', 'deforum forge', 'deforium forge']):
        return 'deforium_forge'
    if any(k in t for k in ['pdf', 'converter', 'converter para pdf', 'converter para pdf', 'pdf']):
        return 'convert_pdf'
    if any(k in t for k in ['rever', 'revê', 'revisar', 'revisão', 'proofread']):
        return 'proofread'
    if any(k in t for k in ['pesquisa', 'pesquisar', 'web', 'procura']):
        return 'web'
    # default: interpret/preparation
    return 'interpret'
