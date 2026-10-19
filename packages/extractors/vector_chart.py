"""
Vector Chart Geometry Decoder.

Extracts data series and points from digitally-rendered vector charts in PDFs
by inspecting drawing path streams (`page.get_drawings()`) and performing
linear regression scale calibration against axis tick labels.
"""

from decimal import Decimal, InvalidOperation
import io
import math
import re
from typing import Any, Dict, List, Optional, Tuple
import uuid
import fitz  # PyMuPDF
from PIL import Image

from packages.canonical import (
    AccuracyTier,
    BoundingBox,
    ChartSeries,
    ChartSeriesPoint,
    Figure,
)
from packages.normalize import canonicalize_financial_number


class LinearScale:
    def __init__(self, slope: float, intercept: float, r_squared: float):
        self.slope = slope
        self.intercept = intercept
        self.r_squared = r_squared

    def y_to_val(self, y: float) -> float:
        """Inverts a visual Y-pixel coordinate into a financial value."""
        return self.slope * y + self.intercept


def fit_linear_scale(ticks: List[Tuple[float, float]]) -> Optional[LinearScale]:
    """
    Fits linear model: Value = slope * y_pixel + intercept.
    Requires at least 2 distinct tick points.
    """
    if len(ticks) < 2:
        return None

    # Sort ticks by y coordinate
    ticks = sorted(ticks, key=lambda p: p[0])
    n = len(ticks)
    sum_y = sum(p[0] for p in ticks)
    sum_v = sum(p[1] for p in ticks)
    sum_y2 = sum(p[0] ** 2 for p in ticks)
    sum_yv = sum(p[0] * p[1] for p in ticks)

    denom = (n * sum_y2 - sum_y ** 2)
    if abs(denom) < 1e-9:
        return None

    slope = (n * sum_yv - sum_y * sum_v) / denom
    intercept = (sum_v - slope * sum_y) / n

    # Compute R^2
    mean_v = sum_v / n
    ss_tot = sum((p[1] - mean_v) ** 2 for p in ticks)
    ss_res = sum((p[1] - (slope * p[0] + intercept)) ** 2 for p in ticks)
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0

    return LinearScale(slope=slope, intercept=intercept, r_squared=r_squared)


def extract_vector_charts(
    page: fitz.Page,
    page_number: int,
    doc_id: str,
) -> List[Tuple[Figure, ChartSeries]]:
    """
    Scans vector drawings on the page for clustered chart geometries
    (vertical bars, column clusters), calibrates axis scale, and extracts
    data series.
    """
    drawings = page.get_drawings()
    if not drawings:
        return []

    # 1. Collect solid-filled rectangles
    rects: List[fitz.Rect] = []
    for d in drawings:
        fill = d.get("fill")
        # Must have fill color
        if not fill:
            continue
        for item in d.get("items", []):
            if item[0] == "re":
                r = item[1]
                # Filter out full-page backgrounds and thin gridlines
                if r.width > 5.0 and r.height > 5.0 and r.width < (page.rect.width * 0.8) and r.height < (page.rect.height * 0.8):
                    rects.append(r)

    if len(rects) < 2:
        return []

    # 2. Cluster rectangles into potential bar charts
    # Group rects by similar width and common baseline (within 10 px)
    clusters: List[List[fitz.Rect]] = []
    sorted_rects = sorted(rects, key=lambda r: (r.y1, r.x0))

    current_cluster = [sorted_rects[0]]
    for r in sorted_rects[1:]:
        prev = current_cluster[-1]
        # Check if sharing baseline within 8px and having similar width
        if abs(r.y1 - prev.y1) < 8.0 and abs(r.width - prev.width) < 8.0 and (r.x0 > prev.x0):
            current_cluster.append(r)
        else:
            if len(current_cluster) >= 2:
                clusters.append(current_cluster)
            current_cluster = [r]
    if len(current_cluster) >= 2:
        clusters.append(current_cluster)

    if not clusters:
        return []

    # 3. For each cluster, look for adjacent text (ticks on Y, labels on X)
    results: List[Tuple[Figure, ChartSeries]] = []
    text_words = page.get_text("words")  # (x0, y0, x1, y1, word, block_no, line_no, word_no)

    for cluster_idx, bar_rects in enumerate(clusters):
        chart_x0 = min(r.x0 for r in bar_rects)
        chart_x1 = max(r.x1 for r in bar_rects)
        chart_y0 = min(r.y0 for r in bar_rects)
        chart_y1 = max(r.y1 for r in bar_rects)

        # Look for Y-axis ticks to the left of the chart (x in [chart_x0 - 150, chart_x0])
        ticks: List[Tuple[float, float]] = []
        for w in text_words:
            wx0, wy0, wx1, wy1, word = w[0], w[1], w[2], w[3], w[4]
            if (chart_x0 - 180 <= wx0 <= chart_x0 + 10) and (chart_y0 - 50 <= wy0 <= chart_y1 + 50):
                norm = canonicalize_financial_number(word)
                if not norm.is_null and norm.normalized_value is not None:
                    # Visual center y of tick
                    tick_y = (wy0 + wy1) / 2.0
                    ticks.append((tick_y, float(norm.normalized_value)))

        # Fallback ticks if axis ticks were sparse
        if len(ticks) < 2:
            # Baseline = 0, top of chart = 100 or relative scale
            ticks = [(chart_y1, 0.0), (chart_y0, 100.0)]

        scale = fit_linear_scale(ticks)
        if not scale:
            continue

        # Find X labels under each bar (y in [chart_y1 - 5, chart_y1 + 40])
        points: List[ChartSeriesPoint] = []
        tolerance_val = Decimal(str(round(abs(scale.slope) * 2.0, 2)))

        for b_idx, bar in enumerate(bar_rects):
            bar_center_x = (bar.x0 + bar.x1) / 2.0
            x_label = f"Series_{b_idx + 1}"

            # Look for closest text word directly under bar
            closest_dist = 1e9
            for w in text_words:
                wx0, wy0, wx1, wy1, word = w[0], w[1], w[2], w[3], w[4]
                if (chart_y1 - 5 <= wy0 <= chart_y1 + 45) and (bar.x0 - 20 <= wx0 <= bar.x1 + 20):
                    dist = abs((wx0 + wx1) / 2.0 - bar_center_x)
                    if dist < closest_dist:
                        closest_dist = dist
                        x_label = word.strip()

            # Measure bar value at top
            raw_measured_val = scale.y_to_val(bar.y0)
            point = ChartSeriesPoint(
                x_label=x_label,
                y_value=Decimal(str(round(raw_measured_val, 2))),
                tolerance=tolerance_val,
            )
            points.append(point)

        fig_id = f"fig_chart_{doc_id}_p{page_number}_{cluster_idx + 1}"
        series = ChartSeries(
            series_name=f"Chart Series {cluster_idx + 1}",
            points=points,
            method="vector_geometry_regression",
            tolerance=tolerance_val,
        )

        figure = Figure(
            id=fig_id,
            document_id=doc_id,
            page_number=page_number,
            caption=f"Vector Chart: {series.series_name}",
            figure_type="chart",
            bbox=BoundingBox(
                page_number=page_number,
                x0=chart_x0 - 40,
                y0=chart_y0 - 20,
                x1=chart_x1 + 20,
                y1=chart_y1 + 30,
            ),
            image_crop_key=f"crops/{doc_id}/{fig_id}.png",
            chart_series=[series],
        )
        results.append((figure, series))

    return results
