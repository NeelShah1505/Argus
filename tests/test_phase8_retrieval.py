"""
Phase 8 Tests: Structure-Aware Document Chunking & Hybrid Semantic Retrieval (BM25 + Dense RRF).
"""

import pytest

from packages.canonical import (
    AccuracyTier,
    BoundingBox,
    DocumentOutline,
    EvidenceCoordinates,
    Table,
    TableCell,
    TextElement,
    TOCItem,
)
from packages.retrieval import (
    DocumentChunk,
    HybridRetrievalEngine,
    chunk_document_elements,
    get_retrieval_engine,
)


def test_structure_aware_chunking():
    outline = DocumentOutline(
        document_id="doc_ret_1",
        items=[
            TOCItem(level=1, title="Item 1. Business", page_number=1, section_id="s1"),
            TOCItem(level=1, title="Item 8. Financials", page_number=2, section_id="s2"),
        ],
    )

    t1 = TextElement(
        id="t1", document_id="doc_ret_1", page_number=1, text="Company operates in consumer electronics.",
        bbox=BoundingBox(page_number=1, x0=10, y0=20, x1=200, y1=50),
    )
    t2 = TextElement(
        id="t2", document_id="doc_ret_1", page_number=2, text="Operating cash flow was 110,000 USD.",
        bbox=BoundingBox(page_number=2, x0=10, y0=20, x1=200, y1=50),
    )

    ev = EvidenceCoordinates(
        document_id="doc_ret_1",
        page_number=2,
        bbox=BoundingBox(page_number=2, x0=10, y0=50, x1=100, y1=70),
        raw_text="cell",
        render_image_key="doc_ret_1_p2.png",
    )

    c1 = TableCell(
        id="c1", table_id="tbl_1", row_idx=0, col_idx=0, is_header=True, raw_text="Segment",
        tier=AccuracyTier.VERIFIED, evidence=ev,
    )
    c2 = TableCell(
        id="c2", table_id="tbl_1", row_idx=0, col_idx=1, is_header=True, raw_text="Revenue",
        tier=AccuracyTier.VERIFIED, evidence=ev,
    )
    c3 = TableCell(
        id="c3", table_id="tbl_1", row_idx=1, col_idx=0, is_header=False, raw_text="Americas",
        tier=AccuracyTier.VERIFIED, evidence=ev,
    )
    c4 = TableCell(
        id="c4", table_id="tbl_1", row_idx=1, col_idx=1, is_header=False, raw_text="150,000",
        tier=AccuracyTier.VERIFIED, evidence=ev,
    )

    tbl = Table(
        id="tbl_1",
        document_id="doc_ret_1",
        page_number=2,
        title="Revenue by Geography",
        rows_count=2,
        cols_count=2,
        cells=[c1, c2, c3, c4],
        bbox=BoundingBox(page_number=2, x0=10, y0=50, x1=500, y1=200),
    )

    chunks = chunk_document_elements("doc_ret_1", [t1, t2], [tbl], outline=outline)

    assert len(chunks) == 3
    # First chunk has section title Item 1
    assert "Item 1. Business" in chunks[0].section_title
    assert "consumer electronics" in chunks[0].text

    # Table chunk has table summary
    table_chunk = next(ch for ch in chunks if ch.chunk_type == "table_summary")
    assert "Revenue by Geography" in table_chunk.text
    assert "Americas | 150,000" in table_chunk.text


def test_hybrid_search_bm25_and_rrf():
    engine = HybridRetrievalEngine()

    c1 = DocumentChunk(
        id="c1", document_id="doc_aapl", page_number=1, section_title="Overview",
        text="Apple designs Mac, iPhone, iPad and wearables in Cupertino.",
        chunk_type="text",
    )
    c2 = DocumentChunk(
        id="c2", document_id="doc_aapl", page_number=42, section_title="Note 7 - Debt",
        text="Note 7: Term debt consists of floating rate notes due 2026 totaling 95,000 million USD.",
        chunk_type="footnote",
    )
    c3 = DocumentChunk(
        id="c3", document_id="doc_msft", page_number=10, section_title="Cloud",
        text="Microsoft Cloud and Azure revenue grew thirty percent.",
        chunk_type="text",
    )

    engine.add_chunks([c1, c2, c3])

    # 1. Exact term search ("Note 7") should strongly rank c2 first via BM25
    results = engine.search("Note 7 Term debt", top_k=2)
    assert len(results) >= 1
    top_chunk, score = results[0]
    assert top_chunk.id == "c2"
    assert "Note 7" in top_chunk.text

    # 2. Document isolation filtering
    results_filtered = engine.search("revenue", top_k=5, document_id="doc_msft")
    assert len(results_filtered) == 1
    assert results_filtered[0][0].id == "c3"
