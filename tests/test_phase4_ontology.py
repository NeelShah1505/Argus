"""
Phase 4 Tests: Financial Metric Ontology, Synonym Resolution & Expanded Formula Registry.
"""

from decimal import Decimal
import pytest

from packages.calc import (
    CalculationError,
    clean_metric_label,
    get_formula_registry,
    resolve_canonical_metric,
)
from packages.canonical import (
    AccuracyTier,
    BoundingBox,
    EvidenceCoordinates,
    ExtractionMetadata,
    Fact,
)


def make_fact(fact_id: str, metric: str, val: Decimal, tier: AccuracyTier = AccuracyTier.VERIFIED) -> Fact:
    ev = EvidenceCoordinates(
        document_id="doc_ont",
        page_number=1,
        bbox=BoundingBox(page_number=1, x0=10, y0=20, x1=200, y1=50),
        raw_text=str(val),
        render_image_key="renders/doc_ont/p1.png",
    )
    return Fact(
        id=fact_id,
        tenant_id="tenant_ont",
        document_id="doc_ont",
        element_id=f"elem_{fact_id}",
        entity="Acme Corp",
        metric=metric,
        period="FY2024",
        value=val,
        raw_text=str(val),
        currency="USD",
        tier=tier,
        confidence=1.0,
        evidence=ev,
        extraction=ExtractionMetadata(engines_used=["test"], agreement_score=1.0),
    )


@pytest.mark.parametrize(
    "raw_input,expected_canonical",
    [
        ("Net Sales", "revenue"),
        ("total revenues", "revenue"),
        ("Turnover", "revenue"),
        ("Revenue from Contracts with Customers", "revenue"),
        ("Product Sales", "revenue"),
        ("Cost of Goods Sold", "cost_of_sales"),
        ("COGS", "cost_of_sales"),
        ("Cost of Revenue", "cost_of_sales"),
        ("Cost of Products Sold", "cost_of_sales"),
        ("Operating Income", "operating_income"),
        ("Income from Operations", "operating_income"),
        ("Operating Profit", "operating_income"),
        ("Net Income (Loss)", "net_income"),
        ("Net Earnings", "net_income"),
        ("Profit for the Year", "net_income"),
        ("Cash and Cash Equivalents", "cash_and_equivalents"),
        ("Total Assets", "total_assets"),
        ("Total Liabilities", "total_liabilities"),
        ("Shareholders' Equity", "stockholders_equity"),
        ("Total Stockholders' Equity", "stockholders_equity"),
        ("Cash Flows from Operating Activities", "operating_cash_flow"),
        ("Capital Expenditures", "capex"),
        ("Free Cash Flow", "free_cash_flow"),
    ],
)
def test_ontology_synonym_resolution(raw_input: str, expected_canonical: str):
    resolved = resolve_canonical_metric(raw_input)
    assert resolved == expected_canonical


def test_ontology_negative_guardrails():
    """Verify that misleading strings do NOT falsely map to revenue."""
    # Deferred revenue is a liability, not revenue
    assert resolve_canonical_metric("Deferred Revenue") != "revenue"
    assert resolve_canonical_metric("Unearned Revenue") != "revenue"
    # Cost of revenue is cost of sales, not revenue
    assert resolve_canonical_metric("Cost of Revenue") == "cost_of_sales"
    # Gross margin is a percentage/ratio, not revenue
    assert resolve_canonical_metric("Gross Margin") != "revenue"


def test_clean_metric_label_strips_footnotes():
    assert clean_metric_label("Total Net Sales (Note 3)*:") == "total net sales"
    assert clean_metric_label("Revenues [1]†") == "revenues"
    assert clean_metric_label("Cost of goods sold (1)") == "cost of goods sold"


def test_expanded_formula_registry_executions():
    registry = get_formula_registry()

    f_rev = make_fact("f_rev", "revenue", Decimal("1000000"))
    f_ni = make_fact("f_ni", "net_income", Decimal("150000"))
    f_ocf = make_fact("f_ocf", "operating_cash_flow", Decimal("220000"))
    f_capex = make_fact("f_capex", "capex", Decimal("50000"))
    f_liab = make_fact("f_liab", "total_liabilities", Decimal("400000"))
    f_eq = make_fact("f_eq", "stockholders_equity", Decimal("600000"))
    f_ca = make_fact("f_ca", "current_assets", Decimal("300000"))
    f_inv = make_fact("f_inv", "inventory", Decimal("60000"))
    f_cl = make_fact("f_cl", "current_liabilities", Decimal("120000"))

    # 1. Net Margin: 150000 / 1000000 = 0.1500 (15.00%)
    m_net = registry.execute_calculation("net_margin", [f_ni, f_rev])
    assert m_net.calculated_value == Decimal("0.1500")

    # 2. Free Cash Flow: 220000 - 50000 = 170000
    m_fcf = registry.execute_calculation("free_cash_flow", [f_ocf, f_capex])
    assert m_fcf.calculated_value == Decimal("170000.00")

    # 3. Debt to Equity: 400000 / 600000 = 0.67
    m_dte = registry.execute_calculation("debt_to_equity", [f_liab, f_eq])
    assert m_dte.calculated_value == Decimal("0.67")

    # 4. Return on Equity: 150000 / 600000 = 0.2500 (25.00%)
    m_roe = registry.execute_calculation("return_on_equity", [f_ni, f_eq])
    assert m_roe.calculated_value == Decimal("0.2500")

    # 5. Quick Ratio: (300000 - 60000) / 120000 = 240000 / 120000 = 2.00
    m_qr = registry.execute_calculation("quick_ratio", [f_ca, f_inv, f_cl])
    assert m_qr.calculated_value == Decimal("2.00")
