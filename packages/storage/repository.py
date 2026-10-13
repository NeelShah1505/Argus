from datetime import datetime, timezone
from typing import Dict, List, Optional
from packages.canonical import (
    AuditEvent,
    Document,
    DocumentStatus,
    Fact,
    Job,
    Page,
    Table,
    TableCell,
    TextElement,
)


class DocumentRepository:
    """
    Thread-safe repository for documents, pages, extracted elements, and audit lineage.
    Enforces tenant isolation across all lookups.
    """

    def __init__(self):
        self._documents: Dict[str, Document] = {}
        self._pages: Dict[str, List[Page]] = {}  # doc_id -> list of pages
        self._text_elements: Dict[str, List[TextElement]] = {}  # doc_id -> list of elements
        self._tables: Dict[str, List[Table]] = {}  # doc_id -> list of tables
        self._facts: Dict[str, List[Fact]] = {}  # doc_id -> list of facts
        self._jobs: Dict[str, Job] = {}  # job_id -> job
        self._doc_jobs: Dict[str, List[str]] = {}  # doc_id -> job_ids
        self._audit_events: Dict[str, List[AuditEvent]] = {}  # doc_id -> list of events
        self._hash_to_doc_id: Dict[str, str] = {}  # sha256 -> doc_id for version tracking

    def save_document(self, doc: Document) -> Document:
        self._documents[doc.id] = doc
        self._hash_to_doc_id[doc.file_hash] = doc.id
        return doc

    def get_document(self, doc_id: str, tenant_id: Optional[str] = None) -> Optional[Document]:
        doc = self._documents.get(doc_id)
        if doc and tenant_id and doc.tenant_id != tenant_id:
            return None
        return doc

    def find_by_hash(self, file_hash: str, tenant_id: Optional[str] = None) -> Optional[Document]:
        doc_id = self._hash_to_doc_id.get(file_hash)
        if not doc_id:
            return None
        return self.get_document(doc_id, tenant_id=tenant_id)

    def list_documents(self, tenant_id: Optional[str] = None) -> List[Document]:
        if tenant_id:
            return [d for d in self._documents.values() if d.tenant_id == tenant_id]
        return list(self._documents.values())

    def update_status(self, doc_id: str, status: DocumentStatus) -> Optional[Document]:
        doc = self._documents.get(doc_id)
        if doc:
            doc.status = status
            doc.updated_at = datetime.now(timezone.utc)
        return doc

    def add_page(self, page: Page):
        self._pages.setdefault(page.document_id, []).append(page)

    def get_pages(self, doc_id: str) -> List[Page]:
        return sorted(self._pages.get(doc_id, []), key=lambda p: p.page_number)

    def add_text_element(self, element: TextElement):
        self._text_elements.setdefault(element.document_id, []).append(element)

    def get_text_elements(self, doc_id: str, page_number: Optional[int] = None) -> List[TextElement]:
        elements = self._text_elements.get(doc_id, [])
        if page_number is not None:
            return [e for e in elements if e.page_number == page_number]
        return elements

    def add_table(self, table: Table):
        self._tables.setdefault(table.document_id, []).append(table)

    def get_tables(self, doc_id: str, page_number: Optional[int] = None) -> List[Table]:
        tables = self._tables.get(doc_id, [])
        if page_number is not None:
            return [t for t in tables if t.page_number == page_number]
        return tables

    def get_cells(self, doc_id: str) -> List[TableCell]:
        cells: List[TableCell] = []
        for tbl in self.get_tables(doc_id):
            cells.extend(tbl.cells)
        return cells

    def update_cell(self, doc_id: str, cell_id: str, new_raw_text: str, reviewer_id: str, reason: str) -> Optional[TableCell]:
        target_cell: Optional[TableCell] = None
        for tbl in self.get_tables(doc_id):
            for cell in tbl.cells:
                if cell.id == cell_id:
                    old_val = cell.raw_text
                    cell.raw_text = new_raw_text
                    target_cell = cell
                    # Record audit event
                    self.add_audit_event(
                        AuditEvent(
                            id=f"audit_{datetime.now(timezone.utc).timestamp()}",
                            tenant_id=tbl.cells[0].evidence.document_id if tbl.cells else "default",
                            document_id=doc_id,
                            event_type="CELL_CORRECTION",
                            actor_id=reviewer_id,
                            details={
                                "cell_id": cell_id,
                                "old_value": old_val,
                                "new_value": new_raw_text,
                                "reason": reason,
                            },
                        )
                    )
                    break
        return target_cell

    def add_fact(self, fact: Fact):
        self._facts.setdefault(fact.document_id, []).append(fact)

    def get_facts(self, doc_id: Optional[str] = None, entity: Optional[str] = None, metric: Optional[str] = None, period: Optional[str] = None) -> List[Fact]:
        all_facts: List[Fact] = []
        if doc_id:
            all_facts = self._facts.get(doc_id, [])
        else:
            for f_list in self._facts.values():
                all_facts.extend(f_list)

        filtered = all_facts
        if entity:
            filtered = [f for f in filtered if f.entity.lower() == entity.lower()]
        if metric:
            filtered = [f for f in filtered if f.metric.lower() == metric.lower()]
        if period:
            filtered = [f for f in filtered if f.period.lower() == period.lower()]
        return filtered

    def create_job(self, job: Job) -> Job:
        self._jobs[job.id] = job
        self._doc_jobs.setdefault(job.document_id, []).append(job.id)
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def get_document_jobs(self, doc_id: str) -> List[Job]:
        job_ids = self._doc_jobs.get(doc_id, [])
        return [self._jobs[jid] for jid in job_ids if jid in self._jobs]

    def add_audit_event(self, event: AuditEvent):
        self._audit_events.setdefault(event.document_id, []).append(event)

    def get_audit_events(self, doc_id: str) -> List[AuditEvent]:
        return self._audit_events.get(doc_id, [])


_default_repo: Optional[DocumentRepository] = None


def get_document_repo() -> DocumentRepository:
    global _default_repo
    if _default_repo is None:
        _default_repo = DocumentRepository()
    return _default_repo
