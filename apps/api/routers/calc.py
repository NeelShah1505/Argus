from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from packages.calc import CalculationError, get_formula_registry, get_lineage_graph
from packages.canonical import DerivedMetric, Fact
from packages.storage.repository import get_document_repo

router = APIRouter(prefix="/api/v1", tags=["calculations"])


class RunCalculationRequest(BaseModel):
    formula_id: str
    fact_ids: List[str]
    tenant_id: str = "tenant_default"


@router.post("/calculations/run", response_model=DerivedMetric)
async def run_calculation(payload: RunCalculationRequest):
    repo = get_document_repo()
    all_facts = repo.get_facts()
    fact_map = {f.id: f for f in all_facts}

    input_facts: List[Fact] = []
    for fid in payload.fact_ids:
        if fid not in fact_map:
            raise HTTPException(status_code=404, detail=f"Input fact '{fid}' not found in fact store.")
        input_facts.append(fact_map[fid])

    registry = get_formula_registry()
    lineage = get_lineage_graph()

    try:
        derived = registry.execute_calculation(
            formula_id=payload.formula_id,
            input_facts=input_facts,
            tenant_id=payload.tenant_id,
        )
        lineage.register_derived_metric(derived)
        return derived
    except CalculationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/lineage/{metric_id}")
async def get_metric_lineage(metric_id: str):
    lineage = get_lineage_graph()
    dag = lineage.get_lineage(metric_id)
    if not dag:
        raise HTTPException(status_code=404, detail=f"Lineage for metric '{metric_id}' not found.")
    return dag


@router.get("/facts", response_model=List[Fact])
async def list_facts(
    entity: Optional[str] = None,
    metric: Optional[str] = None,
    period: Optional[str] = None,
    document_id: Optional[str] = None,
):
    repo = get_document_repo()
    return repo.get_facts(doc_id=document_id, entity=entity, metric=metric, period=period)
