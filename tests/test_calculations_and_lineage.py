from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from packages.calc import CalculationError, get_formula_registry, get_lineage_graph
from packages.canonical import (
    AccuracyTier,
    BoundingBox,
    EvidenceCoordinates,
    ExtractionMetadata,
    Fact,
)
from packages.storage.repository import get_document_repo

client = TestClient(app)


def make_test_fact(
    fact_id: str,
    metric: str,
    period: str,
    value: Decimal,
    currency: str = "USD",
    tier: AccuracyTier = AccuracyTier.VERIFIED,
) -> Fact:
    return Fact(
        id=fact_id,
        tenant_id="tenant_calc",
        document_id="doc_calc_1",
        element_id=f"elem_{fact_id}",
        entity="Acme Corp",
        metric=metric,
        period=period,
        value=value,
        raw_text=str(value),
        currency=currency,
        scale=Decimal("1.0"),
        tier=tier,
        confidence=1.0,
        evidence=EvidenceCoordinates(
            document_id="doc_calc_1",
            page_number=1,
            bbox=BoundingBox(page_number=1, x0=10, y0=20, x1=200, y1=50),
            raw_text=str(value),
            render_image_key="renders/doc_calc_1/p1.png",
        ),
        extraction=ExtractionMetadata(engines_used=["pdfplumber", "docling"], agreement_score=1.0),
    )


def test_growth_calculation_exact():
    registry = get_formula_registry()
    f_curr = make_test_fact("f_rev_24", "revenue", "FY2024", Decimal("125000.00"))
    f_prev = make_test_fact("f_rev_23", "revenue", "FY2023", Decimal("100000.00"))

    derived = registry.execute_calculation("revenue_growth", [f_curr, f_prev])
    assert derived.calculated_value == Decimal("0.2500")
    assert derived.tier == AccuracyTier.VERIFIED
    assert len(derived.lineage_dag["inputs"]) == 2


def test_currency_mismatch_guard():
    registry = get_formula_registry()
    f_usd = make_test_fact("f_usd", "revenue", "FY2024", Decimal("100000"), currency="USD")
    f_eur = make_test_fact("f_eur", "revenue", "FY2023", Decimal("80000"), currency="EUR")

    with pytest.raises(CalculationError, match="Currency mismatch"):
        registry.execute_calculation("revenue_growth", [f_usd, f_eur])


def test_tier_inheritance_and_blocked_r_tier():
    registry = get_formula_registry()

    # If one input is Estimated (M), output inherits Estimated (M)
    f_v = make_test_fact("f_v", "revenue", "FY2024", Decimal("110000"), tier=AccuracyTier.VERIFIED)
    f_m = make_test_fact("f_m", "revenue", "FY2023", Decimal("100000"), tier=AccuracyTier.ESTIMATED)
    derived = registry.execute_calculation("revenue_growth", [f_v, f_m])
    assert derived.tier == AccuracyTier.ESTIMATED

    # If one input is Needs Review (R), calculation is BLOCKED
    f_r = make_test_fact("f_r", "revenue", "FY2023", Decimal("100000"), tier=AccuracyTier.NEEDS_REVIEW)
    with pytest.raises(CalculationError, match="Calculation blocked"):
        registry.execute_calculation("revenue_growth", [f_v, f_r])


def test_calculation_api_and_lineage_dag():
    repo = get_document_repo()
    f_curr = make_test_fact("fact_api_rev_24", "revenue", "FY2024", Decimal("200000"))
    f_prev = make_test_fact("fact_api_rev_23", "revenue", "FY2023", Decimal("160000"))
    repo.add_fact(f_curr)
    repo.add_fact(f_prev)

    # Call API to run calculation
    payload = {
        "formula_id": "revenue_growth",
        "fact_ids": ["fact_api_rev_24", "fact_api_rev_23"],
    }
    res = client.post("/api/v1/calculations/run", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["calculated_value"] == "0.2500"
    metric_id = data["id"]

    # Verify lineage endpoint returns DAG
    lin_res = client.get(f"/api/v1/lineage/{metric_id}")
    assert lin_res.status_code == 200
    lin_data = lin_res.json()
    assert lin_data["metric_id"] == metric_id
    assert len(lin_data["lineage_dag"]["inputs"]) == 2

    # Invalidate fact -> metric is purged from active graph
    lineage = get_lineage_graph()
    affected = lineage.invalidate_fact("fact_api_rev_24")
    assert metric_id in affected
    assert lineage.get_metric(metric_id) is None
