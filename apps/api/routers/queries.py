from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from packages.agents import AnalystResponse, get_orchestrator

router = APIRouter(prefix="/api/v1/queries", tags=["queries"])


class AnalystQueryRequest(BaseModel):
    query: str
    tenant_id: str = "tenant_default"
    document_id: Optional[str] = None


@router.post("", response_model=AnalystResponse)
async def submit_analyst_query(payload: AnalystQueryRequest):
    """
    Submits natural language question to Argus Analyst Orchestrator.
    Guarantees evidence grounding and post-generation numeric claim verification.
    """
    orchestrator = get_orchestrator()
    return orchestrator.handle_query(
        query=payload.query,
        tenant_id=payload.tenant_id,
        doc_id=payload.document_id,
    )
