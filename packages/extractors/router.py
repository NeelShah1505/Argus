import io
import mimetypes
from pathlib import Path
from typing import List, Tuple
import fitz  # PyMuPDF
from PIL import Image

from packages.canonical import (
    BoundingBox,
    Figure,
    Page,
    Table,
    TextElement,
)
from packages.storage.object_store import get_object_store
from .native import (
    extract_csv,
    extract_docx,
    extract_pdf,
    extract_xlsx,
)
from .ocr import extract_scanned_pdf
from .render_office import render_office_document
from .text_layer_validator import validate_page_text_layer
from .vector_chart import extract_vector_charts


def render_pdf_pages_to_storage(doc_id: str, file_bytes: bytes) -> List[Page]:
    """
    Renders each PDF page to PNG at 150 DPI and stores in object storage.
    Returns canonical Page objects.
    """
    store = get_object_store()
    pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages: List[Page] = []

    for page_num, page in enumerate(pdf_doc, start=1):
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        render_key = f"renders/{doc_id}/p{page_num}.png"
        store.put_bytes(render_key, img_bytes, content_type="image/png")

        pages.append(
            Page(
                id=f"page_{doc_id}_{page_num}",
                document_id=doc_id,
                page_number=page_num,
                render_key=render_key,
                width=float(page.rect.width),
                height=float(page.rect.height),
            )
        )
    return pages


def route_and_extract(
    filename: str, file_bytes: bytes, doc_id: str
) -> Tuple[List[Page], List[TextElement], List[Table], List[Figure]]:
    """
    Inspects document type and routes to optimal extraction path.
    Renders visual pages and coordinates into canonical models.
    """
    ext = Path(filename).suffix.lower()
    store = get_object_store()
    figures: List[Figure] = []

    if ext == ".pdf":
        pages = render_pdf_pages_to_storage(doc_id, file_bytes)
        
        # Phase 2: Check text layer health
        pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
        needs_ocr = False
        for p_idx, page in enumerate(pdf_doc, start=1):
            health = validate_page_text_layer(page, page_number=p_idx)
            if health.should_use_ocr:
                needs_ocr = True
                break

        if needs_ocr:
            text_elements, tables = extract_scanned_pdf(file_bytes, doc_id)
        else:
            _, text_elements, tables = extract_pdf(file_bytes, doc_id)
            # Phase 3: Extract digital vector charts
            for p_idx, page in enumerate(pdf_doc, start=1):
                chart_results = extract_vector_charts(page, page_number=p_idx, doc_id=doc_id)
                for fig, _ in chart_results:
                    figures.append(fig)
            
        return pages, text_elements, tables, figures

    elif ext == ".docx":
        pages = render_office_document(file_bytes, ext, doc_id)
        text_elements, tables = extract_docx(file_bytes, doc_id)
        return pages, text_elements, tables, figures

    elif ext in [".xlsx", ".xls"]:
        pages = render_office_document(file_bytes, ext, doc_id)
        text_elements, tables = extract_xlsx(file_bytes, doc_id)
        return pages, text_elements, tables, figures

    elif ext == ".csv":
        pages = render_office_document(file_bytes, ext, doc_id)
        text_elements, tables = extract_csv(file_bytes, doc_id)
        return pages, text_elements, tables, figures

    else:
        raise ValueError(f"Unsupported file format: {ext}")
