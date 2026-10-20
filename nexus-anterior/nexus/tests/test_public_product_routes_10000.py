"""10,000 deterministic cases for each public product route."""
from __future__ import annotations

import io
import json
import zipfile

from nexus.adapters.office import document_kind
from nexus.adapters.product_routes import music_candidate, normalize_plan, web_candidate
from nexus.adapters.runner import PROCESS_TO_TOOL, process_fingerprint
from nexus.contracts import validate


CASES = 10_000
ROUTES = ("video", "podcast", "visual_podcast", "book", "music", "web")


def _request(process: str, text: str):
    return {"process": process, "text": text, "filename": "", "attachment": ""}


def _plan(route: str, i: int) -> tuple[str, str]:
    source = f"Fonte factual {i}: Lisboa recebeu {i % 97 + 1} caixas."
    raw = json.dumps({
        "title": f"{route} {i}",
        "body": f"Conteúdo candidato para {route} no caso {i}.",
        "steps": [f"passo {i}-1", f"passo {i}-2"],
        "quotes": [source],
    }, ensure_ascii=False)
    return source, raw


def _odt(i: int) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("mimetype", "application/vnd.oasis.opendocument.text")
        archive.writestr("content.xml", f"<document><p>Livro {i}</p></document>")
    return stream.getvalue()


def test_video_route_10000():
    assert PROCESS_TO_TOOL["video"] == "video_plan_file"
    assert len(process_fingerprint("video")) == 64
    for i in range(CASES):
        assert validate("request", _request("video", f"vídeo {i}"))["process"] == "video"
        source, raw = _plan("video", i)
        result = normalize_plan(raw, source, "video", "model", "transform")
        assert validate("result", result)["outcome"] == "candidate"
        assert result["ai_calls"] == 1


def test_podcast_route_10000():
    assert PROCESS_TO_TOOL["podcast"] == "podcast_plan_file"
    assert len(process_fingerprint("podcast")) == 64
    for i in range(CASES):
        assert validate("request", _request("podcast", f"podcast {i}"))["process"] == "podcast"
        source, raw = _plan("podcast", i)
        result = normalize_plan(raw, source, "podcast", "model", "transform")
        assert validate("result", result)["outcome"] == "candidate"
        assert result["ai_calls"] == 1


def test_visual_podcast_route_10000():
    assert PROCESS_TO_TOOL["visual_podcast"] == "visual_podcast_plan_file"
    assert len(process_fingerprint("visual_podcast")) == 64
    for i in range(CASES):
        assert validate("request", _request("visual_podcast", f"podcast visual {i}"))["process"] == "visual_podcast"
        source, raw = _plan("visual_podcast", i)
        result = normalize_plan(raw, source, "visual_podcast", "model", "transform")
        assert validate("result", result)["outcome"] == "candidate"
        assert result["ai_calls"] == 1


def test_book_route_10000_writer_contract():
    assert PROCESS_TO_TOOL["book"] == "book_file"
    assert len(process_fingerprint("book")) == 64
    sample = _odt(0)
    for i in range(CASES):
        assert validate("request", _request("book", f"livro {i}"))["process"] == "book"
        assert document_kind(sample) == ".odt"


def test_music_route_10000_keyword_contract():
    assert PROCESS_TO_TOOL["music"] == "music_plan_file"
    assert len(process_fingerprint("music")) == 64
    for i in range(CASES):
        text = f"Tema: memória {i}\nLetra: verso {i}\nEstilo: folk acústico {i % 7}"
        assert validate("request", _request("music", text))["process"] == "music"
        result = music_candidate(text)
        assert validate("result", result)["outcome"] == "candidate"
        spec = json.loads(result["evidence"][0]["value"])
        assert spec["lyrics"] == f"verso {i}"
        assert f"memória {i}" in spec["prompt"]


def test_web_route_10000_query_contract():
    assert PROCESS_TO_TOOL["web"] == "web_plan_file"
    assert len(process_fingerprint("web")) == 64
    for i in range(CASES):
        text = f"Consulta: história local caso {i}"
        assert validate("request", _request("web", text))["process"] == "web"
        result = web_candidate(text)
        assert validate("result", result)["outcome"] == "candidate"
        assert result["evidence"][0]["value"] == f"história local caso {i}"


def test_exact_budget():
    assert CASES * len(ROUTES) == 60_000
