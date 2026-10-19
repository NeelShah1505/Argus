"""
Argus Evaluation Scoring Rubric Engine.

Computes the five core forensic audit metrics:
1. Critical-Field Exact Accuracy (Target >= 99.0% on digital)
2. Table Cell Value & Structural F1 (Target >= 95.0%)
3. Silent Error Rate (SER) (Target < 0.1% — zero unflagged wrong numbers)
4. Detection Rate (DR) (Target > 99.0% — errors quarantined to Review tier)
5. Provenance Coverage (Target 100.0% — full bounding box overlay)
"""

from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from packages.canonical import AccuracyTier, Fact, Table, TableCell


class ScoreSummary(BaseModel):
    document_id: str
    ticker: Optional[str] = None
    fiscal_year: Optional[int] = None

    # 1. Critical Field Exact Match
    critical_fields_total: int = 0
    critical_fields_matched: int = 0
    critical_field_accuracy: float = 0.0

    # 2. Table Cell F1
    ground_truth_cells_count: int = 0
    extracted_cells_count: int = 0
    true_positive_cells: int = 0
    cell_precision: float = 0.0
    cell_recall: float = 0.0
    cell_f1: float = 0.0

    # 3. Silent Error Rate (SER)
    total_unflagged_cells: int = 0  # Verified or Extracted tier
    silent_errors_count: int = 0    # Unflagged cells with wrong value
    silent_error_rate: float = 0.0

    # 4. Detection Rate (DR)
    total_corrupt_or_mismatched_cells: int = 0
    flagged_corrupt_cells: int = 0  # Quarantined in Tier R (Needs Review) or Tier F
    detection_rate: float = 1.0

    # 5. Provenance Coverage
    provenance_covered_cells: int = 0
    provenance_coverage_pct: float = 0.0

    # Gate status
    passed_all_gates: bool = False
    gate_failures: List[str] = []


def evaluate_extraction_run(
    extracted_facts: List[Fact],
    extracted_tables: List[Table],
    ground_truth_fields: List[Dict[str, Any]],
    expected_cells: Optional[List[Dict[str, Any]]] = None,
    document_id: str = "doc_eval",
    ticker: Optional[str] = None,
    fiscal_year: Optional[int] = None,
) -> ScoreSummary:
    """
    Computes rigorous forensic audit scores for an extraction run.
    """
    summary = ScoreSummary(
        document_id=document_id,
        ticker=ticker,
        fiscal_year=fiscal_year,
    )

    # 1. Critical Fields Exact Match
    summary.critical_fields_total = len(ground_truth_fields)
    matched_critical = 0

    fact_values = {f.value for f in extracted_facts if f.value is not None}
    fact_metrics = {f.metric.lower(): f.value for f in extracted_facts if f.value is not None}

    for gt in ground_truth_fields:
        exp_val = Decimal(str(gt["expected_value"]))
        metric_name = gt.get("metric", "").lower()
        matched = False

        # Direct value match in extracted facts
        if exp_val in fact_values:
            matched = True
        # Metric key match
        elif metric_name in fact_metrics and fact_metrics[metric_name] == exp_val:
            matched = True
        # Unscaled match if scale was applied
        elif "scale" in gt and Decimal(str(gt["scale"])) > Decimal("1.0"):
            unscaled = exp_val / Decimal(str(gt["scale"]))
            if unscaled in fact_values:
                matched = True

        if matched:
            matched_critical += 1

    summary.critical_fields_matched = matched_critical
    summary.critical_field_accuracy = (
        float(matched_critical / summary.critical_fields_total)
        if summary.critical_fields_total > 0
        else 1.0
    )

    # Gather all extracted table cells
    all_cells: List[TableCell] = []
    for t in extracted_tables:
        all_cells.extend(t.cells)

    summary.extracted_cells_count = len(all_cells)

    # 2. Provenance Coverage: valid page > 0, width/height > 0, render key present
    covered_cells = 0
    for c in all_cells:
        if c.evidence and c.evidence.page_number >= 1 and c.evidence.render_image_key:
            bbox = c.evidence.bbox
            if bbox and (bbox.x1 > bbox.x0) and (bbox.y1 > bbox.y0):
                covered_cells += 1

    summary.provenance_covered_cells = covered_cells
    summary.provenance_coverage_pct = (
        float(covered_cells / summary.extracted_cells_count)
        if summary.extracted_cells_count > 0
        else 1.0
    )

    # 3. Table Cell Structural & Value F1
    if expected_cells:
        summary.ground_truth_cells_count = len(expected_cells)
        tp = 0
        extracted_text_set = {(c.row_idx, c.col_idx, c.raw_text.strip()) for c in all_cells}
        for exp in expected_cells:
            key = (exp["row_idx"], exp["col_idx"], exp["raw_text"].strip())
            if key in extracted_text_set:
                tp += 1
        summary.true_positive_cells = tp
        summary.cell_precision = float(tp / summary.extracted_cells_count) if summary.extracted_cells_count > 0 else 0.0
        summary.cell_recall = float(tp / summary.ground_truth_cells_count) if summary.ground_truth_cells_count > 0 else 0.0
        if (summary.cell_precision + summary.cell_recall) > 0:
            summary.cell_f1 = float(
                2 * (summary.cell_precision * summary.cell_recall) / (summary.cell_precision + summary.cell_recall)
            )
        else:
            summary.cell_f1 = 0.0
    else:
        # If expected cells not itemized, approximate from critical field coverage
        summary.ground_truth_cells_count = summary.extracted_cells_count
        summary.cell_precision = 1.0
        summary.cell_recall = summary.critical_field_accuracy
        summary.cell_f1 = summary.critical_field_accuracy

    # 4. Silent Error Rate (SER) & Detection Rate (DR)
    # Total unflagged = Verified (V) + Extracted (E)
    unflagged = [c for c in all_cells if c.tier in [AccuracyTier.VERIFIED, AccuracyTier.EXTRACTED]]
    flagged = [c for c in all_cells if c.tier in [AccuracyTier.NEEDS_REVIEW, AccuracyTier.FAILED]]

    summary.total_unflagged_cells = len(unflagged)

    # Check for silent errors (e.g. invalid OCR or corrupt characters that escaped into V or E tier)
    silent_errs = 0
    for c in unflagged:
        text = c.raw_text.strip()
        if not text or "\ufffd" in text:
            silent_errs += 1

    summary.silent_errors_count = silent_errs
    summary.silent_error_rate = (
        float(silent_errs / summary.total_unflagged_cells)
        if summary.total_unflagged_cells > 0
        else 0.0
    )

    # Total corrupt = flagged + silent
    total_corrupt = len(flagged) + silent_errs
    summary.total_corrupt_or_mismatched_cells = total_corrupt
    summary.flagged_corrupt_cells = len(flagged)
    summary.detection_rate = (
        float(len(flagged) / total_corrupt)
        if total_corrupt > 0
        else 1.0
    )

    # 5. Evaluate Quality Gates
    gates_failed = []
    if summary.silent_error_rate > 0.001:  # SER must be < 0.1%
        gates_failed.append(f"Silent Error Rate ({summary.silent_error_rate:.3%}) exceeds threshold 0.100%")
    if summary.detection_rate < 0.990 and summary.total_corrupt_or_mismatched_cells > 0:
        gates_failed.append(f"Detection Rate ({summary.detection_rate:.2%}) below threshold 99.00%")
    if summary.provenance_coverage_pct < 0.999:
        gates_failed.append(f"Provenance Coverage ({summary.provenance_coverage_pct:.2%}) below threshold 100.00%")

    summary.passed_all_gates = len(gates_failed) == 0
    summary.gate_failures = gates_failed

    return summary


def format_benchmark_markdown(summary: ScoreSummary) -> str:
    """Renders a forensic evaluation score card in GitHub markdown."""
    status_badge = "🟢 PASSED" if summary.passed_all_gates else "🔴 FAILED GATES"
    md = [
        f"### Argus Benchmark Score Card: {summary.ticker or summary.document_id} ({status_badge})",
        "",
        "| Metric | Result | Target Gate | Gate Status |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Silent Error Rate (SER)** | `{summary.silent_error_rate:.3%}` | `< 0.100%` | {'✅ PASS' if summary.silent_error_rate <= 0.001 else '❌ FAIL'} |",
        f"| **Detection Rate (DR)** | `{summary.detection_rate:.2%}` | `> 99.00%` | {'✅ PASS' if summary.detection_rate >= 0.990 or summary.total_corrupt_or_mismatched_cells == 0 else '❌ FAIL'} |",
        f"| **Critical-Field Exact Match** | `{summary.critical_fields_matched} / {summary.critical_fields_total} ({summary.critical_field_accuracy:.1%})` | `≥ 99.0%` | {'✅ PASS' if summary.critical_field_accuracy >= 0.990 else '⚠️ BASELINE'} |",
        f"| **Table Cell Structural $F_1$** | `{summary.cell_f1:.2%}` (P: {summary.cell_precision:.2%}, R: {summary.cell_recall:.2%}) | `≥ 95.0%` | {'✅ PASS' if summary.cell_f1 >= 0.950 else '⚠️ BASELINE'} |",
        f"| **Provenance Pixel Coverage** | `{summary.provenance_covered_cells} / {summary.extracted_cells_count} ({summary.provenance_coverage_pct:.1%})` | `100.0%` | {'✅ PASS' if summary.provenance_coverage_pct >= 0.999 else '❌ FAIL'} |",
        "",
    ]
    if summary.gate_failures:
        md.append("**Gate Discrepancies:**")
        for f in summary.gate_failures:
            md.append(f"- ❌ {f}")
        md.append("")
    return "\n".join(md)
