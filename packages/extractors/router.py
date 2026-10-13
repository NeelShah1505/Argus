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
        _, text_elements, tables = extract_pdf(file_bytes, doc_id)
        return pages, text_elements, tables, figures

    elif ext == ".docx":
        # Create a synthetic page render representing the document
        synthetic_key = f"renders/{doc_id}/p1.png"
        img = Image.new("RGB", (800, 1000), color=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        store.put_bytes(synthetic_key, buf.getvalue(), content_type="image/png")

        pages = [
            Page(
                id=f"page_{doc_id}_1",
                document_id=doc_id,
                page_number=1,
                render_key=synthetic_key,
                width=800.0,
                height=1000.0,
            )
        ]
        text_elements, tables = extract_docx(file_bytes, doc_id)
        return pages, text_elements, tables, figures

    elif ext in [".xlsx", ".xls"]:
        synthetic_key = f"renders/{doc_id}/p1.png"
        img = Image.new("RGB", (1000, 800), color=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        store.put_bytes(synthetic_key, buf.getvalue(), content_type="image/png")

        pages = [
            Page(
                id=f"page_{doc_id}_1",
                document_id=doc_id,
                page_number=1,
                render_key=synthetic_key,
                width=1000.0,
                height=800.0,
            )
        ]
        text_elements, tables = extract_xlsx(file_bytes, doc_id)
        return pages, text_elements, tables, figures

    elif ext == ".csv":
        synthetic_key = f"renders/{doc_id}/p1.png"
        img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        store.put_bytes(synthetic_key, buf.getvalue(), content_type="image/png")

        pages = [
            Page(
                id=f"page_{doc_id}_1",
                document_id=doc_id,
                page_number=1,
                render_key=synthetic_key,
                width=800.0,
                height=600.0,
            )
        ]
        text_elements, tables = extract_csv(file_bytes, doc_id)
        return pages, text_elements, tables, figures

    else:
        raise ValueError(f"Unsupported file format: {ext}")
