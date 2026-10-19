"""
Phase 3 Tests: Vector Chart Geometry Decoder & Linear Scale Regression.
"""

from decimal import Decimal
import pytest
import fitz  # PyMuPDF

from packages.extractors.router import route_and_extract
from packages.extractors.vector_chart import (
    LinearScale,
    extract_vector_charts,
    fit_linear_scale,
)


def generate_digital_chart_pdf() -> bytes:
    """
    Creates a synthetic digital PDF containing a vector bar chart
    with exact vector rectangle drawing commands and text axis ticks.
    """
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)

    # 1. Draw 3 vertical bars (rectangles with blue fill)
    # Baseline is at y=500
    # Bar 1: x in [120, 160], y in [350, 500] -> height 150 (corresponds to $150M)
    page.draw_rect(fitz.Rect(120, 350, 160, 500), fill=(0.1, 0.4, 0.8), color=(0.1, 0.4, 0.8))
    # Bar 2: x in [200, 240], y in [250, 500] -> height 250 (corresponds to $250M)
    page.draw_rect(fitz.Rect(200, 250, 240, 500), fill=(0.1, 0.4, 0.8), color=(0.1, 0.4, 0.8))
    # Bar 3: x in [280, 320], y in [200, 500] -> height 300 (corresponds to $300M)
    page.draw_rect(fitz.Rect(280, 200, 320, 500), fill=(0.1, 0.4, 0.8), color=(0.1, 0.4, 0.8))

    # 2. Draw Y-axis tick labels to the left of the chart (x=50)
    # y=500 -> 0
    page.insert_text(fitz.Point(60, 500), "$0", fontsize=10)
    # y=400 -> 100M
    page.insert_text(fitz.Point(50, 400), "100M", fontsize=10)
    # y=300 -> 200M
    page.insert_text(fitz.Point(50, 300), "200M", fontsize=10)
    # y=200 -> 300M
    page.insert_text(fitz.Point(50, 200), "300M", fontsize=10)

    # 3. Draw X-axis labels below the baseline (y=520)
    page.insert_text(fitz.Point(125, 520), "FY22", fontsize=10)
    page.insert_text(fitz.Point(205, 520), "FY23", fontsize=10)
    page.insert_text(fitz.Point(285, 520), "FY24", fontsize=10)

    return doc.tobytes()


def test_linear_scale_calibration():
    # Ticks: (y_pixel, value)
    # In PDF coordinates: higher y is lower on page
    ticks = [(500.0, 0.0), (400.0, 100000000.0), (200.0, 300000000.0)]
    scale = fit_linear_scale(ticks)
    assert scale is not None
    assert scale.r_squared > 0.999

    # Check inversion
    val_500 = scale.y_to_val(500.0)
    assert round(val_500) == 0

    val_350 = scale.y_to_val(350.0)
    assert round(val_350) == 150000000


def test_extract_vector_charts_e2e():
    pdf_bytes = generate_digital_chart_pdf()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    results = extract_vector_charts(doc[0], page_number=1, doc_id="doc_chart_test")

    assert len(results) >= 1
    figure, series = results[0]

    assert figure.figure_type == "chart"
    assert figure.page_number == 1
    assert len(series.points) == 3

    labels = [p.x_label for p in series.points]
    assert "FY22" in labels
    assert "FY23" in labels
    assert "FY24" in labels

    # Check numerical measurements
    points_by_label = {p.x_label: p for p in series.points}
    fy22_val = points_by_label["FY22"].y_value
    fy23_val = points_by_label["FY23"].y_value
    fy24_val = points_by_label["FY24"].y_value

    assert abs(fy22_val - Decimal("150000000")) < Decimal("10000000")
    assert abs(fy23_val - Decimal("250000000")) < Decimal("10000000")
    assert abs(fy24_val - Decimal("300000000")) < Decimal("10000000")


def test_route_and_extract_includes_figures():
    pdf_bytes = generate_digital_chart_pdf()
    pages, text_elements, tables, figures = route_and_extract("report_with_charts.pdf", pdf_bytes, "doc_route_chart")

    assert len(figures) >= 1
    fig = figures[0]
    assert fig.figure_type == "chart"
    assert len(fig.chart_series) >= 1
    assert len(fig.chart_series[0].points) == 3
