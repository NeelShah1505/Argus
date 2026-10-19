"""
Multimodal Vision Fallback for Raster Figures, Charts & Flowcharts.

Routes cropped raster image figures and flowcharts to multimodal vision models
under strict per-document budget and token limits.
"""

from decimal import Decimal
import io
from typing import Any, Dict, List, Optional
import uuid

from packages.canonical import (
    AccuracyTier,
    BoundingBox,
    ChartSeries,
    ChartSeriesPoint,
    DiagramEdge,
    DiagramGraph,
    DiagramNode,
    Figure,
)
from packages.llm import get_llm_provider
from packages.storage.object_store import get_object_store


class VisionBudgetExceeded(Exception):
    pass


class VisionFigureBudgetManager:
    def __init__(self, max_calls_per_doc: int = 5):
        self.max_calls = max_calls_per_doc
        self._doc_counts: Dict[str, int] = {}

    def record_call(self, doc_id: str) -> None:
        count = self._doc_counts.get(doc_id, 0)
        if count >= self.max_calls:
            raise VisionBudgetExceeded(
                f"Visual processing budget exceeded ({self.max_calls} calls) for document {doc_id}."
            )
        self._doc_counts[doc_id] = count + 1

    def get_count(self, doc_id: str) -> int:
        return self._doc_counts.get(doc_id, 0)


_BUDGET_MGR = VisionFigureBudgetManager()


def extract_raster_figure(
    crop_image_bytes: bytes,
    figure_type: str,
    doc_id: str,
    page_number: int,
    bbox: BoundingBox,
    caption: Optional[str] = None,
) -> Figure:
    """
    Submits a figure crop to the vision provider with bounded budget enforcement.
    Parses response into typed ChartSeries or DiagramGraph.
    """
    _BUDGET_MGR.record_call(doc_id)
    provider = get_llm_provider()
    store = get_object_store()

    fig_id = f"fig_raster_{uuid.uuid4().hex[:8]}"
    crop_key = f"crops/{doc_id}/{fig_id}.png"
    store.put_bytes(crop_key, crop_image_bytes, content_type="image/png")

    raw_result = provider.extract_figure_visual(
        crop_image_bytes=crop_image_bytes,
        figure_type=figure_type,
        page_context=caption,
    )

    chart_series_list: List[ChartSeries] = []
    diagram_graph: Optional[DiagramGraph] = None

    if figure_type == "diagram":
        nodes = [
            DiagramNode(
                id=n["id"],
                text=n["text"],
                node_type=n.get("node_type", "process"),
            )
            for n in raw_result.get("nodes", [])
        ]
        edges = [
            DiagramEdge(
                from_node_id=e["from_node_id"],
                to_node_id=e["to_node_id"],
                label=e.get("label"),
            )
            for e in raw_result.get("edges", [])
        ]
        diagram_graph = DiagramGraph(nodes=nodes, edges=edges)
    else:
        # Chart
        points = [
            ChartSeriesPoint(
                x_label=p["x_label"],
                y_value=Decimal(str(p["y_value"])),
                tolerance=Decimal(str(p.get("tolerance", "2.0"))),
            )
            for p in raw_result.get("points", [])
        ]
        chart_series_list.append(
            ChartSeries(
                series_name=raw_result.get("series_name", "Visual Series"),
                points=points,
                method="multimodal_vision_fallback",
                tolerance=Decimal("2.5"),
            )
        )

    return Figure(
        id=fig_id,
        document_id=doc_id,
        page_number=page_number,
        caption=caption or raw_result.get("title", f"Raster {figure_type.capitalize()}"),
        figure_type=figure_type,
        bbox=bbox,
        image_crop_key=crop_key,
        chart_series=chart_series_list,
        diagram_graph=diagram_graph,
    )
