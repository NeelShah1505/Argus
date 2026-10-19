"""
Structure-Aware Document Chunker.

Creates search chunks that preserve structural context: section headings,
page coordinates, and table headers for footnote associations.
"""

from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

from packages.canonical import BoundingBox, DocumentOutline, Table, TextElement


class DocumentChunk(BaseModel):
    id: str
    document_id: str
    page_number: int
    section_title: str
    text: str
    chunk_type: str  # 'text', 'table_summary', 'footnote'
    bbox: Optional[BoundingBox] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


def chunk_document_elements(
    document_id: str,
    text_elements: List[TextElement],
    tables: List[Table],
    outline: Optional[DocumentOutline] = None,
    max_chunk_chars: int = 800,
) -> List[DocumentChunk]:
    """
    Groups atomic text blocks and tables into cohesive, structure-tagged chunks.
    """
    chunks: List[DocumentChunk] = []

    # Map page number to closest preceding section title in outline
    page_section_map: Dict[int, str] = {}
    if outline and outline.items:
        current_title = outline.items[0].title
        for item in sorted(outline.items, key=lambda it: it.page_number):
            page_section_map[item.page_number] = item.title

    # 1. Chunk Text Elements (grouped by page and section)
    elems_by_page: Dict[int, List[TextElement]] = {}
    for el in text_elements:
        elems_by_page.setdefault(el.page_number, []).append(el)

    for page_num, page_elems in elems_by_page.items():
        section = page_section_map.get(page_num, f"Page {page_num}")
        curr_text_parts: List[str] = []
        curr_chars = 0
        curr_bbox = None

        for el in page_elems:
            curr_text_parts.append(el.text)
            curr_chars += len(el.text)
            curr_bbox = el.bbox if curr_bbox is None else curr_bbox

            if curr_chars >= max_chunk_chars:
                chunk_text = "\n".join(curr_text_parts)
                chunks.append(
                    DocumentChunk(
                        id=f"chk_txt_{uuid.uuid4().hex[:8]}",
                        document_id=document_id,
                        page_number=page_num,
                        section_title=section,
                        text=f"[{section} | Page {page_num}]\n{chunk_text}",
                        chunk_type="text",
                        bbox=curr_bbox,
                    )
                )
                curr_text_parts = []
                curr_chars = 0
                curr_bbox = None

        if curr_text_parts:
            chunk_text = "\n".join(curr_text_parts)
            chunks.append(
                DocumentChunk(
                    id=f"chk_txt_{uuid.uuid4().hex[:8]}",
                    document_id=document_id,
                    page_number=page_num,
                    section_title=section,
                    text=f"[{section} | Page {page_num}]\n{chunk_text}",
                    chunk_type="text",
                    bbox=curr_bbox,
                )
            )

    # 2. Chunk Tables (as structured tabular markdown with title)
    for tbl in tables:
        section = page_section_map.get(tbl.page_number, f"Page {tbl.page_number}")
        # Format table into readable text rows
        rows_dict: Dict[int, List[str]] = {}
        for c in sorted(tbl.cells, key=lambda cell: (cell.row_idx, cell.col_idx)):
            rows_dict.setdefault(c.row_idx, []).append(c.raw_text.strip())

        table_lines = [f"[Table: {tbl.title} | {section} | Page {tbl.page_number}]"]
        for r_idx in sorted(rows_dict.keys()):
            table_lines.append(" | ".join(rows_dict[r_idx]))

        table_text = "\n".join(table_lines)
        chunks.append(
            DocumentChunk(
                id=f"chk_tbl_{uuid.uuid4().hex[:8]}",
                document_id=document_id,
                page_number=tbl.page_number,
                section_title=section,
                text=table_text,
                chunk_type="table_summary",
                bbox=tbl.bbox,
                metadata={"table_id": tbl.id, "rows": tbl.rows_count, "cols": tbl.cols_count},
            )
        )

    return chunks
