"""
Phase 6 Tests: Multimodal Vision Fallback for Raster Figures, Flowcharts & Budget Management.
"""

from decimal import Decimal
import io
import pytest
from PIL import Image

from packages.canonical import BoundingBox
from packages.extractors.vision_figure import (
    VisionBudgetExceeded,
    VisionFigureBudgetManager,
    extract_raster_figure,
)


def make_dummy_crop() -> bytes:
    im = Image.new("RGB", (200, 200), color=(240, 240, 240))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def test_extract_raster_chart_figure():
    crop = make_dummy_crop()
    bbox = BoundingBox(page_number=1, x0=50, y0=50, x1=250, y1=250)
    fig = extract_raster_figure(crop, figure_type="chart", doc_id="doc_vis_1", page_number=1, bbox=bbox)

    assert fig.figure_type == "chart"
    assert len(fig.chart_series) == 1
    series = fig.chart_series[0]
    assert len(series.points) >= 3
    assert series.points[0].x_label == "Q1"
    assert series.points[0].y_value == Decimal("120.5")
    assert fig.image_crop_key.startswith("crops/doc_vis_1/")


def test_extract_raster_flowchart_figure():
    crop = make_dummy_crop()
    bbox = BoundingBox(page_number=2, x0=100, y0=100, x1=400, y1=300)
    fig = extract_raster_figure(crop, figure_type="diagram", doc_id="doc_vis_2", page_number=2, bbox=bbox)

    assert fig.figure_type == "diagram"
    assert fig.diagram_graph is not None
    graph = fig.diagram_graph
    assert len(graph.nodes) == 3
    assert len(graph.edges) == 2
    assert graph.nodes[0].text == "Customer Ingestion"
    assert graph.edges[0].label == "extracts"


def test_vision_budget_limit_enforced():
    """Verify that per-document vision call ceiling prevents runaway API consumption."""
    mgr = VisionFigureBudgetManager(max_calls_per_doc=2)
    doc_id = "doc_heavy_runaway"

    mgr.record_call(doc_id)
    assert mgr.get_count(doc_id) == 1
    mgr.record_call(doc_id)
    assert mgr.get_count(doc_id) == 2

    with pytest.raises(VisionBudgetExceeded):
        mgr.record_call(doc_id)
