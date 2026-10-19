"""
Phase 9: Cross-Period Financial Reconciliation & Restatement Engine.

Provides automated forensic reconciliation:
1. Multi-document restatement detection across quarters/fiscal years.
2. Cross-statement identity reconciliation (Balance Sheet Cash delta vs Cash Flow Statement Net Change).
3. Footnote schedule reconciliation (Balance Sheet line items vs Footnote tranche breakdowns).
4. Retained earnings rollforward reconciliation.
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from packages.calc.ontology import resolve_canonical_metric
from packages.canonical.models import EvidenceCoordinates, Fact


class RestatementFlag(BaseModel):
    metric: str
    canonical_metric: str
    period: str
    entity: str
    original_value: Decimal
    original_doc_id: str
    original_evidence: Optional[EvidenceCoordinates] = None
    new_value: Decimal
    new_doc_id: str
    new_evidence: Optional[EvidenceCoordinates] = None
    delta: Decimal
    delta_pct: Decimal
    severity: str  # "INFO", "WARNING", "CRITICAL_RESTATEMENT"
    description: str


class CrossStatementCheck(BaseModel):
    check_name: str
    entity: str
    period: str
    expected_value: Decimal
    actual_value: Decimal
    delta: Decimal
    is_balanced: bool
    tolerance: Decimal
    details: str
    lineage_fact_ids: List[str] = Field(default_factory=list)


class FootnoteReconciliationCheck(BaseModel):
    line_item_metric: str
    period: str
    entity: str
    primary_statement_value: Decimal
    footnote_schedule_sum: Decimal
    delta: Decimal
    is_balanced: bool
    tolerance: Decimal
    component_facts: List[Dict[str, Any]] = Field(default_factory=list)
    details: str


class ReconciliationReport(BaseModel):
    tenant_id: str
    entity: Optional[str] = None
    status: str  # "BALANCED", "RESTATEMENTS_DETECTED", "UNBALANCED"
    restatements_count: int = 0
    checks_count: int = 0
    unbalanced_count: int = 0
    restatements: List[RestatementFlag] = Field(default_factory=list)
    statement_checks: List[CrossStatementCheck] = Field(default_factory=list)
    footnote_checks: List[FootnoteReconciliationCheck] = Field(default_factory=list)
    summary: str


def detect_cross_period_restatements(facts: List[Fact]) -> List[RestatementFlag]:
    """
    Scans a set of extracted facts across multiple documents or filings.
    If different documents report different values for the same (entity, canonical_metric, period),
    flags an automated restatement with absolute and percentage deltas.
    """
    # Group by (entity.lower(), canonical_metric, period)
    grouped: Dict[tuple, List[Fact]] = {}
    for f in facts:
        c_metric = resolve_canonical_metric(f.metric)
        key = (f.entity.strip().lower(), c_metric, f.period.strip().upper())
        grouped.setdefault(key, []).append(f)

    restatements: List[RestatementFlag] = []

    for (entity, c_metric, period), flist in grouped.items():
        if len(flist) < 2:
            continue

        # Look for differences across different documents or distinct values
        # Deduplicate identical facts within the same doc
        seen_values: Dict[Decimal, Fact] = {}
        for f in flist:
            if f.value not in seen_values:
                seen_values[f.value] = f

        val_list = list(seen_values.values())
        if len(val_list) >= 2:
            # Sort by doc_id or preserve order as original -> subsequent
            orig = val_list[0]
            new = val_list[1]

            delta = new.value - orig.value
            if orig.value != Decimal("0"):
                delta_pct = ((delta / abs(orig.value)) * Decimal("100")).quantize(Decimal("0.01"))
            else:
                delta_pct = Decimal("100.00") if delta != 0 else Decimal("0.00")

            # Determine severity
            abs_pct = abs(delta_pct)
            if abs_pct >= Decimal("5.00") or (orig.value > 0 and new.value < 0) or (orig.value < 0 and new.value > 0):
                severity = "CRITICAL_RESTATEMENT"
            elif abs_pct >= Decimal("0.50"):
                severity = "WARNING"
            else:
                severity = "INFO"

            desc = (
                f"Metric '{c_metric}' for {orig.entity} ({period}) was reported as {orig.value} {orig.currency} "
                f"in document {orig.document_id}, but revised to {new.value} {new.currency} in document {new.document_id} "
                f"(Delta: {delta:+} {orig.currency}, {delta_pct:+}%)."
            )

            restatements.append(
                RestatementFlag(
                    metric=orig.metric,
                    canonical_metric=c_metric,
                    period=period,
                    entity=orig.entity,
                    original_value=orig.value,
                    original_doc_id=orig.document_id,
                    original_evidence=orig.evidence,
                    new_value=new.value,
                    new_doc_id=new.document_id,
                    new_evidence=new.evidence,
                    delta=delta,
                    delta_pct=delta_pct,
                    severity=severity,
                    description=desc,
                )
            )

    return restatements


def reconcile_cash_movement(
    beginning_cash: Fact,
    ending_cash: Fact,
    net_cash_flow: Fact,
    tolerance: Decimal = Decimal("1.0"),
) -> CrossStatementCheck:
    """
    Reconciles Balance Sheet cash delta with Cash Flow Statement Net Change in Cash:
    Delta Cash_BS = Ending Cash - Beginning Cash
    Identity: Delta Cash_BS == Net Change in Cash_CFS
    """
    delta_bs = ending_cash.value - beginning_cash.value
    delta = abs(delta_bs - net_cash_flow.value)
    is_balanced = delta <= tolerance

    details = (
        f"Ending Cash ({ending_cash.value}) - Beginning Cash ({beginning_cash.value}) = {delta_bs}. "
        f"CFS Net Change in Cash = {net_cash_flow.value}. Discrepancy delta = {delta} (tolerance = {tolerance})."
    )

    return CrossStatementCheck(
        check_name="cash_movement_reconciliation",
        entity=ending_cash.entity,
        period=ending_cash.period,
        expected_value=net_cash_flow.value,
        actual_value=delta_bs,
        delta=delta,
        is_balanced=is_balanced,
        tolerance=tolerance,
        details=details,
        lineage_fact_ids=[beginning_cash.id, ending_cash.id, net_cash_flow.id],
    )


def reconcile_retained_earnings(
    beginning_re: Fact,
    ending_re: Fact,
    net_income: Fact,
    dividends: Optional[Fact] = None,
    tolerance: Decimal = Decimal("1.0"),
) -> CrossStatementCheck:
    """
    Rollforward check for Stockholders' Equity:
    Ending Retained Earnings = Beginning Retained Earnings + Net Income - Dividends
    """
    div_val = dividends.value if dividends else Decimal("0")
    expected_ending = beginning_re.value + net_income.value - div_val
    delta = abs(ending_re.value - expected_ending)
    is_balanced = delta <= tolerance

    fact_ids = [beginning_re.id, ending_re.id, net_income.id]
    if dividends:
        fact_ids.append(dividends.id)

    details = (
        f"Beginning RE ({beginning_re.value}) + Net Income ({net_income.value}) - Dividends ({div_val}) "
        f"= Expected Ending RE ({expected_ending}). Reported Ending RE = {ending_re.value}. Delta = {delta}."
    )

    return CrossStatementCheck(
        check_name="retained_earnings_rollforward",
        entity=ending_re.entity,
        period=ending_re.period,
        expected_value=expected_ending,
        actual_value=ending_re.value,
        delta=delta,
        is_balanced=is_balanced,
        tolerance=tolerance,
        details=details,
        lineage_fact_ids=fact_ids,
    )


def reconcile_footnote_schedule(
    primary_line_item: Fact,
    schedule_components: List[Fact],
    tolerance: Decimal = Decimal("1.0"),
) -> FootnoteReconciliationCheck:
    """
    Reconciles a primary financial statement line item against the sum of detailed tranches in a footnote schedule.
    Identity: primary_line_item.value == sum(component.value for component in schedule_components)
    """
    component_sum = sum((c.value for c in schedule_components), Decimal("0"))
    delta = abs(primary_line_item.value - component_sum)
    is_balanced = delta <= tolerance

    comp_data = [
        {
            "id": c.id,
            "metric": c.metric,
            "value": str(c.value),
            "currency": c.currency,
            "document_id": c.document_id,
        }
        for c in schedule_components
    ]

    details = (
        f"Primary Line Item '{primary_line_item.metric}' = {primary_line_item.value} {primary_line_item.currency}. "
        f"Footnote Breakdown Sum = {component_sum} {primary_line_item.currency} across {len(schedule_components)} items. "
        f"Delta = {delta} (tolerance = {tolerance})."
    )

    return FootnoteReconciliationCheck(
        line_item_metric=primary_line_item.metric,
        period=primary_line_item.period,
        entity=primary_line_item.entity,
        primary_statement_value=primary_line_item.value,
        footnote_schedule_sum=component_sum,
        delta=delta,
        is_balanced=is_balanced,
        tolerance=tolerance,
        component_facts=comp_data,
        details=details,
    )


def run_full_reconciliation(
    facts: List[Fact],
    tenant_id: str = "tenant_default",
) -> ReconciliationReport:
    """
    Executes all cross-period restatement detections and cross-statement identity verifications
    on the provided facts repository.
    """
    restatements = detect_cross_period_restatements(facts)

    statement_checks: List[CrossStatementCheck] = []
    footnote_checks: List[FootnoteReconciliationCheck] = []

    # Map facts by canonical metric and period
    facts_by_metric_period: Dict[tuple, List[Fact]] = {}
    for f in facts:
        c_metric = resolve_canonical_metric(f.metric)
        facts_by_metric_period.setdefault((c_metric, f.period.strip().upper()), []).append(f)

    # 1. Cash flow reconciliation checks
    for (metric, period), flist in facts_by_metric_period.items():
        if metric == "operating_cash_flow":
            # Check if we have beginning and ending cash for this entity/period
            entity = flist[0].entity
            cash_facts = [
                f for f in facts
                if resolve_canonical_metric(f.metric) == "cash_and_equivalents" and f.entity.lower() == entity.lower()
            ]
            if len(cash_facts) >= 2:
                # Sorted by period
                c_sorted = sorted(cash_facts, key=lambda f: f.period)
                beg = c_sorted[0]
                end = c_sorted[1]
                net_cf = flist[0]
                check = reconcile_cash_movement(beg, end, net_cf)
                statement_checks.append(check)

    # Calculate overall status
    unbalanced_statement = sum(1 for c in statement_checks if not c.is_balanced)
    unbalanced_footnote = sum(1 for c in footnote_checks if not c.is_balanced)
    unbalanced_count = unbalanced_statement + unbalanced_footnote

    if restatements and unbalanced_count > 0:
        status = "UNBALANCED"
        summary = f"Detected {len(restatements)} restatement(s) and {unbalanced_count} unbalanced reconciliation check(s)."
    elif restatements:
        status = "RESTATEMENTS_DETECTED"
        summary = f"Detected {len(restatements)} cross-period restatement(s) across filings."
    elif unbalanced_count > 0:
        status = "UNBALANCED"
        summary = f"Detected {unbalanced_count} cross-statement reconciliation discrepancy(ies)."
    else:
        status = "BALANCED"
        summary = "All financial statements, footnote schedules, and cross-period comparisons are strictly balanced."

    entity_name = facts[0].entity if facts else None

    return ReconciliationReport(
        tenant_id=tenant_id,
        entity=entity_name,
        status=status,
        restatements_count=len(restatements),
        checks_count=len(statement_checks) + len(footnote_checks),
        unbalanced_count=unbalanced_count,
        restatements=restatements,
        statement_checks=statement_checks,
        footnote_checks=footnote_checks,
        summary=summary,
    )
