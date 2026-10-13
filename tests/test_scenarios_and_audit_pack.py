from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from packages.canonical import (
    AccuracyTier,
    BoundingBox,
    EvidenceCoordinates,
    ExtractionMetadata,
    Fact,
)
from packages.storage.repository import get_document_repo
from tests.fixtures import generate_test_csv

client = TestClient(app)


def test_scenario_modeler_driver_projections():
    payload = {
        "base_revenue": "100000.00",
        "growth_rate_pct": "10.0",
        "target_gross_margin_pct": "40.0",
        "projection_years": 3,
    }
    res = client.post("/api/v1/scenarios", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["label"] == "Scenario Model — Not a Statistical Forecast"
    assert data["is_statistical_forecast"] is False
    projections = data["projections"]
    assert len(projections) == 3

    # Year 1: 100000 * 1.10 = 110000, GP: 110000 * 0.40 = 44000
    assert Decimal(str(projections[0]["projected_revenue"])) == Decimal("110000.00")
    assert Decimal(str(projections[0]["projected_gross_profit"])) == Decimal("44000.00")

    # Year 2: 110000 * 1.10 = 121000, GP: 121000 * 0.40 = 48400
    assert Decimal(str(projections[1]["projected_revenue"])) == Decimal("121000.00")
    assert Decimal(str(projections[1]["projected_gross_profit"])) == Decimal("48400.00")


def test_audit_pack_export_and_attestation():
    csv_bytes = generate_test_csv()
    files = {"file": ("audit_target.csv", csv_bytes, "text/csv")}
    upload_res = client.post("/api/v1/documents?tenant_id=tenant_audit", files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # Request Audit Pack
    pack_res = client.get(f"/api/v1/audit-pack/{doc_id}")
    assert pack_res.status_code == 200
    pack_data = pack_res.json()

    assert "audit_pack_id" in pack_data
    assert pack_data["document"]["id"] == doc_id
    assert pack_data["certificate"]["verified"] is True
    assert "Argus Evidence Contract" in pack_data["certificate"]["attestation"]
    assert len(pack_data["tables_summary"]) >= 1


def test_anomalies_endpoint():
    repo = get_document_repo()
    f1 = Fact(
        id="f_yoy_23",
        tenant_id="tenant_anom",
        document_id="doc_anom",
        element_id="elem_23",
        entity="Global Corp",
        metric="Revenue",
        period="2023",
        value=Decimal("100000"),
        raw_text="100000",
        currency="USD",
        scale=Decimal("1.0"),
        tier=AccuracyTier.VERIFIED,
        confidence=1.0,
        evidence=EvidenceCoordinates(
            document_id="doc_anom",
            page_number=1,
            bbox=BoundingBox(page_number=1, x0=0, y0=0, x1=100, y1=100),
            raw_text="100000",
            render_image_key="key",
        ),
        extraction=ExtractionMetadata(),
    )
    # 80% jump triggers ANOM-03 outlier (>40%)
    f2 = Fact(
        id="f_yoy_24",
        tenant_id="tenant_anom",
        document_id="doc_anom",
        element_id="elem_24",
        entity="Global Corp",
        metric="Revenue",
        period="2024",
        value=Decimal("180000"),
        raw_text="180000",
        currency="USD",
        scale=Decimal("1.0"),
        tier=AccuracyTier.VERIFIED,
        confidence=1.0,
        evidence=EvidenceCoordinates(
            document_id="doc_anom",
            page_number=1,
            bbox=BoundingBox(page_number=1, x0=0, y0=0, x1=100, y1=100),
            raw_text="180000",
            render_image_key="key",
        ),
        extraction=ExtractionMetadata(),
    )
    repo.add_fact(f1)
    repo.add_fact(f2)

    res = client.get("/api/v1/anomalies?document_id=doc_anom")
    assert res.status_code == 200
    anomalies = res.json()
    assert len(anomalies) >= 1
    outlier = [a for a in anomalies if a["rule_id"] == "ANOM-03"][0]
    assert "abnormal YoY change" in outlier["description"]
