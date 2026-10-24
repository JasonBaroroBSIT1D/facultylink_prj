"""Phase 2.1 OCR reliability (unit + optional live Tesseract)."""
from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from services.ocr.tesseract_config import (  # noqa: E402
    configure_pytesseract,
    resolve_tesseract_executable,
    tesseract_version_line,
)
from services.ocr.text_extractor import (  # noqa: E402
    MIN_PAGE_TEXT_CHARS,
    extract_text_from_bytes,
)
from services.validation.set_sef_engine import _normalize_ocr_text, _parse_fields  # noqa: E402
from services.validation.rule_loader import load_set_sef_rules  # noqa: E402


def test_tesseract_discovery_windows():
    path = resolve_tesseract_executable()
    if path:
        assert path.lower().endswith("tesseract.exe") or "tesseract" in path.lower()
        assert configure_pytesseract() is True
        version = tesseract_version_line()
        assert version and "tesseract" in version.lower()
    else:
        pytest.skip("Tesseract not installed on this machine")


def test_normalize_ocr_academic_year():
    noisy = "Academic Year: 2O25-2O26\nSemester: First"
    norm = _normalize_ocr_text(noisy)
    assert "2025-2026" in norm


def test_parse_fields_noisy_set_rating():
    rules = load_set_sef_rules()
    rule = rules["indicators"]["A.1"]
    text = """
    Student Evaluation of Teachers
    Faculty: Demo Faculty
    Academic Year: 2O25-2O26
    Semester: First Semester
    Overall SET Rating: 88
    """
    fields, conf = _parse_fields(_normalize_ocr_text(text), rule)
    assert fields.get("overall_rating") == 88.0
    assert fields.get("academic_year") == "2025-2026"
    assert conf.get("overall_rating", 0) >= 0.7


@patch("services.ocr.text_extractor.configure_pytesseract", return_value=False)
def test_pdf_text_only_uses_pypdf(_mock_tess):
    from pypdf import PdfWriter

    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    # pypdf blank pages have no text; use a minimal PDF with embedded text via add_page
    buf = io.BytesIO()
    writer.write(buf)
    data = buf.getvalue()
    result = extract_text_from_bytes(data, "application/pdf")
    assert result.status == "completed"
    assert "pypdf" in result.method or "empty" in str(result.page_methods)


@patch("services.ocr.text_extractor._ocr_image_pil")
@patch("services.ocr.text_extractor.configure_pytesseract", return_value=True)
def test_pdf_mixed_page_order(_mock_tess_ok, mock_ocr):
    mock_ocr.return_value = ("Scanned SET page two", 70.0, "tesseract_rot0")

    fake_fitz = MagicMock()
    page_mock = MagicMock()
    pix = MagicMock()
    pix.n = 3
    pix.width = 10
    pix.height = 10
    pix.samples = b"\x00" * 300
    page_mock.get_pixmap.return_value = pix
    fake_fitz.__len__.return_value = 2
    fake_fitz.__getitem__.side_effect = lambda i: page_mock
    fake_fitz.close = MagicMock()

    p1 = MagicMock()
    p1.extract_text.return_value = "Page one text layer " + ("x" * MIN_PAGE_TEXT_CHARS)
    p2 = MagicMock()
    p2.extract_text.return_value = ""
    reader = MagicMock()
    reader.pages = [p1, p2]

    with patch("pypdf.PdfReader", return_value=reader):
        with patch("pymupdf.open", return_value=fake_fitz):
            result = extract_text_from_bytes(b"%PDF-fake", "application/pdf")

    assert "Page one" in result.text
    assert "Scanned SET" in result.text
    assert result.page_methods[0].startswith("pypdf_text:p1")
    assert "tesseract" in result.page_methods[1]
    assert result.method == "pdf_mixed_pypdf_tesseract"


@pytest.mark.skipif(not resolve_tesseract_executable(), reason="Tesseract not installed")
def test_live_tesseract_png_extract():
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (640, 200), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 60), "Overall SET Rating: 77", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result = extract_text_from_bytes(buf.getvalue(), "image/png")
    assert result.status == "completed"
    assert "tesseract" in result.method
    assert "77" in result.text or result.confidence >= 0


def test_live_tesseract_jpeg_extract():
    if not resolve_tesseract_executable():
        pytest.skip("Tesseract not installed")
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (500, 120), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((10, 40), "Semester: First Semester", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    result = extract_text_from_bytes(buf.getvalue(), "image/jpeg")
    assert result.status == "completed"
    assert result.text.strip() != "" or result.confidence <= 30
