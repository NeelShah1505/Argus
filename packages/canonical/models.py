"""
Argus Canonical Data Model
Defines the universal immutable schema contracts for all document extraction,
normalization, verification, and analytical entities.
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AccuracyTier(str, Enum):
    """
    Accuracy tiers governing the Evidence Contract:
    - V (Verified): >=2 engines agree + arithmetic/identity checks passed + valid source bbox.
    - E (Extracted): Confident single-engine extraction, no cross-check available.
    - M (Estimated): Measured from chart geometry; carries explicit tolerance bounds.
    - R (Needs Review): Validation failure, ensemble disagreement, or low OCR confidence.
    - F (Failed): Extraction failed; region preserved for debugging.
    """
    VERIFIED = "V"
    EXTRACTED = "E"
    ESTIMATED = "M"
    NEEDS_REVIEW = "R"
    FAILED = "F"


class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    CLASSIFIED = "CLASSIFIED"
    ROUTED = "ROUTED"
    EXTRACTED = "EXTRACTED"
    NORMALIZED = "NORMALIZED"
    VALIDATED = "VALIDATED"
    APPROVED = "APPROVED"
    PARTIAL = "PARTIAL"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    INDEXED = "INDEXED"
    ANALYSIS_READY = "ANALYSIS_READY"
    FAILED = "FAILED"
    ERROR = "ERROR"


class BoundingBox(BaseModel):
    page_number: int
    x0: float
    y0: float
    x1: float
    y1: float
    unit: str = "normalized_1000"  # Coords normalized to [0, 1000]


class EvidenceCoordinates(BaseModel):
    document_id: str
    page_number: int
    bbox: BoundingBox
    raw_text: str
    render_image_key: str
    crop_image_key: Optional[str] = None


class ExtractionMetadata(BaseModel):
    engines_used: List[str] = Field(default_factory=list)
    agreement_score: float = 1.0
    raw_candidates: Dict[str, str] = Field(default_factory=dict)
    vision_adjudicated: bool = False


class ValidationResult(BaseModel):
    rule_id: str
    rule_name: str
    passed: bool
    expected_value: Optional[Decimal] = None
    actual_value: Optional[Decimal] = None
    discrepancy: Optional[Decimal] = None
    message: str


class Document(BaseModel):
    id: str
    tenant_id: str
    filename: str
    file_hash: str  # SHA-256
    mime_type: str
    page_count: int = 0
    status: DocumentStatus = DocumentStatus.UPLOADED
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Page(BaseModel):
    id: str
    document_id: str
    page_number: int
    render_key: str
    width: float
    height: float


class TOCItem(BaseModel):
    level: int  # 1 for H1/Section, 2 for H2, 3 for H3
    title: str
    page_number: int
    section_id: str
    bbox: Optional[BoundingBox] = None


class DocumentOutline(BaseModel):
    document_id: str
    items: List[TOCItem] = Field(default_factory=list)


class TextElement(BaseModel):
    id: str
    document_id: str
    page_number: int
    text: str
    bbox: BoundingBox
    confidence: float = 1.0


class TableCell(BaseModel):
    id: str
    table_id: str
    row_idx: int
    col_idx: int
    row_span: int = 1
    col_span: int = 1
    is_header: bool = False
    raw_text: str
    normalized_value: Optional[Decimal] = None
    currency: Optional[str] = None
    scale: Optional[Decimal] = None
    tier: AccuracyTier = AccuracyTier.NEEDS_REVIEW
    evidence: EvidenceCoordinates
    extraction: ExtractionMetadata = Field(default_factory=ExtractionMetadata)
    validations: List[ValidationResult] = Field(default_factory=list)


class Table(BaseModel):
    id: str
    document_id: str
    page_number: int
    title: Optional[str] = None
    rows_count: int
    cols_count: int
    cells: List[TableCell] = Field(default_factory=list)
    bbox: BoundingBox
    tier: AccuracyTier = AccuracyTier.NEEDS_REVIEW


class Figure(BaseModel):
    id: str
    document_id: str
    page_number: int
    caption: Optional[str] = None
    figure_type: str = "chart"
    bbox: BoundingBox
    image_crop_key: str
    chart_series: List["ChartSeries"] = Field(default_factory=list)
    diagram_graph: Optional["DiagramGraph"] = None


class ChartSeriesPoint(BaseModel):
    x_label: str
    y_value: Decimal
    tolerance: Decimal = Decimal("0.0")


class ChartSeries(BaseModel):
    series_name: str
    points: List[ChartSeriesPoint] = Field(default_factory=list)
    method: str = "measured"
    tolerance: Decimal = Decimal("0.02")


class DiagramNode(BaseModel):
    id: str
    text: str
    node_type: str = "process"
    bbox: Optional[BoundingBox] = None


class DiagramEdge(BaseModel):
    from_node_id: str
    to_node_id: str
    label: Optional[str] = None


class DiagramGraph(BaseModel):
    nodes: List[DiagramNode] = Field(default_factory=list)
    edges: List[DiagramEdge] = Field(default_factory=list)


class Fact(BaseModel):
    id: str
    tenant_id: str
    document_id: str
    element_id: str
    entity: str
    metric: str
    period: str  # ISO 8601 or fiscal identifier, e.g., 'FY2024'
    value: Decimal
    raw_text: str
    currency: str = "USD"
    scale: Decimal = Decimal("1.0")
    tier: AccuracyTier
    confidence: float = 1.0
    evidence: EvidenceCoordinates
    extraction: ExtractionMetadata = Field(default_factory=ExtractionMetadata)
    validations: List[ValidationResult] = Field(default_factory=list)


class DerivedMetric(BaseModel):
    id: str
    tenant_id: str
    formula_id: str
    formula_name: str
    input_fact_ids: List[str]
    calculated_value: Decimal
    tier: AccuracyTier
    lineage_dag: Dict[str, Any] = Field(default_factory=dict)


class Correction(BaseModel):
    id: str
    tenant_id: str
    document_id: str
    element_id: str
    old_value: Optional[str] = None
    new_value: str
    reviewer_id: str
    reason: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    propagated_to: List[str] = Field(default_factory=list)


class AuditEvent(BaseModel):
    id: str
    tenant_id: str
    document_id: str
    event_type: str
    actor_id: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Job(BaseModel):
    id: str
    tenant_id: str
    document_id: str
    stage: str
    status: str
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
