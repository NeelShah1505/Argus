from typing import List
from packages.canonical import AccuracyTier, ExtractionMetadata, ValidationResult


def determine_cell_tier(
    extraction: ExtractionMetadata,
    validations: List[ValidationResult],
    has_valid_evidence: bool,
    is_chart_measured: bool = False,
) -> AccuracyTier:
    """
    Enforces the Evidence Contract tier assignment:
    - Tier V (Verified): >=2 engines agree (or adjudicated) + all arithmetic checks passed + valid evidence
    - Tier E (Extracted): Single engine confident extraction with no check failures
    - Tier M (Estimated): Chart measured
    - Tier R (Needs Review): Any failed check, unresolved disagreement, or low confidence
    - Tier F (Failed): Extraction failure
    """
    if not has_valid_evidence:
        return AccuracyTier.NEEDS_REVIEW

    # 1. Any failed validation locks the tier to Needs Review
    if any(not v.passed for v in validations):
        return AccuracyTier.NEEDS_REVIEW

    if is_chart_measured:
        return AccuracyTier.ESTIMATED

    # 2. Check extraction consensus
    has_dual_engines = len(extraction.engines_used) >= 2 or extraction.vision_adjudicated
    all_validations_passed = len(validations) > 0 and all(v.passed for v in validations)

    if has_dual_engines and all_validations_passed:
        return AccuracyTier.VERIFIED
    elif has_dual_engines or extraction.agreement_score >= 0.90:
        return AccuracyTier.EXTRACTED
    else:
        return AccuracyTier.NEEDS_REVIEW
