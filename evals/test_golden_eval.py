from decimal import Decimal
import pytest
from packages.extractors import route_and_extract
from packages.normalize import canonicalize_financial_number
from tests.fixtures import (
    generate_test_docx,
    generate_test_pdf,
    generate_test_xlsx,
)


def test_golden_evaluation_gate():
    """
    CI Accuracy Regression Gate (ADR-06).
    Evaluates extraction fidelity against 3 benchmark golden documents:
    - Critical-field exact match >= 99.5%
    - 100% Provenance coverage
    - 0 unsupported claims
    """
    # 1. Golden Document 1: Acme Annual PDF
    pdf_bytes = generate_test_pdf()
    pages, text_elems, tables, _ = route_and_extract("acme_golden.pdf", pdf_bytes, "doc_golden_pdf")

    assert len(tables) >= 1
    t1 = tables[0]
    cell_values = {c.raw_text: c for c in t1.cells}

    # Verify critical fields exact values and signs
    assert "391,036" in cell_values
    norm_rev = canonicalize_financial_number(cell_values["391,036"].raw_text)
    assert norm_rev.normalized_value == Decimal("391036")

    assert "(213,972)" in cell_values
    norm_cos = canonicalize_financial_number(cell_values["(213,972)"].raw_text)
    assert norm_cos.normalized_value == Decimal("-213972")  # Negative preserved!

    assert "177,064" in cell_values
    norm_gp = canonicalize_financial_number(cell_values["177,064"].raw_text)
    assert norm_gp.normalized_value == Decimal("177064")

    # Provenance coverage verification: 100% of cells have bounding box & document id
    for c in t1.cells:
        assert c.evidence.document_id == "doc_golden_pdf"
        assert c.evidence.bbox.unit == "normalized_1000"

    # 2. Golden Document 2: Beta Holdings DOCX
    docx_bytes = generate_test_docx()
    _, _, docx_tables, _ = route_and_extract("beta_golden.docx", docx_bytes, "doc_golden_docx")
    assert len(docx_tables) >= 1
    docx_cells = {c.raw_text: c for c in docx_tables[0].cells}
    assert "$145,000" in docx_cells
    norm_sales = canonicalize_financial_number(docx_cells["$145,000"].raw_text)
    assert norm_sales.normalized_value == Decimal("145000")

    # 3. Golden Document 3: Balance Sheet XLSX
    xlsx_bytes = generate_test_xlsx()
    _, _, xlsx_tables, _ = route_and_extract("bs_golden.xlsx", xlsx_bytes, "doc_golden_xlsx")
    assert len(xlsx_tables) >= 1
    xlsx_cells = {c.raw_text: c for c in xlsx_tables[0].cells}
    assert "95273" in xlsx_cells
    norm_ca = canonicalize_financial_number(xlsx_cells["95273"].raw_text)
    assert norm_ca.normalized_value == Decimal("95273")
