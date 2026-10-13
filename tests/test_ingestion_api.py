import io
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from packages.canonical import AccuracyTier, DocumentStatus
from tests.fixtures import (
    generate_test_csv,
    generate_test_docx,
    generate_test_pdf,
    generate_test_xlsx,
)

client = TestClient(app)


def test_upload_pdf_end_to_end():
    pdf_bytes = generate_test_pdf()
    files = {"file": ("acme_annual_2024.pdf", pdf_bytes, "application/pdf")}
    response = client.post("/api/v1/documents?tenant_id=tenant_test", files=files)
    assert response.status_code == 201
    data = response.json()

    assert data["filename"] == "acme_annual_2024.pdf"
    assert data["status"] == DocumentStatus.EXTRACTED.value
    assert data["version"] == 1
    assert data["page_count"] >= 1
    assert data["tables_extracted"] >= 1
    assert data["text_blocks_extracted"] >= 1
    doc_id = data["id"]

    # Verify status endpoint
    status_resp = client.get(f"/api/v1/documents/{doc_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == DocumentStatus.EXTRACTED.value
    assert len(status_data["jobs"]) >= 1

    # Verify page render endpoint
    page_resp = client.get(f"/api/v1/documents/{doc_id}/pages/1")
    assert page_resp.status_code == 200
    page_data = page_resp.json()
    assert "page" in page_data
    assert page_data["page"]["page_number"] == 1

    # Verify page image retrieval
    img_resp = client.get(f"/api/v1/documents/{doc_id}/pages/1/image")
    assert img_resp.status_code == 200
    assert img_resp.headers["content-type"] == "image/png"
    assert len(img_resp.content) > 100

    # Verify elements endpoint
    elements_resp = client.get(f"/api/v1/documents/{doc_id}/elements")
    assert elements_resp.status_code == 200
    elem_data = elements_resp.json()
    assert len(elem_data["tables"]) >= 1
    first_table = elem_data["tables"][0]
    assert len(first_table["cells"]) >= 6
    # Verify evidence coordinates on cells
    first_cell = first_table["cells"][0]
    assert "evidence" in first_cell
    assert first_cell["evidence"]["document_id"] == doc_id
    assert first_cell["evidence"]["bbox"]["unit"] == "normalized_1000"


def test_upload_deduplication_version_bump():
    csv_bytes = generate_test_csv()
    files = {"file": ("revenue_segments.csv", csv_bytes, "text/csv")}

    # First upload
    res1 = client.post("/api/v1/documents?tenant_id=tenant_test", files=files)
    assert res1.status_code == 201
    d1 = res1.json()
    assert d1["version"] == 1
    doc_id = d1["id"]

    # Re-upload identical file -> version bumps to 2, doc_id preserved
    res2 = client.post("/api/v1/documents?tenant_id=tenant_test", files=files)
    assert res2.status_code == 201
    d2 = res2.json()
    assert d2["id"] == doc_id
    assert d2["version"] == 2


def test_upload_docx_and_xlsx():
    # DOCX
    docx_bytes = generate_test_docx()
    files_docx = {"file": ("earnings_summary.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    res_docx = client.post("/api/v1/documents?tenant_id=tenant_test", files=files_docx)
    assert res_docx.status_code == 201
    assert res_docx.json()["tables_extracted"] >= 1

    # XLSX
    xlsx_bytes = generate_test_xlsx()
    files_xlsx = {"file": ("balance_sheet.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    res_xlsx = client.post("/api/v1/documents?tenant_id=tenant_test", files=files_xlsx)
    assert res_xlsx.status_code == 201
    assert res_xlsx.json()["tables_extracted"] >= 1
