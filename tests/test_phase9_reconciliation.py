"""
Phase 9 Tests: Cross-Period Financial Reconciliation & Restatement Engine.
"""

from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from packages.calc import (
    CrossStatementCheck,
    FootnoteReconciliationCheck,
    ReconciliationReport,
    RestatementFlag,
    detect_cross_period_restatements,
    reconcile_cash_movement,
    reconcile_footnote_schedule,
    reconcile_retained_earnings,
    run_full_reconciliation,
)
from packages.canonical import (
    AccuracyTier,
    BoundingBox,
    EvidenceCoordinates,
    Fact,
)
from packages.storage.repository import get_document_repo


def _make_fact(
    id: str,
    doc_id: str,
    entity: str,
    metric: str,
    period: str,
    value: Decimal,
    currency: str = "USD",
) -> Fact:
    ev = EvidenceCoordinates(
        document_id=doc_id,
        page_number=1,
        bbox=BoundingBox(page_number=1, x0=10, y0=20, x1=100, y1=50),
        raw_text=f"{value} {currency}",
        render_image_key=f"{doc_id}_p1.png",
    )
    return Fact(
        id=id,
        tenant_id="tenant_default",
        document_id=doc_id,
        element_id=f"el_{id}",
        entity=entity,
        metric=metric,
        period=period,
        value=value,
        raw_text=f"{value}",
        currency=currency,
        scale=Decimal("1.0"),
        tier=AccuracyTier.VERIFIED,
        confidence=1.0,
        evidence=ev,
    )


def test_cross_period_restatement_detection():
    # Doc A reports Net Sales of 100,000 in FY2023
    f1 = _make_fact("f1", "doc_q1", "Acme Corp", "Net Sales", "FY2023", Decimal("100000"))
    # Doc B subsequently reports Revenue of 108,000 for the same FY2023 (8% restatement)
    f2 = _make_fact("f2", "doc_10k", "Acme Corp", "Revenue", "FY2023", Decimal("108000"))

    flags = detect_cross_period_restatements([f1, f2])
    assert len(flags) == 1
    flag = flags[0]
    assert flag.canonical_metric == "revenue"
    assert flag.period == "FY2023"
    assert flag.original_value == Decimal("100000")
    assert flag.new_value == Decimal("108000")
    assert flag.delta == Decimal("8000")
    assert flag.delta_pct == Decimal("8.00")
    assert flag.severity == "CRITICAL_RESTATEMENT"
    assert flag.original_doc_id == "doc_q1"
    assert flag.new_doc_id == "doc_10k"


def test_cash_movement_reconciliation():
    beg_cash = _make_fact("c_beg", "doc_1", "Acme Corp", "Cash and cash equivalents", "FY2023", Decimal("29965"))
    end_cash = _make_fact("c_end", "doc_1", "Acme Corp", "Cash and cash equivalents", "FY2024", Decimal("30737"))

    # Balanced CFS net change: 30737 - 29965 = 772
    net_cf_balanced = _make_fact("c_net", "doc_1", "Acme Corp", "Net cash from operating activities", "FY2024", Decimal("772"))
    check_ok = reconcile_cash_movement(beg_cash, end_cash, net_cf_balanced)
    assert check_ok.is_balanced is True
    assert check_ok.delta == Decimal("0")

    # Broken CFS net change: reports 500 (delta 272)
    net_cf_broken = _make_fact("c_net2", "doc_1", "Acme Corp", "Net cash from operating activities", "FY2024", Decimal("500"))
    check_fail = reconcile_cash_movement(beg_cash, end_cash, net_cf_broken)
    assert check_fail.is_balanced is False
    assert check_fail.delta == Decimal("272")


def test_retained_earnings_rollforward():
    beg_re = _make_fact("re_beg", "doc_1", "Acme Corp", "Retained Earnings", "FY2023", Decimal("10000"))
    end_re = _make_fact("re_end", "doc_1", "Acme Corp", "Retained Earnings", "FY2024", Decimal("13000"))
    ni = _make_fact("ni", "doc_1", "Acme Corp", "Net Income", "FY2024", Decimal("4000"))
    div = _make_fact("div", "doc_1", "Acme Corp", "Dividends paid", "FY2024", Decimal("1000"))

    # Balanced: 10000 + 4000 - 1000 = 13000
    check = reconcile_retained_earnings(beg_re, end_re, ni, div)
    assert check.is_balanced is True
    assert check.delta == Decimal("0")


def test_footnote_schedule_reconciliation():
    total_debt = _make_fact("debt_total", "doc_1", "Acme Corp", "Term Debt", "FY2024", Decimal("95000"))

    tranche1 = _make_fact("t1", "doc_1", "Acme Corp", "Floating rate notes due 2026", "FY2024", Decimal("15000"))
    tranche2 = _make_fact("t2", "doc_1", "Acme Corp", "3.25% senior notes due 2029", "FY2024", Decimal("50000"))
    tranche3 = _make_fact("t3", "doc_1", "Acme Corp", "4.10% notes due 2034", "FY2024", Decimal("30000"))

    check = reconcile_footnote_schedule(total_debt, [tranche1, tranche2, tranche3])
    assert check.is_balanced is True
    assert check.footnote_schedule_sum == Decimal("95000")
    assert check.delta == Decimal("0")

    # If tranche 3 is missing 5,000
    tranche3_corrupt = _make_fact("t3c", "doc_1", "Acme Corp", "4.10% notes due 2034", "FY2024", Decimal("25000"))
    check_corrupt = reconcile_footnote_schedule(total_debt, [tranche1, tranche2, tranche3_corrupt])
    assert check_corrupt.is_balanced is False
    assert check_corrupt.delta == Decimal("5000")


def test_full_reconciliation_report_and_api():
    repo = get_document_repo()

    f1 = _make_fact("api_f1", "doc_p9_1", "TechCo", "Operating Revenue", "FY2023", Decimal("50000"))
    f2 = _make_fact("api_f2", "doc_p9_2", "TechCo", "Net Sales", "FY2023", Decimal("53000"))
    repo.add_fact(f1)
    repo.add_fact(f2)

    client = TestClient(app)
    response = client.get("/api/v1/reconciliation?entity=TechCo")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ("RESTATEMENTS_DETECTED", "UNBALANCED")
    assert data["restatements_count"] >= 1
    assert any(r["canonical_metric"] == "revenue" for r in data["restatements"])
