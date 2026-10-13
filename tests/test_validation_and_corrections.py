from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from packages.canonical import (
    AccuracyTier,
    ExtractionMetadata,
    ValidationResult,
)
from packages.validate import (
    check_yoy_outlier,
    determine_cell_tier,
    validate_balance_sheet_identity,
    validate_sign_sanity,
    validate_subtotal_footing,
)
from tests.fixtures import generate_test_csv

client = TestClient(app)


def test_subtotal_footing_validation():
    # Balanced
    items = [Decimal("100.00"), Decimal("250.00"), Decimal("50.00")]
    total = Decimal("400.00")
    res_pass = validate_subtotal_footing(total, items)
    assert res_pass.passed is True
    assert res_pass.discrepancy is None

    # Off by one dollar
    total_broken = Decimal("401.00")
    res_fail = validate_subtotal_footing(total_broken, items)
    assert res_fail.passed is False
    assert res_fail.discrepancy == Decimal("1.00")
    assert res_fail.expected_value == Decimal("401.00")
    assert res_fail.actual_value == Decimal("400.00")


def test_balance_sheet_identity():
    assets = Decimal("1000000.00")
    liab = Decimal("600000.00")
    equity = Decimal("400000.00")

    # Balanced
    res_pass = validate_balance_sheet_identity(assets, liab, equity)
    assert res_pass.passed is True

    # Imbalanced
    bad_equity = Decimal("350000.00")
    res_fail = validate_balance_sheet_identity(assets, liab, bad_equity)
    assert res_fail.passed is False
    assert res_fail.discrepancy == Decimal("50000.00")


def test_sign_sanity():
    res_pos_rev = validate_sign_sanity("Total Revenue", Decimal("500000"))
    assert res_pos_rev.passed is True

    res_neg_rev = validate_sign_sanity("Total Revenue", Decimal("-500000"))
    assert res_neg_rev.passed is False
    assert "Sign anomaly" in res_neg_rev.message


def test_tier_determination_logic():
    extraction_dual = ExtractionMetadata(engines_used=["pdfplumber", "docling"], agreement_score=1.0)
    extraction_single = ExtractionMetadata(engines_used=["pdfplumber"], agreement_score=1.0)

    val_pass = [ValidationResult(rule_id="R1", rule_name="Test Pass", passed=True, message="ok")]
    val_fail = [ValidationResult(rule_id="R2", rule_name="Test Fail", passed=False, message="failed")]

    # Dual engine + validations passed -> Tier V (Verified)
    assert determine_cell_tier(extraction_dual, val_pass, has_valid_evidence=True) == AccuracyTier.VERIFIED

    # Check failure -> Tier R (Needs Review)
    assert determine_cell_tier(extraction_dual, val_fail, has_valid_evidence=True) == AccuracyTier.NEEDS_REVIEW

    # Chart measured -> Tier M (Estimated)
    assert determine_cell_tier(extraction_dual, val_pass, has_valid_evidence=True, is_chart_measured=True) == AccuracyTier.ESTIMATED


def test_correction_workflow_api():
    csv_bytes = generate_test_csv()
    files = {"file": ("q3_segments.csv", csv_bytes, "text/csv")}
    upload_res = client.post("/api/v1/documents?tenant_id=tenant_review", files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]
    orig_ver = upload_res.json()["version"]

    # Get elements
    elem_res = client.get(f"/api/v1/documents/{doc_id}/elements")
    assert elem_res.status_code == 200
    tables = elem_res.json()["tables"]
    cell_to_edit = tables[0]["cells"][1]  # row 0, col 1
    cell_id = cell_to_edit["id"]

    # Submit correction
    patch_payload = {
        "document_id": doc_id,
        "new_raw_text": "(1,500.00)",
        "reviewer_id": "auditor_42",
        "reason": "Reconciled with footnote 4 adjustment",
    }
    patch_res = client.patch(f"/api/v1/documents/elements/{cell_id}", json=patch_payload)
    assert patch_res.status_code == 200
    patch_data = patch_res.json()

    assert patch_data["status"] == "corrected"
    assert patch_data["new_version"] == orig_ver + 1
    updated_cell = patch_data["cell"]
    assert updated_cell["raw_text"] == "(1,500.00)"
    assert Decimal(str(updated_cell["normalized_value"])) == Decimal("-1500.00")
    assert updated_cell["tier"] == AccuracyTier.VERIFIED.value

    # Verify audit event in document validation endpoint
    val_res = client.get(f"/api/v1/documents/{doc_id}/validation")
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert len(val_data["audit_events"]) >= 1
    audit_evt = val_data["audit_events"][0]
    assert audit_evt["actor_id"] == "auditor_42"
    assert audit_evt["event_type"] == "CELL_CORRECTION"
    assert audit_evt["details"]["new_value"] == "(1,500.00)"
