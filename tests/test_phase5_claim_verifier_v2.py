"""
Phase 5 Tests: Deterministic Claim Verifier V2 (Composite-Key Matching & Collision Defense).
"""

from decimal import Decimal
import pytest

from packages.agents.claim_verifier import verify_and_ground_claims
from packages.canonical import (
    AccuracyTier,
    BoundingBox,
    DerivedMetric,
    EvidenceCoordinates,
    ExtractionMetadata,
    Fact,
)


def make_fact(fact_id: str, metric: str, val: Decimal, scale: Decimal = Decimal("1.0")) -> Fact:
    ev = EvidenceCoordinates(
        document_id="doc_v2",
        page_number=1,
        bbox=BoundingBox(page_number=1, x0=10, y0=20, x1=200, y1=50),
        raw_text=str(val),
        render_image_key="renders/doc_v2/p1.png",
    )
    return Fact(
        id=fact_id,
        tenant_id="tenant_v2",
        document_id="doc_v2",
        element_id=f"elem_{fact_id}",
        entity="Apple Inc.",
        metric=metric,
        period="FY2024",
        value=val,
        raw_text=str(val),
        currency="USD",
        scale=scale,
        tier=AccuracyTier.VERIFIED,
        confidence=1.0,
        evidence=ev,
        extraction=ExtractionMetadata(engines_used=["test"], agreement_score=1.0),
    )


def test_claim_verifier_synonym_context_match():
    """Verify that 'Net Sales' prose resolves to a 'total_revenue' fact via the ontology."""
    f_rev = make_fact("f_rev_24", "total_revenue", Decimal("394328000000"))
    allowed_facts = [f_rev]

    draft = "For FY2024, net sales were $394,328,000,000 USD."
    res = verify_and_ground_claims(draft, allowed_facts, [])
    assert res.has_unsupported_claims is False
    assert len(res.valid_claims) == 1
    assert res.valid_claims[0].resolved_id == "f_rev_24"
    assert res.valid_claims[0].matched_metric == "total_revenue"


def test_claim_verifier_semantic_collision_defense():
    """
    CRITICAL AUDIT TEST:
    If LLM hallucinates 'debt was 394328000000' and ONLY revenue equals 394328000000,
    the verifier MUST reject and strip the number (Weakness 1 & 3 fix).
    """
    f_rev = make_fact("f_rev_24", "total_revenue", Decimal("394328000000"))
    allowed_facts = [f_rev]

    # Hallucinated metric context: claiming revenue value is debt
    draft_collision = "For FY2024, total debt stood at $394,328,000,000 USD."
    res = verify_and_ground_claims(draft_collision, allowed_facts, [])

    # The number must be stripped because the context 'total debt' does not match the fact 'total_revenue'
    assert res.has_unsupported_claims is True
    assert "$394,328,000,000" in res.stripped_tokens
    assert "[not stated in the ingested documents]" in res.verified_answer
    assert "$394,328,000,000" not in res.verified_answer


def test_claim_verifier_disambiguates_same_value():
    """
    When two facts share the exact same numeric value, verifier uses
    context to link to the correct fact ID.
    """
    f_rev = make_fact("f_rev", "revenue", Decimal("500000"))
    f_inv = make_fact("f_inv", "inventory", Decimal("500000"))
    allowed_facts = [f_rev, f_inv]

    # Context 1: Inventory
    draft_inv = "Company reported inventory of 500000 USD."
    res_inv = verify_and_ground_claims(draft_inv, allowed_facts, [])
    assert res_inv.has_unsupported_claims is False
    assert res_inv.valid_claims[0].resolved_id == "f_inv"

    # Context 2: Revenue
    draft_rev = "Company reported revenue of 500000 USD."
    res_rev = verify_and_ground_claims(draft_rev, allowed_facts, [])
    assert res_rev.has_unsupported_claims is False
    assert res_rev.valid_claims[0].resolved_id == "f_rev"
