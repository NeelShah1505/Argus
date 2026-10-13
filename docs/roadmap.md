# Argus — Engineering Roadmap & Phasing Plan

**Status:** Active  
**Current Execution Focus:** Phase 1 (Core Foundations through Production Slice)

---

## Phase 1: Digital-Native Core Engine (Current Scope — Milestones M0 – M7)

The objective of Phase 1 is to construct the complete, auditable end-to-end slice for digital-native corporate filings with uncompromising accuracy and zero hallucination.

```
M0: Foundations & Scaffolding
├── Canonical Pydantic schemas (Document, Table, Cell, Fact, Evidence)
├── Repository layout, Makefile, Docker Compose (PostgreSQL 16 + pgvector, MinIO)
└── Pluggable LLM/Vision adapters with deterministic MockProvider fixture defaults

M1: Ingestion & Canonical Model
├── Multi-format ingest routes: PDF (pdfplumber/PyMuPDF), DOCX, XLSX, CSV, PPTX
├── Ingestion state machine (UPLOADED -> EXTRACTED -> VALIDATED -> APPROVED)
└── Per-page rendering to object storage with SHA-256 deduplication

M2: Table Ensemble, Canonicalization & Evidence Linkage
├── Dual-engine table parsing (pdfplumber + Docling) with cell-level grid alignment
├── Numeric Canonicalization engine ((1,245) -> -1245, EU/Indian formats, scale suffixes, nulls)
├── OCR confusion pair detection ({8<->3}, {5<->6}, {1<->l}, {0<->O})
└── Cell-level crop adjudication via vision model with fallback to Tier R

M3: Validation Engine, Accuracy Tiers & Review Actions
├── L1 Structural + L2 Arithmetic checks (Subtotal footing, Balance Sheet identities)
├── Accuracy Tier assignment (Verified, Extracted, Estimated, Needs Review, Failed)
└── Versioned human correction flow (PATCH /elements/:id) with append-only audit events

M4: Fact Store, Calculation Registry & Lineage DAG
├── Normalization of semantic facts (Entity, Metric, Fiscal Period, Normalized Decimal)
├── Typed calculation registry (Margins, YoY growth, liquidity ratios) using Decimal
└── Dependency graph tracking: changing a primary fact invalidates dependent metrics

M5: Retrieval, Agent Loop & Code-Level Claim Verifier
├── Structure-aware chunking preserving table headers, footnotes, and section hierarchy
├── Hybrid retrieval (pgvector embeddings + PostgreSQL full-text search)
├── Master system prompt orchestration loop with typed server-validated tools
└── Post-generation claim verifier (claim_verifier.py): strips any ungrounded numeric tokens

M6: Enterprise Web Application Core
├── Design system tokens (Dark canvas #0A0D12, Fraunces serif, IBM Plex Mono)
├── Workspace Inbox with processing status chips and exception counts
├── Document Explorer with PDF.js normalized bounding box overlay canvas
└── Keyboard-first Review Console (j/k rows, h/l cells, E inline edit, Enter save, A approve)

M7: Insights, Anomaly Catalog, Scenarios & Audit Pack
├── Executive Insights Dashboard with TierBadges, sparklines, and Lineage Drawers
├── 12-rule Anomaly Engine feed sorted by severity (Critical, High, Medium)
├── Driver-based Scenario Modeler ("Scenario Model — Not a Forecast")
└── One-Click Audit Pack Export: forensic PDF linking all numbers to original pixel crops
```

---

## Phase 2: Scanned OCR, Chart Measurement & Template Memory (Backlog)

*Prerequisite: Phase 1 acceptance gates cleared and verified on live corporate filings.*

### 1. Scanned Document OCR Pipeline
- Integration of `PaddleOCR` and `surya` for dense low-contrast scanned documents.
- Automatic page orientation, de-skewing, and noise filtering.
- Table Transformer (`TATR`) deep-learning model for borderless table segmentation on bitmap images.

### 2. Geometric Chart Measurement Engine
- Automatic segmentation of figure bounding boxes into chart classes (Bar, Line, Stacked Area, Pie).
- High-precision OCR extraction of axis tick labels and units.
- Pixel-coordinate extraction of bar heights and line inflection points.
- Linear regression scale fit: $V(y) = Y_{scale} \cdot (y - Y_0)$ with residual calculation.
- Automated reconciliation against printed data labels and adjacent financial table footnotes.
- Assignment of Tier $M$ (Estimated) with explicit tolerance intervals (e.g., $\pm 2.5\%$).

### 3. Diagram & Flowchart Extraction
- Visual analysis of organizational structures, process flows, and entity hierarchies.
- Extraction into canonical `DiagramGraph` (Nodes, Edges, Semantic Labels).
- Interactive SVG/Canvas graph viewer in the Document Explorer.

### 4. Layout Fingerprinting & Compounding Template Memory
- Perceptual hash (pHash) + structural grid topology n-grams for recurring document identification.
- Automatic propagation of reviewer corrections across matching documents from the same publisher.
- Template drift detection: down-weighting confidence if layout changes.

---

## Phase 3: Enterprise Hardening & Predictive Scaling (Future)

*Prerequisite: Dual-client deployment active with $> 1,000$ documents ingested.*

### 1. Statistical Forecasting Ladder
- Hard gate: Activated exclusively for time-series with $N \ge 20$ historical observations.
- Automated model ladder: Naive $\to$ Holt-Winters $\to$ ARIMA $\to$ ETS.
- Walk-forward backtesting with 80% and 95% confidence intervals rendered on charts.

### 2. Universal File Ingestion
- Native email parsing (`.eml`, `.msg`) with attachment tree extraction.
- SEC EDGAR live feed connector for direct XBRL and HTML filing ingestion.
- Multi-file ZIP archive batch ingestion with nested archive unpacking.

### 3. Enterprise Multi-Tenancy & Compliance
- PostgreSQL Row-Level Security (RLS) hardened with per-tenant connection pooling.
- Client-managed encryption keys (AWS KMS / Azure Key Vault per tenant).
- SOC 2 Type II audit logging, SAML / Okta SSO integration, and automated PII redaction pipelines.
