from decimal import Decimal
from typing import List, Optional
from packages.canonical import ValidationResult


def validate_subtotal_footing(
    reported_total: Decimal,
    line_items: List[Decimal],
    tolerance: Decimal = Decimal("0.01"),
    context_name: str = "Column Subtotal",
) -> ValidationResult:
    """
    Verifies that the sum of line items equals the reported total within tolerance.
    Does NOT mutate any values.
    """
    computed_sum = sum(line_items, Decimal("0.0"))
    delta = abs(reported_total - computed_sum)

    passed = delta <= tolerance
    msg = (
        f"{context_name} footing passed: sum({computed_sum}) == reported({reported_total})"
        if passed
        else f"{context_name} footing mismatch: computed sum({computed_sum}) != reported({reported_total}), delta={delta}"
    )

    return ValidationResult(
        rule_id="L2_SUBTOTAL_FOOTING",
        rule_name=f"{context_name} Footing",
        passed=passed,
        expected_value=reported_total,
        actual_value=computed_sum,
        discrepancy=delta if not passed else None,
        message=msg,
    )
