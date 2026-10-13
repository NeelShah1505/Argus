from decimal import Decimal
from typing import Optional
from packages.canonical import ValidationResult


def validate_balance_sheet_identity(
    total_assets: Decimal,
    total_liabilities: Decimal,
    stockholders_equity: Decimal,
    tolerance: Decimal = Decimal("0.01"),
) -> ValidationResult:
    """
    Verifies the fundamental balance sheet equation:
    Assets == Liabilities + Stockholders' Equity
    """
    liab_plus_equity = total_liabilities + stockholders_equity
    delta = abs(total_assets - liab_plus_equity)
    passed = delta <= tolerance

    msg = (
        f"Balance Sheet balanced: Assets({total_assets}) == Liab+Equity({liab_plus_equity})"
        if passed
        else f"Balance Sheet imbalanced: Assets({total_assets}) != Liab+Equity({liab_plus_equity}), discrepancy={delta}"
    )

    return ValidationResult(
        rule_id="L2_BALANCE_SHEET_IDENTITY",
        rule_name="Balance Sheet Fundamental Identity",
        passed=passed,
        expected_value=total_assets,
        actual_value=liab_plus_equity,
        discrepancy=delta if not passed else None,
        message=msg,
    )


def validate_sign_sanity(
    metric_name: str,
    value: Decimal,
) -> ValidationResult:
    """
    Flags impossible signs (e.g. negative revenue or negative cash).
    """
    lower_metric = metric_name.lower()
    passed = True
    msg = f"{metric_name} sign is valid."

    if "revenue" in lower_metric or "sales" in lower_metric:
        if value < Decimal("0"):
            passed = False
            msg = f"Sign anomaly: {metric_name} is negative ({value})."

    elif "cash" in lower_metric and "flow" not in lower_metric and "change" not in lower_metric:
        if value < Decimal("0"):
            passed = False
            msg = f"Sign anomaly: {metric_name} balance cannot be negative ({value})."

    return ValidationResult(
        rule_id="L2_SIGN_SANITY",
        rule_name="Sign Plausibility Check",
        passed=passed,
        actual_value=value,
        message=msg,
    )
