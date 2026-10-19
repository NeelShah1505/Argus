"""
Phase 7 Tests: Document Structure, Table of Contents (TOC) & Reading Order Reconstruction.
"""

import io
from fastapi.testclient import TestClient
import fitz  # PyMuPDF
import pytest

from apps.api.main import app
from packages.canonical import BoundingBox, TextElement
from packages.extractors.structure import (
    extract_document_outline,
    sort_reading_order,
)

client = TestClient(app)


def generate_pdf_with_bookmarks() -> bytes:
    doc = fitz.open()
    p1 = doc.new_page(width=600, height=800)
    p1.insert_text(fitz.Point(50, 100), "Overview", fontsize=14)
    p2 = doc.new_page(width=600, height=800)
    p2.insert_text(fitz.Point(50, 100), "Financial Results", fontsize=14)

    # Set bookmarks: [lvl, title, page_number]
    toc = [
        [1, "1. Executive Summary", 1],
        [1, "2. Financial Results", 2],
        [2, "2.1 Income Statement", 2],
    ]
    doc.set_toc(toc)
    return doc.tobytes()


def generate_sec_10k_style_pdf() -> bytes:
    doc = fitz.open()
    p1 = doc.new_page(width=600, height=800)
    p1.insert_text(fitz.Point(50, 80), "ITEM 1. BUSINESS", fontsize=13)
    p1.insert_text(fitz.Point(50, 200), "ITEM 1A. RISK FACTORS", fontsize=13)
    p2 = doc.new_page(width=600, height=800)
    p2.insert_text(fitz.Point(50, 80), "ITEM 8. CONSOLIDATED FINANCIAL STATEMENTS", fontsize=13)
    return doc.tobytes()


def test_outline_extraction_from_embedded_bookmarks():
    pdf_bytes = generate_pdf_with_bookmarks()
    outline = extract_document_outline(pdf_bytes, "doc_bkmk_test")

    assert outline.document_id == "doc_bkmk_test"
    assert len(outline.items) == 3
    assert outline.items[0].title == "1. Executive Summary"
    assert outline.items[0].page_number == 1
    assert outline.items[1].title == "2. Financial Results"
    assert outline.items[2].level == 2


def test_outline_extraction_from_item_patterns():
    pdf_bytes = generate_sec_10k_style_pdf()
    outline = extract_document_outline(pdf_bytes, "doc_item_test")

    assert len(outline.items) >= 3
    titles = [it.title for it in outline.items]
    assert any("ITEM 1. BUSINESS" in t for t in titles)
    assert any("ITEM 1A. RISK FACTORS" in t for t in titles)
    assert any("ITEM 8. CONSOLIDATED FINANCIAL STATEMENTS" in t for t in titles)


def test_sort_reading_order_two_column():
    t_left_top = TextElement(
        id="t1", document_id="d1", page_number=1, text="Left Top",
        bbox=BoundingBox(page_number=1, x0=50, y0=50, x1=250, y1=80),
    )
    t_left_bot = TextElement(
        id="t2", document_id="d1", page_number=1, text="Left Bottom",
        bbox=BoundingBox(page_number=1, x0=50, y0=300, x1=250, y1=330),
    )
    t_right_top = TextElement(
        id="t3", document_id="d1", page_number=1, text="Right Top",
        bbox=BoundingBox(page_number=1, x0=550, y0=50, x1=750, y1=80),
    )

    # Shuffled input
    ordered = sort_reading_order([t_right_top, t_left_bot, t_left_top])
    assert [e.id for e in ordered] == ["t1", "t2", "t3"]


def test_get_document_toc_api():
    pdf_bytes = generate_pdf_with_bookmarks()
    files = {"file": ("filing_with_toc.pdf", pdf_bytes, "application/pdf")}
    res_up = client.post("/api/v1/documents?tenant_id=tenant_toc", files=files)
    assert res_up.status_code == 201
    doc_id = res_up.json()["id"]

    res_toc = client.get(f"/api/v1/documents/{doc_id}/toc")
    assert res_toc.status_code == 200
    data = res_toc.json()
    assert "items" in data
    assert len(data["items"]) >= 2
    assert "Executive Summary" in data["items"][0]["title"]
