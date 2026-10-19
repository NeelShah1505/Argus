"""
Phase 1 Tests: EDGAR XBRL Ground Truth Generation, Benchmark Engine & Scoring Rubric.
"""

from decimal import Decimal
import json
from pathlib import Path
import pytest

from evals.edgar_downloader import fetch_company_facts
from evals.ground_truth_builder import (
    GroundTruthFiling,
    build_ground_truth_from_facts,
    save_ground_truth_filing,
)
from evals.scoring import (
    ScoreSummary,
    evaluate_extraction_run,
    format_benchmark_markdown,
)
from packages.canonical import (
    AccuracyTier,
    BoundingBox,
    EvidenceCoordinates,
    ExtractionMetadata,
    Fact,
    Table,
    TableCell,
)


def test_edgar_facts_caching(tmp_path: Path):
    """Verify that edgar_downloader properly caches and reads facts from disk."""
    sample_facts = {
        "cik": 320193,
        "entityName": "Apple Inc.",
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {"val": 394328000000, "fy": 2024, "fp": "FY", "form": "10-K"}
                        ]
                    }
                }
            }
        },
    }
    cache_file = tmp_path / "CIK0000320193.json"
    cache_file.write_text(json.dumps(sample_facts), encoding="utf-8")

    data = fetch_company_facts("0000320193", cache_dir=tmp_path)
    assert data["entityName"] == "Apple Inc."
    assert "Revenues" in data["facts"]["us-gaap"]


def test_ground_truth_builder_gaap_mapping(tmp_path: Path):
    """Verify ground truth extraction handles critical GAAP metrics, scale, and negative signs."""
    sample_facts = {
        "cik": 789019,
        "entityName": "Microsoft Corporation",
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {
                    "units": {
                        "USD": [
                            {"val": 245122000000, "fy": 2024, "fp": "FY", "form": "10-K"}
                        ]
                    }
                },
                "CostOfGoodsAndServicesSold": {
                    "units": {
                        "USD": [
                            {"val": 74500000000, "fy": 2024, "fp": "FY", "form": "10-K"}
                        ]
                    }
                },
                "Assets": {
                    "units": {
                        "USD": [
                            {"val": 512163000000, "fy": 2024, "fp": "FY", "form": "10-K"}
                        ]
                    }
                },
            }
        },
    }
    gt = build_ground_truth_from_facts(sample_facts, ticker="MSFT", fiscal_year=2024)
    assert gt.ticker == "MSFT"
    assert gt.fiscal_year == 2024
    assert len(gt.critical_fields) == 3

    metrics = {f.metric: f for f in gt.critical_fields}
    assert metrics["total_revenue"].expected_value == Decimal("245122000000")
    assert metrics["total_revenue"].is_negative is False

    assert metrics["cost_of_sales"].expected_value == Decimal("74500000000")
    assert metrics["cost_of_sales"].is_negative is True  # Cost of sales sign convention

    # Verify serialization
    saved_path = save_ground_truth_filing(gt, output_dir=tmp_path)
    assert saved_path.exists()
    content = json.loads(saved_path.read_text(encoding="utf-8"))
    assert content["ticker"] == "MSFT"


def test_scoring_rubric_silent_error_detection():
    """Verify the scoring engine detects silent errors and flags failed quality gates."""
    # Create mock extracted facts and cells
    evidence_good = EvidenceCoordinates(
        document_id="doc_eval",
        page_number=1,
        bbox=BoundingBox(page_number=1, x0=10, y0=10, x1=100, y1=30),
        raw_text="394,328",
        render_image_key="renders/doc_eval/p1.png",
    )
    c1 = TableCell(
        id="c1",
        table_id="t1",
        row_idx=0,
        col_idx=1,
        is_header=False,
        raw_text="394,328",
        tier=AccuracyTier.VERIFIED,
        evidence=evidence_good,
    )
    # Silent corrupt cell (contains replacement character \ufffd in Verified tier)
    c2 = TableCell(
        id="c2",
        table_id="t1",
        row_idx=1,
        col_idx=1,
        is_header=False,
        raw_text="12\ufffd500",
        tier=AccuracyTier.VERIFIED,
        evidence=evidence_good,
    )
    # Quarantined cell in Tier R
    c3 = TableCell(
        id="c3",
        table_id="t1",
        row_idx=2,
        col_idx=1,
        is_header=False,
        raw_text="50,000",
        tier=AccuracyTier.NEEDS_REVIEW,
        evidence=evidence_good,
    )

    t = Table(
        id="t1",
        document_id="doc_eval",
        page_number=1,
        title="Income Statement",
        rows_count=3,
        cols_count=2,
        cells=[c1, c2, c3],
        bbox=BoundingBox(page_number=1, x0=0, y0=0, x1=500, y1=500),
    )

    fact_rev = Fact(
        id="f_rev",
        tenant_id="tenant_eval",
        document_id="doc_eval",
        element_id="c1",
        entity="Apple Inc.",
        metric="total_revenue",
        period="FY2024",
        value=Decimal("394328000000"),
        raw_text="394,328",
        scale=Decimal("1000000"),
        currency="USD",
        tier=AccuracyTier.VERIFIED,
        confidence=1.0,
        evidence=evidence_good,
        extraction=ExtractionMetadata(engines_used=["pdfplumber"], agreement_score=1.0),
    )

    gt_fields = [
        {"metric": "total_revenue", "expected_value": "394328000000", "scale": "1000000"},
        {"metric": "net_income", "expected_value": "99803000000", "scale": "1000000"},
    ]

    summary = evaluate_extraction_run(
        extracted_facts=[fact_rev],
        extracted_tables=[t],
        ground_truth_fields=gt_fields,
        document_id="doc_eval",
        ticker="AAPL",
        fiscal_year=2024,
    )

    # Critical field: 1 matched out of 2
    assert summary.critical_fields_matched == 1
    assert summary.critical_fields_total == 2
    assert summary.critical_field_accuracy == 0.5

    # Provenance coverage
    assert summary.provenance_coverage_pct == 1.0

    # Silent error rate: c2 has corrupt char in Verified tier -> 1 silent error out of 2 unflagged
    assert summary.silent_errors_count == 1
    assert summary.silent_error_rate == 0.5  # 50% SER
    assert summary.passed_all_gates is False
    assert any("Silent Error Rate" in err for err in summary.gate_failures)

    # Markdown format
    md = format_benchmark_markdown(summary)
    assert "Score Card: AAPL" in md
    assert "Silent Error Rate (SER)" in md
    assert "FAILED GATES" in md
