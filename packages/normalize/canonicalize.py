import re
from decimal import Decimal, InvalidOperation
from typing import Optional
from pydantic import BaseModel


class CanonicalizedNumber(BaseModel):
    raw_text: str
    normalized_value: Optional[Decimal] = None
    currency: Optional[str] = None
    scale: Decimal = Decimal("1.0")
    is_null: bool = False
    is_negative: bool = False
    applied_rule: str = "raw"


NULL_MARKERS = {
    "—", "–", "-", "nil", "n/a", "na", "n/m", "nm", "none", "null", "", " ", "—", "—"
}

CURRENCY_SYMBOLS = {
    "$": "USD",
    "USD": "USD",
    "€": "EUR",
    "EUR": "EUR",
    "£": "GBP",
    "GBP": "GBP",
    "₹": "INR",
    "INR": "INR",
    "¥": "JPY",
    "JPY": "JPY",
    "CHF": "CHF",
}

SCALE_MULTIPLIERS = {
    "k": Decimal("1000"),
    "thousand": Decimal("1000"),
    "thousands": Decimal("1000"),
    "m": Decimal("1000000"),
    "mn": Decimal("1000000"),
    "million": Decimal("1000000"),
    "millions": Decimal("1000000"),
    "b": Decimal("1000000000"),
    "bn": Decimal("1000000000"),
    "billion": Decimal("1000000000"),
    "billions": Decimal("1000000000"),
    "cr": Decimal("10000000"),
    "crore": Decimal("10000000"),
    "crores": Decimal("10000000"),
    "lakh": Decimal("100000"),
    "lakhs": Decimal("100000"),
}


def canonicalize_financial_number(raw_text: str, default_currency: str = "USD") -> CanonicalizedNumber:
    """
    Deterministically normalizes raw financial strings into Decimal objects.
    Guarantees that null markers are preserved as None (never coerced to 0).
    """
    text = raw_text.strip()

    # 1. Null check
    if text.lower() in NULL_MARKERS:
        return CanonicalizedNumber(
            raw_text=raw_text,
            normalized_value=None,
            is_null=True,
            applied_rule="null_marker",
        )

    # 2. Currency extraction
    detected_currency = default_currency
    for symbol, curr_code in CURRENCY_SYMBOLS.items():
        if symbol in text:
            detected_currency = curr_code
            text = text.replace(symbol, "")
            break

    text = text.strip()

    # 3. Sign detection first (Parentheses negation or trailing minus)
    is_negative = False
    rule = "standard"

    if text.startswith("(") and text.endswith(")"):
        is_negative = True
        text = text[1:-1].strip()
        rule = "parentheses_negative"
    elif text.endswith("-"):
        is_negative = True
        text = text[:-1].strip()
        rule = "trailing_negative"
    elif text.startswith("-"):
        is_negative = True
        text = text[1:].strip()
        rule = "leading_negative"

    # 4. Scale suffix extraction (e.g. 12.3m, 450k, 1.2bn, 50cr, 10lakh)
    detected_scale = Decimal("1.0")
    scale_match = re.search(r"([a-zA-Z]+)$", text)
    if scale_match:
        suffix = scale_match.group(1).lower()
        if suffix in SCALE_MULTIPLIERS:
            detected_scale = SCALE_MULTIPLIERS[suffix]
            text = text[: -len(suffix)].strip()

    # Remove non-numeric spacing (e.g. '1 234 567')
    text = re.sub(r"\s+", "", text)

    # 5. European format vs Indian vs Standard US
    # Check European: 1.245,50 (period is thousand sep, comma is decimal)
    if "." in text and "," in text:
        dot_idx = text.rfind(".")
        comma_idx = text.rfind(",")
        if comma_idx > dot_idx:
            # European: '1.245,50' -> replace '.' with '', replace ',' with '.'
            text = text.replace(".", "").replace(",", ".")
            rule = f"{rule}_european_decimal"
        else:
            # Standard US: '1,245.50' -> remove ','
            text = text.replace(",", "")
            rule = f"{rule}_us_decimal"
    elif "," in text and "." not in text:
        # Check if comma is decimal (e.g. '1245,50') or thousand separator ('1,245')
        parts = text.split(",")
        if len(parts) == 2 and len(parts[1]) in [1, 2]:
            # Trailing 1 or 2 digits after comma -> continental decimal '1245,50'
            text = text.replace(",", ".")
            rule = f"{rule}_comma_decimal"
        else:
            # Thousands separator (US or Indian)
            text = text.replace(",", "")
            rule = f"{rule}_comma_thousands"

    # Clean any leftover non-digits except '.'
    clean_text = re.sub(r"[^\d.]", "", text)
    if not clean_text:
        return CanonicalizedNumber(
            raw_text=raw_text,
            normalized_value=None,
            is_null=True,
            applied_rule="unparseable_null",
        )

    try:
        dec_val = Decimal(clean_text)
        if is_negative:
            dec_val = -dec_val

        # Full unscaled normalized value
        full_val = dec_val * detected_scale

        return CanonicalizedNumber(
            raw_text=raw_text,
            normalized_value=full_val,
            currency=detected_currency,
            scale=detected_scale,
            is_null=False,
            is_negative=is_negative,
            applied_rule=rule,
        )
    except InvalidOperation:
        return CanonicalizedNumber(
            raw_text=raw_text,
            normalized_value=None,
            is_null=True,
            applied_rule="invalid_decimal",
        )
