"""
Deterministic Claim Verifier V2 (The Hallucination Gate).

Scans every numeric token in LLM-generated prose, canonicalizes it through
the 32-case financial number pipeline, extracts local context windows, and
verifies composite tuple (metric, value, entity) against allowed facts
and calculations.

Ungrounded numbers or semantic collisions (e.g., claiming a revenue number is debt)
are stripped and replaced with explicit disclosure.
"""

from decimal import Decimal, InvalidOperation
import re
from typing import Dict, List, Optional, Set, Tuple
from pydantic import BaseModel
from packages.calc.ontology import CANONICAL_SYNONYM_MAP, resolve_canonical_metric
from packages.canonical import AccuracyTier, DerivedMetric, Fact
from packages.normalize import canonicalize_financial_number


class VerifiedClaim(BaseModel):
    token: str
    resolved_id: str
    source_type: str  # 'fact' or 'calc'
    tier: AccuracyTier
    citation: str
    matched_metric: Optional[str] = None


class ClaimVerificationResult(BaseModel):
    verified_answer: str
    valid_claims: List[VerifiedClaim]
    stripped_tokens: List[str]
    has_unsupported_claims: bool


# Matches currency-prefixed, signed, comma/dot-separated numbers with optional scale suffixes
# and percentage signs. Captures the full token for canonicalization.
NUMERIC_PATTERN = re.compile(
    r"[\(\[]?"                             # Optional opening paren/bracket
    r"[\$€£₹]?"                            # Optional currency symbol
    r"\s*-?"                               # Optional leading minus
    r"(?:\d{1,3}(?:[,\.\s]\d{3})+|\d+)"    # Grouped or plain integer digits
    r"(?:[.,]\d+)?"                        # Optional decimal fraction
    r"\s*(?:%|[a-zA-Z]+)?"                 # Optional scale suffix or %
    r"[\)\]]?"                             # Optional closing paren/bracket
)


def canonicalize_claim_token(raw_token: str) -> Optional[Decimal]:
    """
    Canonicalize an LLM-generated numeric token through the SAME
    32-case financial number pipeline used for document extraction.
    """
    result = canonicalize_financial_number(raw_token)
    if result.is_null or result.normalized_value is None:
        return None
    return result.normalized_value


def _detect_context_metric(context_str: str) -> Optional[str]:
    """
    Scans the local context window around a number to identify the financial metric
    being discussed, matching longest synonym phrases first.
    """
    c_lower = context_str.lower()
    candidates = []
    for canonical_key, aliases in CANONICAL_SYNONYM_MAP.items():
        for alias in aliases:
            # Word boundary matching
            if re.search(r"\b" + re.escape(alias) + r"\b", c_lower):
                candidates.append((len(alias), canonical_key))
    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]
    return None


def _matches_calc(canonical_value: Decimal, calc: DerivedMetric) -> bool:
    """Check if canonical value matches derived metric (accounting for % representation)."""
    val = calc.calculated_value
    if canonical_value == val:
        return True
    # If calc is 0.25 and canonical value is 25 (from 25% or 25)
    try:
        if canonical_value == (val * Decimal("100")):
            return True
        if (canonical_value * Decimal("100")) == val:
            return True
    except (InvalidOperation, OverflowError):
        pass
    return False


def _matches_fact(canonical_value: Decimal, fact: Fact) -> bool:
    """Check if canonical value matches fact (exact canonical or unscaled display)."""
    if canonical_value == fact.value:
        return True
    # If fact has scale (e.g. in thousands) and LLM wrote unscaled display number
    if fact.scale > Decimal("1.0"):
        try:
            if canonical_value == (fact.value / fact.scale):
                return True
        except (InvalidOperation, ZeroDivisionError):
            pass
    # Cleaned raw text comparison
    clean_raw = re.sub(r"[^\d.\-]", "", fact.raw_text.replace("(", "-").replace(")", ""))
    if clean_raw:
        try:
            if canonical_value == Decimal(clean_raw):
                return True
        except InvalidOperation:
            pass
    return False


def is_temporal_token(word: str) -> bool:
    """Detects date/period tokens (e.g. FY2024, Q3, 2024) that are not financial quantities."""
    clean = word.strip(".,;:()[]")
    if re.match(r"^FY\d{2,4}$", clean, re.IGNORECASE):
        return True
    if re.match(r"^Q[1-4](?:FY)?\d{0,4}$", clean, re.IGNORECASE):
        return True
    if re.match(r"^(?:19|20)\d{2}$", clean) and not any(c in word for c in "$€£₹") and not re.search(r"[a-zA-Z]", clean):
        return True
    return False


def verify_and_ground_claims(
    draft_answer: str,
    allowed_facts: List[Fact],
    allowed_calcs: List[DerivedMetric],
) -> ClaimVerificationResult:
    """
    Deterministic Claim Verifier V2 (The Hallucination Gate).

    Scans every numeric token in draft_answer:
    1. Canonicalizes it through the 32-case financial number pipeline.
    2. Identifies local metric context from surrounding words.
    3. Reconciles composite key (metric, value) against allowed facts & calcs.
       Rejects collisions where the value matches a different metric.
    4. Strips ungrounded or mismatched numbers with explicit disclosure.
    """
    valid_claims: List[VerifiedClaim] = []
    stripped_tokens: List[str] = []

    output_words = []
    tokens = draft_answer.split()

    for idx, word in enumerate(tokens):
        # Ignore temporal year / period references
        if is_temporal_token(word):
            output_words.append(word)
            continue

        match = NUMERIC_PATTERN.search(word)
        if not match:
            output_words.append(word)
            continue

        raw_match = match.group(0).strip()
        if not any(c.isdigit() for c in raw_match):
            output_words.append(word)
            continue

        # Canonicalize through the 32-case pipeline
        canonical_value = canonicalize_claim_token(raw_match)
        if canonical_value is None:
            output_words.append(word)
            continue

        # Extract surrounding context window (+/- 6 words)
        ctx_start = max(0, idx - 6)
        ctx_end = min(len(tokens), idx + 7)
        context_str = " ".join(tokens[ctx_start:ctx_end])
        detected_metric = _detect_context_metric(context_str)

        # 1. Check in allowed calcs first
        matched_calc: Optional[DerivedMetric] = None
        candidate_calcs = [c for c in allowed_calcs if _matches_calc(canonical_value, c)]
        if candidate_calcs:
            if detected_metric:
                matching_calcs = [
                    c for c in candidate_calcs
                    if detected_metric in c.formula_id or detected_metric in c.formula_name.lower()
                ]
                matched_calc = matching_calcs[0] if matching_calcs else candidate_calcs[0]
            else:
                matched_calc = candidate_calcs[0]

        # 2. Check in allowed facts with composite metric verification
        matched_fact: Optional[Fact] = None
        if not matched_calc:
            candidate_facts = [f for f in allowed_facts if _matches_fact(canonical_value, f)]
            if candidate_facts:
                if detected_metric:
                    # Look for candidate fact whose canonical metric matches context
                    exact_matches = [
                        f for f in candidate_facts
                        if resolve_canonical_metric(f.metric) == detected_metric
                    ]
                    if exact_matches:
                        matched_fact = exact_matches[0]
                    else:
                        # Value collision: value matches an unrelated fact, but context says another metric!
                        matched_fact = None
                else:
                    # No metric mentioned in context: allow candidate fact
                    matched_fact = candidate_facts[0]

        if matched_calc:
            claim = VerifiedClaim(
                token=raw_match,
                resolved_id=matched_calc.id,
                source_type="calc",
                tier=matched_calc.tier,
                citation=f"[{matched_calc.tier.value}: {matched_calc.formula_name}]",
                matched_metric=matched_calc.formula_id,
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
                matched_metric=matched_fact.metric,
            )
            valid_claims.append(claim)
            grounded_word = word.replace(raw_match, f"{raw_match} {citation}")
            output_words.append(grounded_word)

        else:
            # UNGROUNDED / MISMATCHED NUMBER — strip it
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
