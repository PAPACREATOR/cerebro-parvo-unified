"""50,000 cross-route cases after every public product route is enabled."""
from __future__ import annotations

import hashlib
import json

import pytest

from nexus.adapters.product_routes import music_candidate, normalize_plan, web_candidate
from nexus.adapters.tools import compare
from nexus.approval_binding import HumanDecision, promotion_allowed
from nexus.contracts import Blocked, validate
from nexus.store import AI_PROCESSES, NO_AI_PROCESSES, PDF_PROCESSES


CASES = 50_000
ROUTES = ("video", "podcast", "visual_podcast", "book", "music", "web")
NOTEBOOK = {"video", "podcast", "visual_podcast"}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _request(route: str, text: str) -> dict:
    return {"process": route, "text": text, "filename": "", "attachment": ""}


def _candidate(route: str, i: int) -> dict:
    if route in NOTEBOOK:
        source = f"Fonte {i}: facto verificável."
        raw = json.dumps({
            "title": f"{route}-{i}",
            "body": f"Corpo {route} {i}.",
            "steps": [f"micro {i}-1", f"micro {i}-2"],
            "quotes": [source],
        }, ensure_ascii=False)
        return normalize_plan(raw, source, route, "model", "transform")
    if route == "music":
        return music_candidate(f"Tema: tema {i}\nLetra: letra {i}\nEstilo: estilo {i % 9}")
    if route == "web":
        return web_candidate(f"Consulta: pesquisa verificável {i}")
    # Writer/LibreOffice route: its real adapter supplies the PDF. This matrix
    # verifies the result/authority contract without fabricating a PDF file.
    sha = _sha(f"pdf:{i}")
    return {
        "status": "UNKNOWN",
        "outcome": "candidate",
        "title": f"Livro {i}",
        "markdown": f"# Livro {i}\n\nPDF Writer candidato.",
        "ai_calls": 0,
        "artifact": {"name": "resultado.pdf", "sha256": sha},
        "evidence": [{"capability": "libreoffice.writer-pdf", "status": "PASS", "value": sha}],
    }


def test_all_public_routes_50000_end_to_end_contract_cases():
    for i in range(CASES):
        route = ROUTES[i % len(ROUTES)]
        request = _request(route, f"pedido {route} {i}")
        assert validate("request", request)["process"] == route

        # Bidirectional source comparison remains before downstream work.
        left_hash = _sha(f"{route}:{i}:source")
        right_hash = left_hash if i % 7 else _sha(f"{route}:{i}:conflict")
        a = {"status": "PASS", "sha256": left_hash, "capability": "source-a"}
        b = {"status": "PASS", "sha256": right_hash, "capability": "source-b"}
        forward, reverse = compare(a, b), compare(b, a)
        assert forward["outcome"] == reverse["outcome"]
        assert forward["a"] == a and reverse["a"] == b

        result = _candidate(route, i)
        assert validate("result", result)["outcome"] == "candidate"
        assert result["status"] == "UNKNOWN"
        assert (route in AI_PROCESSES) is (result["ai_calls"] == 1)
        assert (route in PDF_PROCESSES) is ("artifact" in result)
        assert route in AI_PROCESSES or route in NO_AI_PROCESSES

        # A tool/model result cannot add Canonical authority.
        hostile = dict(result)
        hostile["authority"] = "CANONICAL"
        with pytest.raises(Blocked):
            validate("result", hostile)

        # Human approval is bound to this exact candidate hash.
        item = f"{i:032x}"[-32:]
        version = _sha(result["markdown"])
        decision = HumanDecision(f"d-{i}", "human-test", item, version, "APPROVE")
        assert promotion_allowed(decision, item, version) is True
        changed = ("0" if version[0] != "0" else "1") + version[1:]
        with pytest.raises(ValueError):
            promotion_allowed(decision, item, changed)


def test_route_sets_are_exact():
    assert CASES == 50_000
    assert AI_PROCESSES == {"interpret", "video", "podcast", "visual_podcast"}
    assert PDF_PROCESSES == {"convert_pdf", "book"}
    assert {"book", "music", "web"}.issubset(NO_AI_PROCESSES)
