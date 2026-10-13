from decimal import Decimal
import pytest
from packages.canonical import (
    AccuracyTier,
    BoundingBox,
    Document,
    DocumentStatus,
    EvidenceCoordinates,
    ExtractionMetadata,
    Fact,
    TableCell,
    ValidationResult,
    DerivedMetric,
    AuditEvent,
)


def test_accuracy_tier_values():
    assert AccuracyTier.VERIFIED.value == "V"
    assert AccuracyTier.EXTRACTED.value == "E"
    assert AccuracyTier.ESTIMATED.value == "M"
    assert AccuracyTier.NEEDS_REVIEW.value == "R"
    assert AccuracyTier.FAILED.value == "F"


def test_bounding_box_normalized_coordinates():
    bbox = BoundingBox(page_number=1, x0=100.5, y0=200.0, x1=500.0, y1=800.0)
    assert bbox.page_number == 1
    assert bbox.x0 == 100.5
    assert bbox.unit == "normalized_1000"


def test_table_cell_with_decimal_and_evidence():
    evidence = EvidenceCoordinates(
        document_id="doc_123",
        page_number=1,
        bbox=BoundingBox(page_number=1, x0=10, y0=20, x1=100, y1=40),
        raw_text="$(1,245.50)",
        render_image_key="renders/doc_123/p1.png",
    )
    cell = TableCell(
        id="cell_001",
        table_id="tbl_001",
        row_idx=2,
        col_idx=3,
        raw_text="$(1,245.50)",
        normalized_value=Decimal("-1245.50"),
        currency="USD",
        scale=Decimal("1.0"),
        tier=AccuracyTier.VERIFIED,
        evidence=evidence,
        extraction=ExtractionMetadata(
            engines_used=["pdfplumber", "docling"],
            agreement_score=1.0,
        ),
        validations=[
            ValidationResult(
                rule_id="L2_FOOTING",
                rule_name="Subtotal Footing",
                passed=True,
                expected_value=Decimal("-1245.50"),
                actual_value=Decimal("-1245.50"),
                message="Subtotal matches column sum.",
            )
        ],
    )

    assert isinstance(cell.normalized_value, Decimal)
    assert cell.normalized_value == Decimal("-1245.50")
    assert cell.tier == AccuracyTier.VERIFIED
    assert len(cell.validations) == 1
    assert cell.validations[0].passed is True


def test_fact_model_invariants():
    evidence = EvidenceCoordinates(
        document_id="doc_456",
        page_number=45,
        bbox=BoundingBox(page_number=45, x0=50, y0=100, x1=400, y1=150),
        raw_text="391,036",
        render_image_key="renders/doc_456/p45.png",
    )
    fact = Fact(
        id="fact_rev_2024",
        tenant_id="tenant_alpha",
        document_id="doc_456",
        element_id="cell_45_2_3",
        entity="Apple Inc.",
        metric="total_revenue",
        period="FY2024",
        value=Decimal("391036000000"),
        raw_text="391,036",
        currency="USD",
        scale=Decimal("1000000"),
        tier=AccuracyTier.VERIFIED,
        confidence=1.0,
        evidence=evidence,
    )

    assert isinstance(fact.value, Decimal)
    assert fact.value == Decimal("391036000000")
    assert fact.entity == "Apple Inc."
    assert fact.period == "FY2024"
    assert fact.tier == AccuracyTier.VERIFIED


def test_derived_metric_dag_lineage():
    metric = DerivedMetric(
        id="metric_gross_margin_2024",
        tenant_id="tenant_alpha",
        formula_id="gross_margin",
        formula_name="Gross Margin",
        input_fact_ids=["fact_rev_2024", "fact_cos_2024"],
        calculated_value=Decimal("0.4528"),
        tier=AccuracyTier.VERIFIED,
        lineage_dag={
            "formula": "gross_profit / revenue",
            "inputs": ["fact_rev_2024", "fact_cos_2024"],
            "intermediate": {"gross_profit": "177064000000"},
        },
    )

    assert metric.calculated_value == Decimal("0.4528")
    assert len(metric.input_fact_ids) == 2
    assert "gross_profit" in metric.lineage_dag["intermediate"]
