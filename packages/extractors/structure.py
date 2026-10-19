"""
Document Structure & Table of Contents (TOC) Extraction Engine.

Extracts embedded bookmarks and synthesizes font-size/pattern section hierarchies
for enterprise document navigation and reading-order reconstruction.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
import uuid
import fitz  # PyMuPDF

from packages.canonical import BoundingBox, DocumentOutline, Table, TextElement, TOCItem


# Standard 10-K and financial report section heading patterns
ITEM_SECTION_PATTERN = re.compile(
    r"^(?:ITEM|PART|SECTION)\s+([0-9]+[A-Z]?|[IVXLCDM]+)[\.\:\s\-]+([A-Za-z0-9\s,\'\"\(\)]+)",
    re.IGNORECASE,
)


def extract_document_outline(file_bytes: bytes, doc_id: str) -> DocumentOutline:
    """
    Extracts document outline. Prefers embedded PDF bookmarks (get_toc).
    If missing, falls back to font-size hierarchy and Item/Section pattern detection.
    """
    try:
        pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception:
        # Non-PDF or unparseable: return single root section
        return DocumentOutline(
            document_id=doc_id,
            items=[
                TOCItem(
                    level=1,
                    title="Document Root",
                    page_number=1,
                    section_id=f"sec_{doc_id}_root",
                )
            ],
        )

    items: List[TOCItem] = []

    # 1. Primary: Embedded PDF Bookmarks / Outline
    raw_toc = pdf_doc.get_toc()  # returns list of [lvl, title, page, ...]
    if raw_toc:
        for idx, entry in enumerate(raw_toc):
            lvl = int(entry[0])
            title = str(entry[1]).strip()
            page = int(entry[2]) if len(entry) > 2 else 1
            if title:
                items.append(
                    TOCItem(
                        level=min(max(1, lvl), 3),
                        title=title,
                        page_number=max(1, page),
                        section_id=f"sec_{doc_id}_bkmk_{idx + 1}",
                    )
                )

    # 2. Fallback: Synthesize outline via font size and Item patterns
    if not items:
        for page_num, page in enumerate(pdf_doc, start=1):
            text_page = page.get_text("dict")
            blocks = text_page.get("blocks", [])

            for b in blocks:
                if "lines" not in b:
                    continue
                for line in b["lines"]:
                    line_spans = line.get("spans", [])
                    if not line_spans:
                        continue

                    line_text = " ".join(s.get("text", "") for s in line_spans).strip()
                    if not line_text or len(line_text) < 4 or len(line_text) > 120:
                        continue

                    max_font_size = max(s.get("size", 10.0) for s in line_spans)
                    bbox_tuple = line.get("bbox", (0, 0, 0, 0))
                    bbox = BoundingBox(
                        page_number=page_num,
                        x0=float(bbox_tuple[0]),
                        y0=float(bbox_tuple[1]),
                        x1=float(bbox_tuple[2]),
                        y1=float(bbox_tuple[3]),
                    )

                    # Pattern 1: SEC 10-K "ITEM 1. BUSINESS", "ITEM 7. MD&A", "ITEM 8. FINANCIAL STATEMENTS"
                    item_match = ITEM_SECTION_PATTERN.match(line_text)
                    if item_match:
                        items.append(
                            TOCItem(
                                level=1,
                                title=line_text,
                                page_number=page_num,
                                section_id=f"sec_{doc_id}_item_{len(items) + 1}",
                                bbox=bbox,
                            )
                        )
                    # Pattern 2: Large Title Header (font >= 15 pt)
                    elif max_font_size >= 15.0 and len(line_text) < 80:
                        items.append(
                            TOCItem(
                                level=1,
                                title=line_text,
                                page_number=page_num,
                                section_id=f"sec_{doc_id}_h1_{len(items) + 1}",
                                bbox=bbox,
                            )
                        )
                    # Pattern 3: Sub-section Header (font in [13.0, 15.0) and uppercase/bold)
                    elif max_font_size >= 13.0 and len(line_text) < 70 and line_text.isupper():
                        items.append(
                            TOCItem(
                                level=2,
                                title=line_text,
                                page_number=page_num,
                                section_id=f"sec_{doc_id}_h2_{len(items) + 1}",
                                bbox=bbox,
                            )
                        )

    # If still empty, supply default page index
    if not items:
        for p in range(1, len(pdf_doc) + 1):
            items.append(
                TOCItem(
                    level=1,
                    title=f"Page {p}",
                    page_number=p,
                    section_id=f"sec_{doc_id}_p{p}",
                )
            )

    return DocumentOutline(document_id=doc_id, items=items)


def sort_reading_order(
    elements: List[Any],
) -> List[Any]:
    """
    Sorts a mixed list of TextElements and Tables into natural reading order:
    1. By page_number ascending.
    2. Within page, by two-column horizontal band first, then y0 top-to-bottom.
    """
    def element_sort_key(elem: Any) -> Tuple[int, int, float]:
        page = getattr(elem, "page_number", 1)
        bbox = getattr(elem, "bbox", None)
        if not bbox:
            return (page, 0, 0.0)
        # Column bucket: 0 if left half of page (< 500), 1 if right half
        col_bucket = 1 if bbox.x0 > 500 else 0
        return (page, col_bucket, bbox.y0)

    return sorted(elements, key=element_sort_key)
