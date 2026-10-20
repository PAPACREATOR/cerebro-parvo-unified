"""Real LibreOffice Writer gate for one immutable .ott test fixture.

The fixture is binary, versioned and hash-bound. This test never creates or edits
styles. LibreOffice instantiates the fixed template, round-trips the document and
exports PDF. The production editorial template remains a separate human-approved
asset; this fixture only proves the mechanism.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("NEXUS_REAL_WRITER") != "1",
    reason="explicit real LibreOffice Writer gate",
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "writer-fixed-test.ott"
FIXED_SHA256 = "379df147e4b7019c197f572bc07491404782ecd0abfc615886cd1c9350399d3f"


def _soffice() -> str:
    requested = os.environ.get("LIBREOFFICE_EXE")
    if requested:
        path = Path(requested)
        if path.is_file():
            return str(path)
        raise AssertionError(f"LIBREOFFICE_EXE missing: {path}")
    found = shutil.which("soffice") or shutil.which("soffice.com") or shutil.which("soffice.exe")
    if not found:
        raise AssertionError("LibreOffice soffice executable not found")
    return found


def _run(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [_soffice(), "--headless", "--norestore", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    return result


def _member(path: Path, name: str) -> bytes:
    with zipfile.ZipFile(path) as archive:
        return archive.read(name)


def test_fixed_writer_template_is_exact_binary_and_contains_expected_contract():
    raw = FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FIXED_SHA256
    assert _member(FIXTURE, "mimetype") == b"application/vnd.oasis.opendocument.text-template"
    styles = _member(FIXTURE, "styles.xml").decode("utf-8")
    content = _member(FIXTURE, "content.xml").decode("utf-8")
    assert 'style:name="NexusBody"' in styles
    assert 'style:name="NexusChapterTitle"' in styles
    assert 'style:page-usage="mirrored"' in styles
    assert 'fo:orphans="2"' in styles
    assert 'fo:widows="2"' in styles
    assert 'fo:keep-with-next="always"' in styles
    assert 'fo:page-width="14.8cm"' in styles
    assert 'fo:page-height="21cm"' in styles
    assert 'fo:margin-left="2.5cm"' in styles
    assert 'fo:margin-right="1.7cm"' in styles
    assert "NEXUS_FIXED_TEMPLATE_TITLE" in content
    assert "NEXUS_FIXED_TEMPLATE_BODY_064" in content


def test_writer_real_instantiates_fixed_template_roundtrips_and_exports_pdf(tmp_path):
    original = FIXTURE.read_bytes()
    local_template = tmp_path / FIXTURE.name
    local_template.write_bytes(original)

    instantiated = tmp_path / "instantiated"
    instantiated.mkdir()
    _run("--convert-to", "odt", "--outdir", str(instantiated), str(local_template), cwd=tmp_path)
    odt = instantiated / "writer-fixed-test.odt"
    assert odt.is_file() and odt.stat().st_size > 1000

    styles = _member(odt, "styles.xml").decode("utf-8")
    content = _member(odt, "content.xml").decode("utf-8")
    for token in (
        'style:page-usage="mirrored"',
        'fo:orphans="2"',
        'fo:widows="2"',
        'fo:keep-with-next="always"',
    ):
        assert token in styles
    assert "NEXUS_FIXED_TEMPLATE_TITLE" in content
    assert "NEXUS_FIXED_TEMPLATE_BODY_064" in content

    flat_dir = tmp_path / "flat"
    flat_dir.mkdir()
    _run("--convert-to", "fodt", "--outdir", str(flat_dir), str(odt), cwd=tmp_path)
    fodt = flat_dir / "writer-fixed-test.fodt"
    assert fodt.is_file() and fodt.stat().st_size > 1000
    flat = fodt.read_text(encoding="utf-8")
    assert "NEXUS_FIXED_TEMPLATE_TITLE" in flat
    assert 'style:page-usage="mirrored"' in flat
    assert 'fo:keep-with-next="always"' in flat
    assert 'fo:orphans="2"' in flat
    assert 'fo:widows="2"' in flat

    roundtrip_dir = tmp_path / "roundtrip"
    roundtrip_dir.mkdir()
    _run("--convert-to", "odt", "--outdir", str(roundtrip_dir), str(fodt), cwd=tmp_path)
    odt2 = roundtrip_dir / "writer-fixed-test.odt"
    assert odt2.is_file()
    roundtrip_styles = _member(odt2, "styles.xml").decode("utf-8")
    roundtrip_content = _member(odt2, "content.xml").decode("utf-8")
    assert "NEXUS_FIXED_TEMPLATE_TITLE" in roundtrip_content
    assert "NEXUS_FIXED_TEMPLATE_BODY_064" in roundtrip_content
    assert "keep-with-next" in roundtrip_styles
    assert "orphans" in roundtrip_styles and "widows" in roundtrip_styles
    assert 'page-usage="mirrored"' in roundtrip_styles

    pdf_dir = tmp_path / "pdf"
    pdf_dir.mkdir()
    _run("--convert-to", "pdf:writer_pdf_Export", "--outdir", str(pdf_dir), str(odt2), cwd=tmp_path)
    pdf = pdf_dir / "writer-fixed-test.pdf"
    raw_pdf = pdf.read_bytes()
    assert len(raw_pdf) > 5_000
    assert raw_pdf.startswith(b"%PDF-")
    assert b"%%EOF" in raw_pdf[-2048:]

    assert local_template.read_bytes() == original
    assert FIXTURE.read_bytes() == original


def test_writer_real_fixed_template_source_never_changes_on_direct_export(tmp_path):
    original = FIXTURE.read_bytes()
    local_template = tmp_path / FIXTURE.name
    local_template.write_bytes(original)
    out = tmp_path / "out"
    out.mkdir()
    _run("--convert-to", "pdf:writer_pdf_Export", "--outdir", str(out), str(local_template), cwd=tmp_path)
    assert local_template.read_bytes() == original
    assert FIXTURE.read_bytes() == original


def _copy_template_with_exact_slots(source: Path, destination: Path, title: str, body: str) -> None:
    """Test-only proof: replace only two existing literal slots; never edit styles."""
    from xml.sax.saxutils import escape

    with zipfile.ZipFile(source, "r") as src, zipfile.ZipFile(destination, "w") as dst:
        for info in src.infolist():
            raw = src.read(info.filename)
            if info.filename == "content.xml":
                text = raw.decode("utf-8")
                assert text.count("NEXUS_FIXED_TEMPLATE_TITLE") == 1
                assert text.count("NEXUS_FIXED_TEMPLATE_BODY_064") == 1
                text = text.replace("NEXUS_FIXED_TEMPLATE_TITLE", escape(title))
                text = text.replace("NEXUS_FIXED_TEMPLATE_BODY_064", escape(body))
                raw = text.encode("utf-8")
            dst.writestr(info, raw)


def test_writer_real_fills_existing_slots_without_touching_styles(tmp_path):
    title = "Capítulo — ação e memória"
    body = "Texto português: informação, proveniência e revisão humana."

    filled_template = tmp_path / "filled.ott"
    _copy_template_with_exact_slots(FIXTURE, filled_template, title, body)

    # The mechanism may fill content slots, but it must not redesign the template.
    assert _member(filled_template, "styles.xml") == _member(FIXTURE, "styles.xml")
    filled_content = _member(filled_template, "content.xml").decode("utf-8")
    assert title in filled_content
    assert body in filled_content
    assert "NEXUS_FIXED_TEMPLATE_TITLE" not in filled_content
    assert "NEXUS_FIXED_TEMPLATE_BODY_064" not in filled_content

    odt_dir = tmp_path / "odt"
    odt_dir.mkdir()
    _run("--convert-to", "odt", "--outdir", str(odt_dir), str(filled_template), cwd=tmp_path)
    odt = odt_dir / "filled.odt"
    assert odt.is_file()

    roundtrip_content = _member(odt, "content.xml").decode("utf-8")
    roundtrip_styles = _member(odt, "styles.xml")
    assert title in roundtrip_content
    assert body in roundtrip_content
    for token in (
        b'style:page-usage="mirrored"',
        b'fo:orphans="2"',
        b'fo:widows="2"',
        b'fo:keep-with-next="always"',
    ):
        assert token in roundtrip_styles

    pdf_dir = tmp_path / "pdf-filled"
    pdf_dir.mkdir()
    _run("--convert-to", "pdf:writer_pdf_Export", "--outdir", str(pdf_dir), str(odt), cwd=tmp_path)
    pdf = pdf_dir / "filled.pdf"
    raw_pdf = pdf.read_bytes()
    assert len(raw_pdf) > 5_000
    assert raw_pdf.startswith(b"%PDF-")
    assert b"%%EOF" in raw_pdf[-2048:]

    # The source template remains immutable throughout the real LibreOffice run.
    assert hashlib.sha256(FIXTURE.read_bytes()).hexdigest() == FIXED_SHA256
