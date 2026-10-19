"""
Phase 2 Tests: Independent OCR Channel & Hidden-Text-Layer Detector.
"""

from decimal import Decimal
import io
import pytest
import fitz  # PyMuPDF
from PIL import Image

from packages.canonical import AccuracyTier
from packages.extractors.ocr import extract_scanned_pdf, get_ocr_engine
from packages.extractors.router import route_and_extract
from packages.extractors.text_layer_validator import validate_page_text_layer


def generate_scanned_image_pdf() -> bytes:
    """Creates a synthetic scanned PDF containing ONLY a raster image and zero text layer."""
    img = Image.new("RGB", (600, 800), color=(250, 250, 250))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    doc = fitz.open()
    page = doc.new_page(width=600, height=800)
    page.insert_image(fitz.Rect(0, 0, 600, 800), stream=img_bytes)
    return doc.tobytes()


def generate_corrupt_microfont_pdf() -> bytes:
    """Creates a PDF with a corrupt hidden text layer (font size 0.1 pt)."""
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)
    # Insert micro-font garbage text (simulates corrupt OCR from legacy scans)
    page.insert_text(fitz.Point(50, 50), "hidden corrupt ocr text", fontsize=0.2, color=(1, 1, 1))
    return doc.tobytes()


def generate_clean_digital_pdf() -> bytes:
    """Creates a regular digital PDF with standard font sizes."""
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)
    page.insert_text(fitz.Point(50, 50), "Standard Corporate 10-K Report", fontsize=14, color=(0, 0, 0))
    page.insert_text(fitz.Point(50, 100), "Revenue was 450,000 USD", fontsize=10, color=(0, 0, 0))
    return doc.tobytes()


def test_text_layer_detector_clean_pdf():
    clean_bytes = generate_clean_digital_pdf()
    doc = fitz.open(stream=clean_bytes, filetype="pdf")
    health = validate_page_text_layer(doc[0], page_number=1)

    assert health.is_scanned is False
    assert health.is_corrupt is False
    assert health.should_use_ocr is False
    assert health.character_count > 10


def test_text_layer_detector_scanned_pdf():
    scanned_bytes = generate_scanned_image_pdf()
    doc = fitz.open(stream=scanned_bytes, filetype="pdf")
    health = validate_page_text_layer(doc[0], page_number=1)

    assert health.is_scanned is True
    assert health.should_use_ocr is True
    assert "empty_text_layer_scanned_page" in health.flags


def test_text_layer_detector_corrupt_microfont():
    corrupt_bytes = generate_corrupt_microfont_pdf()
    doc = fitz.open(stream=corrupt_bytes, filetype="pdf")
    health = validate_page_text_layer(doc[0], page_number=1)

    assert health.should_use_ocr is True
    assert health.is_corrupt is True
    assert any("micro_font" in f or "white_on_white" in f for f in health.flags)


def test_route_and_extract_scanned_pdf_e2e():
    """Verify that routing a pure scanned PDF successfully extracts tables via the OCR channel."""
    scanned_bytes = generate_scanned_image_pdf()
    doc_id = "doc_scanned_test"
    pages, text_elements, tables, figures = route_and_extract("scanned_filing.pdf", scanned_bytes, doc_id)

    assert len(pages) >= 1
    assert len(tables) >= 1
    tbl = tables[0]
    assert tbl.tier == AccuracyTier.EXTRACTED
    assert len(tbl.cells) >= 2

    # Check that OCR cell evidence has valid pixel bounding boxes
    first_cell = tbl.cells[0]
    assert first_cell.evidence.page_number == 1
    assert first_cell.evidence.render_image_key == f"renders/{doc_id}/p1.png"
    assert first_cell.evidence.bbox.x1 > first_cell.evidence.bbox.x0
    assert first_cell.extraction.engines_used == ["ocr_channel"]
