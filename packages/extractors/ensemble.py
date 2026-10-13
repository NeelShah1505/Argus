from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from packages.canonical import (
    AccuracyTier,
    BoundingBox,
    EvidenceCoordinates,
    ExtractionMetadata,
    Table,
    TableCell,
)
from packages.llm import get_llm_provider
from packages.normalize import canonicalize_financial_number, detect_ocr_confusion


def adjudicate_table_ensemble(
    table_id: str,
    doc_id: str,
    page_number: int,
    grid_a: List[List[str]],
    grid_b: List[List[str]],
    crop_bytes_map: Optional[Dict[Tuple[int, int], bytes]] = None,
    llm_provider: Optional[get_llm_provider.__annotations__.get("return")] = None,
) -> Table:
    """
    Executes cell-level voting between Engine A and Engine B.
    Disagreements trigger vision-crop adjudication or escalate to Tier R.
    """
    llm = llm_provider or get_llm_provider()
    crop_map = crop_bytes_map or {}

    max_rows = max(len(grid_a), len(grid_b))
    max_cols = max(
        max((len(r) for r in grid_a), default=0),
        max((len(r) for r in grid_b), default=0),
    )

    cells: List[TableCell] = []
    has_review_cells = False

    for r_idx in range(max_rows):
        row_a = grid_a[r_idx] if r_idx < len(grid_a) else []
        row_b = grid_b[r_idx] if r_idx < len(grid_b) else []

        for c_idx in range(max_cols):
            val_a = row_a[c_idx].strip() if c_idx < len(row_a) else ""
            val_b = row_b[c_idx].strip() if c_idx < len(row_b) else ""

            cell_id = f"c_{table_id}_{r_idx}_{c_idx}"
            bbox = BoundingBox(
                page_number=page_number,
                x0=float((c_idx / max(max_cols, 1)) * 1000.0),
                y0=float((r_idx / max(max_rows, 1)) * 1000.0),
                x1=float(((c_idx + 1) / max(max_cols, 1)) * 1000.0),
                y1=float(((r_idx + 1) / max(max_rows, 1)) * 1000.0),
            )
            evidence = EvidenceCoordinates(
                document_id=doc_id,
                page_number=page_number,
                bbox=bbox,
                raw_text=val_a or val_b,
                render_image_key=f"renders/{doc_id}/p{page_number}.png",
                crop_image_key=f"crops/{doc_id}/{cell_id}.png",
            )

            # 1. Full Consensus
            if val_a == val_b:
                norm = canonicalize_financial_number(val_a)
                cell = TableCell(
                    id=cell_id,
                    table_id=table_id,
                    row_idx=r_idx,
                    col_idx=c_idx,
                    is_header=(r_idx == 0),
                    raw_text=val_a,
                    normalized_value=norm.normalized_value,
                    currency=norm.currency,
                    scale=norm.scale,
                    tier=AccuracyTier.EXTRACTED,
                    evidence=evidence,
                    extraction=ExtractionMetadata(
                        engines_used=["engine_a_pdfplumber", "engine_b_docling"],
                        agreement_score=1.0,
                    ),
                )
                cells.append(cell)

            # 2. Disagreement -> Adjudication
            else:
                crop_bytes = crop_map.get((r_idx, c_idx), b"fake_crop_bytes")
                adj_result = llm.adjudicate_cell_crop(
                    crop_image_bytes=crop_bytes,
                    candidate_a=val_a,
                    candidate_b=val_b,
                )

                chosen_val = adj_result.get("adjudicated_value", "")
                conf = adj_result.get("confidence", 0.0)

                # Check if resolved with high confidence matching candidate
                if conf >= 0.95 and chosen_val in [val_a, val_b]:
                    norm = canonicalize_financial_number(chosen_val)
                    cell = TableCell(
                        id=cell_id,
                        table_id=table_id,
                        row_idx=r_idx,
                        col_idx=c_idx,
                        is_header=(r_idx == 0),
                        raw_text=chosen_val,
                        normalized_value=norm.normalized_value,
                        currency=norm.currency,
                        scale=norm.scale,
                        tier=AccuracyTier.EXTRACTED,
                        evidence=evidence,
                        extraction=ExtractionMetadata(
                            engines_used=["engine_a", "engine_b", "vision_adjudicator"],
                            agreement_score=0.5,
                            raw_candidates={"engine_a": val_a, "engine_b": val_b},
                            vision_adjudicated=True,
                        ),
                    )
                    cells.append(cell)
                else:
                    # Unresolved conflict -> Tier R (Needs Review)
                    has_review_cells = True
                    norm = canonicalize_financial_number(val_a or val_b)
                    cell = TableCell(
                        id=cell_id,
                        table_id=table_id,
                        row_idx=r_idx,
                        col_idx=c_idx,
                        is_header=(r_idx == 0),
                        raw_text=val_a or val_b,
                        normalized_value=norm.normalized_value,
                        currency=norm.currency,
                        scale=norm.scale,
                        tier=AccuracyTier.NEEDS_REVIEW,
                        evidence=evidence,
                        extraction=ExtractionMetadata(
                            engines_used=["engine_a", "engine_b"],
                            agreement_score=0.0,
                            raw_candidates={"engine_a": val_a, "engine_b": val_b},
                            vision_adjudicated=False,
                        ),
                    )
                    cells.append(cell)

    table_tier = AccuracyTier.NEEDS_REVIEW if has_review_cells else AccuracyTier.EXTRACTED
    return Table(
        id=table_id,
        document_id=doc_id,
        page_number=page_number,
        title="Ensemble Reconstructed Table",
        rows_count=max_rows,
        cols_count=max_cols,
        cells=cells,
        bbox=BoundingBox(page_number=page_number, x0=50.0, y0=50.0, x1=950.0, y1=950.0),
        tier=table_tier,
    )
