"""Intent selection (choose_process) with simple keyword heuristics and confidence scoring.

This module is intentionally small and rule-based so it's easy to test and predictable.
"""

KEYWORD_MAP = {
    'visual_podcast': ['podcast', 'podcast visual', 'podcast visual', 'guiao', 'guião', 'video curto', 'vídeo curto', 'podcast'],
    'convert_pdf': ['convert to pdf', 'converte para pdf', 'converter para pdf', 'pdf', 'export pdf', 'gera pdf', 'gerar pdf', 'converte pdf'],
    'proofread': ['revise', 'revisa', 'revisar', 'proofread', 'corrige', 'correção', 'correcao', 'revisão', 'revisao'],
    'zotero': ['zotero', 'referências', 'referencias', 'bibliografia', 'referencias sobre'],
    'ace_step': ['ace-step', 'ace step', 'ace_step', 'workflow ace'],
    'deforium_forge': ['deforum', 'stable diffusion', 'sd', 'deforium', 'forge'],
}

DEFAULT_CONFIDENCE = 0.6


def choose_process(text: str):
    """Return a tuple (process, confidence).

    Very small rule-based scorer:
      - if multiple keywords match, pick the one with most matches
      - confidence is proportional to matches / (len(text_words)+1)
    """
    if not text or not text.strip():
        return {'process': 'interpret', 'confidence': 0.0}

    t = text.lower()
    words = t.split()
    scores = {}
    for proc, kws in KEYWORD_MAP.items():
        score = 0
        for kw in kws:
            if kw in t:
                score += 1
        if score > 0:
            scores[proc] = score

    if not scores:
        # no clear match
        return {'process': 'interpret', 'confidence': 0.0}

    # choose highest score
    best = max(scores.items(), key=lambda x: x[1])
    proc, matches = best
    # confidence heuristic: matches / (number of unique keywords scanned + 1)
    denom = sum(len(k) for k in KEYWORD_MAP.keys())
    confidence = min(0.99, max(DEFAULT_CONFIDENCE, matches / (len(words) + 1)))
    return {'process': proc, 'confidence': confidence}
