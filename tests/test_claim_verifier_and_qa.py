from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from packages.agents import (
    AnalystOrchestrator,
    get_orchestrator,
    verify_and_ground_claims,
)
from packages.canonical import (
    AccuracyTier,
    BoundingBox,
    DerivedMetric,
    EvidenceCoordinates,
    ExtractionMetadata,
    Fact,
)
from packages.storage.repository import get_document_repo

client = TestClient(app)


def make_fact(fact_id: str, metric: str, val: Decimal) -> Fact:
    return Fact(
        id=fact_id,
        tenant_id="tenant_qa",
        document_id="doc_qa",
        element_id=f"elem_{fact_id}",
        entity="Stark Industries",
        metric=metric,
        period="FY2024",
        value=val,
        raw_text=str(val),
        currency="USD",
        scale=Decimal("1.0"),
        tier=AccuracyTier.VERIFIED,
        confidence=1.0,
        evidence=EvidenceCoordinates(
            document_id="doc_qa",
            page_number=1,
            bbox=BoundingBox(page_number=1, x0=10, y0=20, x1=200, y1=50),
            raw_text=str(val),
            render_image_key="renders/doc_qa/p1.png",
        ),
        extraction=ExtractionMetadata(engines_used=["pdfplumber"], agreement_score=1.0),
    )


def test_claim_verifier_grounded_vs_hallucinated():
    fact_rev = make_fact("fact_rev_24", "revenue", Decimal("125000"))
    allowed_facts = [fact_rev]
    allowed_calcs = []

    # 1. Fully grounded draft
    draft_grounded = "Reported revenue was 125000 USD."
    result_grounded = verify_and_ground_claims(draft_grounded, allowed_facts, allowed_calcs)
    assert result_grounded.has_unsupported_claims is False
    assert len(result_grounded.valid_claims) == 1
    assert "[V:" in result_grounded.verified_answer

    # 2. Injected unsupported hallucination: 999999
    draft_injected = "Reported revenue was 125000 USD and secret dividend was 999999 USD."
    result_injected = verify_and_ground_claims(draft_injected, allowed_facts, allowed_calcs)
    assert result_injected.has_unsupported_claims is True
    assert "999999" in result_injected.stripped_tokens
    assert "[not stated in the ingested documents]" in result_injected.verified_answer
    assert "999999" not in result_injected.verified_answer


def test_claim_verifier_with_derived_calc():
    fact_rev = make_fact("fact_rev_24", "revenue", Decimal("200000"))
    calc_growth = DerivedMetric(
        id="metric_growth",
        tenant_id="tenant_qa",
        formula_id="revenue_growth",
        formula_name="Revenue Growth",
        input_fact_ids=["fact_rev_24"],
        calculated_value=Decimal("0.2500"),
        tier=AccuracyTier.VERIFIED,
        lineage_dag={"formula": "growth", "result": "0.25"},
    )

    draft = "Revenue was 200000 and growth was 25.00%."
    result = verify_and_ground_claims(draft, [fact_rev], [calc_growth])
    assert result.has_unsupported_claims is False
    assert len(result.valid_claims) == 2


def test_orchestrator_explicit_abstention():
    # Empty doc with no facts
    orch = get_orchestrator()
    resp = orch.handle_query("What was operating cash flow?", tenant_id="tenant_empty", doc_id="doc_nonexistent")
    assert "The ingested documents do not state" in resp.answer
    assert len(resp.missing_evidence) >= 1


def test_queries_api_endpoint():
    repo = get_document_repo()
    f1 = make_fact("f_api_rev_24", "revenue", Decimal("350000"))
    repo.add_fact(f1)

    payload = {
        "query": "What was Stark Industries revenue?",
        "tenant_id": "tenant_qa",
        "document_id": "doc_qa",
    }
    res = client.post("/api/v1/queries", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert "claims" in data
    assert "Stark Industries" in data["answer"]


def test_claim_verifier_canonical_pipeline_cases():
    """Verify that scale multipliers (12.5M), parentheses negatives (500), and currency are canonicalized."""
    f_millions = make_fact("f_m", "revenue", Decimal("12500000"))
    f_loss = make_fact("f_l", "net_loss", Decimal("-500"))
    allowed = [f_millions, f_loss]

    draft = "Revenue stood at $12.5M while net loss was (500) USD."
    res = verify_and_ground_claims(draft, allowed, [])
    assert res.has_unsupported_claims is False
    assert len(res.valid_claims) == 2
    assert len(res.stripped_tokens) == 0

    # Unmatched hallucinated scale
    draft_fake = "Revenue stood at $12.5M but EBITDA was $99.9B."
    res_fake = verify_and_ground_claims(draft_fake, allowed, [])
    assert res_fake.has_unsupported_claims is True
    assert "$99.9B" in res_fake.stripped_tokens
    assert "[not stated in the ingested documents]" in res_fake.verified_answer

