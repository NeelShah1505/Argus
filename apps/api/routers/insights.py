from decimal import Decimal
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from packages.canonical import AccuracyTier, Fact
from packages.storage.repository import get_document_repo
from packages.validate import check_yoy_outlier

router = APIRouter(prefix="/api/v1", tags=["insights-and-scenarios"])


class ScenarioDriverRequest(BaseModel):
    base_revenue: Decimal
    growth_rate_pct: Decimal  # e.g. 8.5 for 8.5%
    target_gross_margin_pct: Decimal  # e.g. 45.0 for 45%
    projection_years: int = 3
    tenant_id: str = "tenant_default"


class ScenarioYearProjection(BaseModel):
    year_index: int
    projected_revenue: Decimal
    projected_gross_profit: Decimal
    tier: AccuracyTier = AccuracyTier.ESTIMATED


class ScenarioResponse(BaseModel):
    label: str
    is_statistical_forecast: bool
    projections: List[ScenarioYearProjection]
    assumptions_ledger: Dict[str, Any]


@router.post("/scenarios", response_model=ScenarioResponse)
async def compute_scenario(payload: ScenarioDriverRequest):
    """
    Computes deterministic driver-based scenario model.
    Hard rule: Labeled 'Scenario Model — Not a Statistical Forecast'.
    """
    projections: List[ScenarioYearProjection] = []
    curr_rev = payload.base_revenue
    growth_factor = Decimal("1.0") + (payload.growth_rate_pct / Decimal("100.0"))
    margin_factor = payload.target_gross_margin_pct / Decimal("100.0")

    for y in range(1, payload.projection_years + 1):
        curr_rev = (curr_rev * growth_factor).quantize(Decimal("1.00"))
        proj_gp = (curr_rev * margin_factor).quantize(Decimal("1.00"))
        projections.append(
            ScenarioYearProjection(
                year_index=y,
                projected_revenue=curr_rev,
                projected_gross_profit=proj_gp,
                tier=AccuracyTier.ESTIMATED,
            )
        )

    return ScenarioResponse(
        label="Scenario Model — Not a Statistical Forecast",
        is_statistical_forecast=False,
        projections=projections,
        assumptions_ledger={
            "base_revenue": str(payload.base_revenue),
            "annual_growth_rate": f"{payload.growth_rate_pct}%",
            "gross_margin_target": f"{payload.target_gross_margin_pct}%",
            "model_type": "Deterministic Driver Simulation",
            "disclaimer": "Projections are derived from user-defined operational drivers. This is not a statistical time-series forecast.",
        },
    )


@router.get("/anomalies")
async def list_anomalies(document_id: Optional[str] = None):
    repo = get_document_repo()
    anomalies: List[Dict[str, Any]] = []

    facts = repo.get_facts(doc_id=document_id)
    # Check for YoY outliers
    rev_facts = [f for f in facts if "revenue" in f.metric.lower()]
    if len(rev_facts) >= 2:
        rev_sorted = sorted(rev_facts, key=lambda f: f.period)
        for i in range(len(rev_sorted) - 1):
            outlier = check_yoy_outlier(
                metric_name="Revenue",
                val_prev=rev_sorted[i].value,
                val_curr=rev_sorted[i + 1].value,
                element_id=rev_sorted[i + 1].element_id,
            )
            if outlier:
                anomalies.append(outlier.model_dump())

    # Check for unapproved cells
    if document_id:
        tables = repo.get_tables(document_id)
        for t in tables:
            for c in t.cells:
                if c.tier == AccuracyTier.NEEDS_REVIEW:
                    anomalies.append(
                        {
                            "rule_id": "ANOM-02",
                            "rule_name": "Needs Review Discrepancy",
                            "severity": "High",
                            "affected_element_ids": [c.id],
                            "description": f"Cell '{c.raw_text}' flagged for review due to validation or parser disagreement.",
                            "details": c.extraction.raw_candidates,
                        }
                    )
    return anomalies


@router.get("/audit-pack/{document_id}")
async def get_audit_pack(document_id: str):
    """
    Exports a forensic Audit Pack dossier linking every extracted value
    to original pixel coordinates, validations, and reviewer signatures.
    """
    repo = get_document_repo()
    doc = repo.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    tables = repo.get_tables(document_id)
    audit_events = repo.get_audit_events(document_id)
    facts = repo.get_facts(doc_id=document_id)

    pack_data = {
        "audit_pack_id": f"ap_{doc.id}_{doc.version}",
        "document": {
            "id": doc.id,
            "filename": doc.filename,
            "sha256": doc.file_hash,
            "version": doc.version,
            "status": doc.status.value,
        },
        "verified_facts_count": len([f for f in facts if f.tier == AccuracyTier.VERIFIED]),
        "facts": [f.model_dump() for f in facts],
        "audit_trail": [a.model_dump() for a in audit_events],
        "tables_summary": [
            {
                "table_id": t.id,
                "title": t.title,
                "rows": t.rows_count,
                "cols": t.cols_count,
                "tier": t.tier.value,
            }
            for t in tables
        ],
        "certificate": {
            "attestation": "Argus Evidence Contract Forensic Audit Pack",
            "standard": "Dual-Engine Consensus & Pixel-Level Provenance",
            "verified": True,
        },
    }
    return pack_data
