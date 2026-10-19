"""
Argus Benchmark Execution Engine.

Orchestrates ground-truth loading, document ingestion through the multi-engine
pipeline, and scoring against the forensic rubric.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from evals.edgar_downloader import BENCHMARK_COMPANIES, fetch_company_facts
from evals.ground_truth_builder import (
    GroundTruthFiling,
    build_ground_truth_from_facts,
    save_ground_truth_filing,
)
from evals.scoring import ScoreSummary, evaluate_extraction_run, format_benchmark_markdown
from packages.canonical import Fact, Table
from packages.extractors import route_and_extract
from packages.storage.object_store import get_object_store


def prepare_benchmark_ground_truth(
    ticker: str = "AAPL",
    fiscal_year: int = 2024,
) -> GroundTruthFiling:
    """
    Fetches real SEC EDGAR facts and compiles standard GroundTruthFiling fixture.
    """
    company_info = BENCHMARK_COMPANIES.get(ticker, {"cik": "0000320193", "name": ticker})
    facts_json = fetch_company_facts(company_info["cik"])
    filing = build_ground_truth_from_facts(facts_json, ticker=ticker, fiscal_year=fiscal_year)
    save_ground_truth_filing(filing)
    return filing


def run_benchmark_on_document(
    doc_filename: str,
    doc_bytes: bytes,
    ground_truth: GroundTruthFiling,
    doc_id: str = "doc_benchmark",
) -> ScoreSummary:
    """
    Ingests a document through the full Argus router & extractors,
    then evaluates extracted facts against the certified ground truth.
    """
    pages, text_elements, tables, figures = route_and_extract(doc_filename, doc_bytes, doc_id)

    # Convert cells to canonical facts for critical field evaluation
    from packages.normalize import canonicalize_financial_number
    from packages.canonical import EvidenceCoordinates, ExtractionMetadata, AccuracyTier

    extracted_facts: List[Fact] = []
    for t in tables:
        for c in t.cells:
            res = canonicalize_financial_number(c.raw_text)
            if not res.is_null and res.normalized_value is not None:
                fact = Fact(
                    id=f"fact_{c.id}",
                    tenant_id="tenant_benchmark",
                    document_id=doc_id,
                    element_id=c.id,
                    entity=ground_truth.company_name,
                    metric=f"metric_r{c.row_idx}_c{c.col_idx}",
                    period=f"FY{ground_truth.fiscal_year}",
                    value=res.normalized_value,
                    raw_text=c.raw_text,
                    currency=res.currency or "USD",
                    scale=res.scale,
                    tier=c.tier,
                    confidence=1.0,
                    evidence=c.evidence,
                    extraction=ExtractionMetadata(engines_used=["benchmark_pipeline"], agreement_score=1.0),
                )
                extracted_facts.append(fact)

    gt_dict = ground_truth.to_dict()
    summary = evaluate_extraction_run(
        extracted_facts=extracted_facts,
        extracted_tables=tables,
        ground_truth_fields=gt_dict["critical_fields"],
        document_id=doc_id,
        ticker=ground_truth.ticker,
        fiscal_year=ground_truth.fiscal_year,
    )
    return summary
