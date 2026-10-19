import hashlib
import uuid
from typing import List, Optional
from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from decimal import Decimal
from packages.canonical import (
    AccuracyTier,
    Document,
    DocumentOutline,
    DocumentStatus,
    Fact,
    Job,
    Page,
    Table,
    TableCell,
    TextElement,
)
from packages.extractors import route_and_extract
from packages.extractors.structure import extract_document_outline
from packages.normalize import canonicalize_financial_number
from packages.calc.reconciliation import ReconciliationReport, run_full_reconciliation
from packages.retrieval import chunk_document_elements, get_retrieval_engine
from packages.storage.object_store import get_object_store
from packages.storage.repository import get_document_repo

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


class DocumentUploadResponse(BaseModel):
    id: str
    tenant_id: str
    filename: str
    file_hash: str
    status: DocumentStatus
    version: int
    page_count: int
    tables_extracted: int
    text_blocks_extracted: int


class DocumentStatusResponse(BaseModel):
    id: str
    status: DocumentStatus
    version: int
    jobs: List[dict]


@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = "tenant_default",
):
    """
    Ingest and extract a financial document.
    Enforces SHA-256 deduplication and immutable versioning.
    """
    repo = get_document_repo()
    store = get_object_store()

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    file_hash = hashlib.sha256(file_bytes).hexdigest()
    filename = file.filename or "uploaded_document"

    existing_doc = repo.find_by_hash(file_hash, tenant_id=tenant_id)
    if existing_doc:
        doc_id = existing_doc.id
        version = existing_doc.version + 1
        existing_doc.version = version
        doc = existing_doc
    else:
        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        version = 1
        doc = Document(
            id=doc_id,
            tenant_id=tenant_id,
            filename=filename,
            file_hash=file_hash,
            mime_type=file.content_type or "application/octet-stream",
            status=DocumentStatus.UPLOADED,
            version=version,
        )
        repo.save_document(doc)

    # Store original file bytes
    orig_key = f"originals/{doc_id}_{filename}"
    store.put_bytes(orig_key, file_bytes, content_type=doc.mime_type)

    # Record job
    job = Job(
        id=f"job_{uuid.uuid4().hex[:8]}",
        tenant_id=tenant_id,
        document_id=doc_id,
        stage="EXTRACT",
        status="RUNNING",
    )
    repo.create_job(job)

    try:
        pages, text_elements, tables, figures = route_and_extract(filename, file_bytes, doc_id)

        for p in pages:
            repo.add_page(p)
        for t_elem in text_elements:
            repo.add_text_element(t_elem)

        entity_guess = filename.rsplit(".", 1)[0].replace("_", " ").title()

        for tbl in tables:
            repo.add_table(tbl)
            col_headers = {}
            row_labels = {}
            for c in tbl.cells:
                if c.is_header or c.row_idx == 0:
                    col_headers[c.col_idx] = c.raw_text.strip()
                if c.col_idx == 0:
                    row_labels[c.row_idx] = c.raw_text.strip()

            for c in tbl.cells:
                if c.is_header or c.row_idx == 0 or c.col_idx == 0:
                    continue
                norm = canonicalize_financial_number(c.raw_text)
                if norm.normalized_value is not None and not norm.is_null:
                    metric_label = row_labels.get(c.row_idx, f"Row {c.row_idx}")
                    period_label = col_headers.get(c.col_idx, "FY2024")
                    fact_id = f"fact_{doc_id}_{c.id}"
                    fact = Fact(
                        id=fact_id,
                        tenant_id=tenant_id,
                        document_id=doc_id,
                        element_id=c.id,
                        entity=entity_guess,
                        metric=metric_label,
                        period=period_label,
                        value=norm.normalized_value,
                        raw_text=c.raw_text,
                        currency=norm.currency or "USD",
                        scale=norm.scale or Decimal("1.0"),
                        tier=c.tier,
                        confidence=1.0,
                        evidence=c.evidence,
                    )
                    repo.add_fact(fact)

        # Structure-aware chunking and hybrid retrieval indexing
        outline = None
        if filename.lower().endswith(".pdf"):
            try:
                outline = extract_document_outline(file_bytes, doc_id)
            except Exception:
                outline = None
        chunks = chunk_document_elements(doc_id, text_elements, tables, outline=outline)
        get_retrieval_engine().index_chunks(chunks)

        doc.page_count = len(pages)
        doc.status = DocumentStatus.EXTRACTED
        repo.update_status(doc_id, DocumentStatus.EXTRACTED)

        job.status = "COMPLETED"

        return DocumentUploadResponse(
            id=doc.id,
            tenant_id=doc.tenant_id,
            filename=doc.filename,
            file_hash=doc.file_hash,
            status=doc.status,
            version=doc.version,
            page_count=len(pages),
            tables_extracted=len(tables),
            text_blocks_extracted=len(text_elements),
        )
    except Exception as e:
        job.status = "FAILED"
        job.error = str(e)
        repo.update_status(doc_id, DocumentStatus.FAILED)
        raise HTTPException(status_code=500, detail=f"Extraction failure: {str(e)}")


@router.get("", response_model=List[Document])
async def list_documents(tenant_id: Optional[str] = None):
    repo = get_document_repo()
    return repo.list_documents(tenant_id=tenant_id)


@router.get("/{doc_id}", response_model=Document)
async def get_document(doc_id: str, tenant_id: Optional[str] = None):
    repo = get_document_repo()
    doc = repo.get_document(doc_id, tenant_id=tenant_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    return doc


@router.get("/{doc_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(doc_id: str):
    repo = get_document_repo()
    doc = repo.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    jobs = repo.get_document_jobs(doc_id)
    return DocumentStatusResponse(
        id=doc.id,
        status=doc.status,
        version=doc.version,
        jobs=[j.model_dump() for j in jobs],
    )


@router.get("/{doc_id}/pages/{page_num}")
async def get_page_details(doc_id: str, page_num: int):
    repo = get_document_repo()
    pages = [p for p in repo.get_pages(doc_id) if p.page_number == page_num]
    if not pages:
        raise HTTPException(status_code=404, detail=f"Page {page_num} not found.")
    text_elements = repo.get_text_elements(doc_id, page_number=page_num)
    tables = repo.get_tables(doc_id, page_number=page_num)
    return {
        "page": pages[0],
        "text_elements": text_elements,
        "tables": tables,
    }


@router.get("/{doc_id}/pages/{page_num}/image")
async def get_page_image(doc_id: str, page_num: int):
    repo = get_document_repo()
    store = get_object_store()
    pages = [p for p in repo.get_pages(doc_id) if p.page_number == page_num]
    if not pages:
        raise HTTPException(status_code=404, detail=f"Page {page_num} not found.")

    image_bytes = store.get_bytes(pages[0].render_key)
    if not image_bytes:
        raise HTTPException(status_code=404, detail="Page render image not found in storage.")

    return Response(content=image_bytes, media_type="image/png")


@router.get("/{doc_id}/elements")
async def get_document_elements(doc_id: str, tier: Optional[AccuracyTier] = None):
    repo = get_document_repo()
    tables = repo.get_tables(doc_id)
    text_elements = repo.get_text_elements(doc_id)

    if tier:
        filtered_tables: List[Table] = []
        for t in tables:
            matching_cells = [c for c in t.cells if c.tier == tier]
            if matching_cells:
                t_copy = t.model_copy()
                t_copy.cells = matching_cells
                filtered_tables.append(t_copy)
        tables = filtered_tables

    return {
        "document_id": doc_id,
        "tables": tables,
        "text_elements": text_elements,
    }


class CellCorrectionRequest(BaseModel):
    document_id: str
    new_raw_text: str
    reviewer_id: str
    reason: str


@router.patch("/elements/{cell_id}")
async def correct_cell(cell_id: str, payload: CellCorrectionRequest):
    """
    Submit a human reviewer correction.
    Bumps document version, updates cell, assigns Tier V, and logs an append-only audit event.
    """
    from packages.normalize import canonicalize_financial_number

    repo = get_document_repo()
    doc = repo.get_document(payload.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    updated_cell = repo.update_cell(
        doc_id=payload.document_id,
        cell_id=cell_id,
        new_raw_text=payload.new_raw_text,
        reviewer_id=payload.reviewer_id,
        reason=payload.reason,
    )
    if not updated_cell:
        raise HTTPException(status_code=404, detail=f"Cell {cell_id} not found.")

    # Canonicalize and approve to Verified
    norm = canonicalize_financial_number(payload.new_raw_text)
    updated_cell.normalized_value = norm.normalized_value
    updated_cell.currency = norm.currency
    updated_cell.scale = norm.scale
    updated_cell.tier = AccuracyTier.VERIFIED

    # Bump document version
    doc.version += 1

    return {
        "status": "corrected",
        "cell": updated_cell,
        "new_version": doc.version,
    }


@router.get("/{doc_id}/validation")
async def get_document_validation(doc_id: str):
    repo = get_document_repo()
    doc = repo.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    tables = repo.get_tables(doc_id)
    all_validations = []
    for tbl in tables:
        for c in tbl.cells:
            all_validations.extend(c.validations)

    audit_events = repo.get_audit_events(doc_id)

    return {
        "document_id": doc_id,
        "validations_count": len(all_validations),
        "validations": all_validations,
        "audit_events": audit_events,
    }


@router.get("/{doc_id}/toc", response_model=DocumentOutline)
async def get_document_toc(doc_id: str):
    repo = get_document_repo()
    doc = repo.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    store = get_object_store()
    orig_key = f"originals/{doc_id}_{doc.filename}"
    file_bytes = store.get_bytes(orig_key)
    if not file_bytes:
        # Fallback: synthesize single root page
        return DocumentOutline(
            document_id=doc_id,
            items=[{"level": 1, "title": doc.filename, "page_number": 1, "section_id": f"sec_{doc_id}_root"}],
        )

    return extract_document_outline(file_bytes, doc_id)


@router.get("/{doc_id}/reconciliation", response_model=ReconciliationReport)
async def get_document_reconciliation(doc_id: str):
    repo = get_document_repo()
    doc = repo.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc_facts = repo.get_facts(doc_id=doc_id)
    if doc_facts:
        entity = doc_facts[0].entity
        facts = repo.get_facts(entity=entity)
    else:
        facts = doc_facts

    return run_full_reconciliation(facts, tenant_id=doc.tenant_id)
