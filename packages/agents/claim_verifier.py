import re
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel
from packages.canonical import AccuracyTier, DerivedMetric, Fact


class VerifiedClaim(BaseModel):
    token: str
    resolved_id: str
    source_type: str  # 'fact' or 'calc'
    tier: AccuracyTier
    citation: str


class ClaimVerificationResult(BaseModel):
    verified_answer: str
    valid_claims: List[VerifiedClaim]
    stripped_tokens: List[str]
    has_unsupported_claims: bool


NUMERIC_PATTERN = re.compile(r"(\$|€|£|₹)?\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)(%|\b[kmbncrKMBnCR]+)?\b")


def parse_numeric_token(token_str: str) -> Optional[Decimal]:
    """Extract clean numerical value from token string."""
    clean = re.sub(r"[^\d.]", "", token_str)
    try:
        return Decimal(clean)
    except (InvalidOperation, ValueError):
        return None


def verify_and_ground_claims(
    draft_answer: str,
    allowed_facts: List[Fact],
    allowed_calcs: List[DerivedMetric],
) -> ClaimVerificationResult:
    """
    Code-level Claim Verifier (The Hallucination Gate).
    Scans every numeric token in draft_answer:
    - If it resolves to an allowed fact or calculation, appends citation and tier badge.
    - If it DOES NOT resolve, strips the number and replaces it with '[not stated in the ingested documents]'.
    """
    valid_claims: List[VerifiedClaim] = []
    stripped_tokens: List[str] = []

    # Build reference lookup tables
    fact_val_map: Dict[str, Fact] = {}
    for f in allowed_facts:
        fact_val_map[str(f.value)] = f
        # Also store rounded / raw versions
        fact_val_map[str(f.raw_text).replace(",", "").replace("$", "").replace("(", "").replace(")", "")] = f
        if f.scale > Decimal("1.0"):
            unscaled = f.value / f.scale
            fact_val_map[str(unscaled)] = f

    calc_val_map: Dict[str, DerivedMetric] = {}
    for c in allowed_calcs:
        calc_val_map[str(c.calculated_value)] = c
        # percentage string representation, e.g. 0.25 -> 25
        pct_val = (c.calculated_value * Decimal("100")).quantize(Decimal("0.01"))
        calc_val_map[str(pct_val)] = c
        calc_val_map[f"{pct_val:.1f}"] = c
        calc_val_map[f"{pct_val:.2f}"] = c

    output_words = []
    tokens = draft_answer.split()

    for word in tokens:
        match = NUMERIC_PATTERN.search(word)
        if not match:
            output_words.append(word)
            continue

        raw_match = match.group(0)
        parsed_num = parse_numeric_token(raw_match)
        if parsed_num is None:
            output_words.append(word)
            continue

        str_num = str(parsed_num)

        # Check in allowed calcs
        matched_calc: Optional[DerivedMetric] = None
        for k, c in calc_val_map.items():
            if str_num == k or (parsed_num and parse_numeric_token(k) == parsed_num):
                matched_calc = c
                break

        # Check in allowed facts
        matched_fact: Optional[Fact] = None
        if not matched_calc:
            for k, f in fact_val_map.items():
                if str_num == k or (parsed_num and parse_numeric_token(k) == parsed_num):
                    matched_fact = f
                    break

        if matched_calc:
            claim = VerifiedClaim(
                token=raw_match,
                resolved_id=matched_calc.id,
                source_type="calc",
                tier=matched_calc.tier,
                citation=f"[{matched_calc.tier.value}: {matched_calc.formula_name}]",
            )
            valid_claims.append(claim)
            grounded_word = word.replace(raw_match, f"{raw_match} [{matched_calc.tier.value}: {matched_calc.formula_id}]")
            output_words.append(grounded_word)

        elif matched_fact:
            ev = matched_fact.evidence
            citation = f"[{matched_fact.tier.value}: p.{ev.page_number} r{ev.bbox.y0:.0f}]"
            claim = VerifiedClaim(
                token=raw_match,
                resolved_id=matched_fact.id,
                source_type="fact",
                tier=matched_fact.tier,
                citation=citation,
            )
            valid_claims.append(claim)
            grounded_word = word.replace(raw_match, f"{raw_match} {citation}")
            output_words.append(grounded_word)

        else:
            # UNGROUNDED / HALLUCINATED NUMBER! Strip it!
            stripped_tokens.append(raw_match)
            censored_word = word.replace(raw_match, "[not stated in the ingested documents]")
            output_words.append(censored_word)

    verified_answer = " ".join(output_words)

    return ClaimVerificationResult(
        verified_answer=verified_answer,
        valid_claims=valid_claims,
        stripped_tokens=stripped_tokens,
        has_unsupported_claims=len(stripped_tokens) > 0,
    )
