# Argus — Project Context & Operating Charter

**Single Source of Truth**  
*Read before touching any code, prompts, schemas, or design components.*

---

## 1. Executive Summary & Mission
**Argus** is an evidence-first financial document intelligence platform engineered for mission-critical auditability. It ingests complex business and financial documents (native PDFs, DOCXs, XLSXs, CSVs, PPTXs, and later scanned images and charts), reconstructs tables, hierarchies, narrative text, figures, and diagrams into an immutable canonical model, independently verifies every extracted datum, executes deterministic financial computations, and surfaces high-value insights with cryptographic, pixel-level provenance.

### What Argus IS
- A precision data pipeline and auditable review instrument where **every number is on trial**.
- A deterministic arithmetic and validation engine that guarantees **zero unflagged errors**.
- An analyst copilot equipped with a strict code-level claim verifier that strips any ungrounded hallucination.
- A compounding template memory platform where human corrections actively train layout rules.

### What Argus IS NOT
- **Not** a naive LLM wrapper with a file-upload button.
- **Not** an ungrounded statistical guessing tool running ARIMA on 4 annual data points.
- **Not** an autonomous black-box that silently guesses when extraction paths disagree.

---

## 2. Business Context & Stakeholder Landscape
Argus is engineered to satisfy two high-stakes commercial environments:
1. **Internal Operations:** High-throughput, manager-assigned processing of complex enterprise filings (10-Ks, 10-Qs, audit reports, earnings decks, debt covenant schedules) featuring nested multi-page tables, merged headers, footnote linkages, and complex figures.
2. **Commercial Deployment (Dual-Client Enterprise Delivery):** The software is licensed and delivered to two enterprise client companies (institutional finance / private equity / audit). The client executives and senior analysts make capital allocation and compliance decisions based on the extracted figures. Consequently:
   - A wrong number is vastly worse than no number.
   - An uncited claim is a compliance liability.
   - Any silent failure destroys commercial credibility.

---

## 3. User Personas & Core Journeys

| Persona | Core Responsibilities | Critical Platform Needs |
| :--- | :--- | :--- |
| **Financial Analyst** *(Primary)* | Document upload, exploratory Q&A, variance analysis, ratio comparison, driver-based scenario modeling. | Instant search, 2-click drill-down to source pixels, exportable cited memos, guarantee of clean data. |
| **Reviewer / Audit Lead** | Exception management, cell conflict resolution, identity balancing, sign-off on flagged values. | Ultra-fast keyboard-first console (`j`/`k`/`Enter`/`E`), candidate side-by-side adjudication, audit trail. |
| **Client Executive / Partner** | Board presentations, covenant monitoring, risk evaluation, executive summaries. | Absolute trust in dashboard figures, zero hallucinated projections, 1-click **Audit Pack** export. |

---

## 4. The Evidence Contract (The Commercial Guarantee)
Traditional AI systems fail enterprise procurement because they cannot guarantee 100% accuracy on arbitrary inputs. Argus re-architects the problem by selling an **Evidence Contract** modeled directly on independent financial audit standards ("reasonable assurance with complete provenance"):

1. **Two-Click Traceability Guarantee:** Every number rendered on any dashboard, insight card, scenario model, or Q&A response is clickable to its source document page and bounding box in $\le 2$ clicks.
2. **No Silent Errors:** Every number belongs to an explicit **Accuracy Tier**. A number is either proven correct by dual-extraction consensus and arithmetic reconciliation (**Verified**) or it is visually flagged with an amber/red warning badge.
3. **The LLM Never Generates Numbers:** LLMs plan, summarize, and narrate. Extraction is performed by layout-aware vision/heuristic pipelines; arithmetic is computed using `decimal.Decimal` in a typed calculation registry; citations and numbers are validated by a deterministic server-side claim verifier.
4. **Estimates Carry Tolerances:** Numbers derived from charts or visual plots are explicitly labeled as **Estimated ($M$)** with strict tolerance bounds (e.g., $\pm 2.5\%$).
5. **Driver-Based Scenarios vs. Pseudo-Forecasting:** Statistical time-series forecasting (ARIMA/ETS) is strictly gated to series with $\ge 20$ historical observations. Projections with smaller samples are executed as deterministic driver scenarios and branded prominently as *"Scenario — Not a Forecast"*.
6. **Immutable Audit Lineage:** No data point is ever overwritten without versioning. Human corrections generate immutable audit events and invalidate all downstream dependent metrics.

---

## 5. Scope & Phased Rollout Strategy

```
Phase 1: Digital-Native Core (Current)
├── Formats: Native PDF, DOCX, XLSX, CSV, PPTX
├── Extraction: Dual-engine ensemble (pdfplumber + Docling) with cell-level voting
├── Normalization: Full financial numeric canonicalization (accounting negatives, EU, INR, scales)
├── Validation: L1 Structural + L2 Arithmetic (Foot/Cross-foot, Balance Sheet identities)
├── UI: Workspace Inbox, Document Explorer (PDF.js bbox overlay), Review Console (keyboard-first)
└── Analysis: Fact Store, Calc Registry, Grounded Cited Q&A (Claim Verifier), Scenario Sliders

Phase 2: Scans, Charts & Template Memory (Next)
├── Scanned PDF & Image OCR (PaddleOCR / surya benchmarked)
├── TATR (Table Transformer) image-table segmentation
├── Chart Measurement Pipeline: tick OCR + geometric scale inversion + table reconciliation
├── Flowcharts & Org Trees -> interactive DiagramGraph (nodes/edges)
├── Layout Fingerprinting (perceptual hash + structural grid) & Template Memory propagation
└── Full Anomaly Engine (Benford's Law, duplicate invoice hash, segment-sum reconciliation)

Phase 3: Enterprise Hardening & Predictive Scaling (Future)
├── Statistical forecasting engine (ARIMA / ETS ladder for N >= 20 observations)
├── Universal format ingestion (EML/MSG, HTML filings, ZIP archives)
├── Multi-tenant enterprise RBAC, SSO, client KMS encryption, and PostgreSQL RLS
└── One-Click Audit Pack generation (PDF dossier with cell crops and signature certificates)
```

---

## 6. Strict Non-Goals (Version 1)
- **NO** free-form code execution or dynamic Python execution by LLM agents.
- **NO** statistical time-series forecasting on series with $< 20$ data points.
- **NO** training or fine-tuning of models on proprietary client financial data.
- **NO** automatic silent approval of $R$-tier (Needs Review) cells without explicit reviewer sign-off.
- **NO** floating-point arithmetic for currency, volumes, or shares.

---

## 7. Success Gates & Acceptance Thresholds

| Metric | Target Gate | Verification Method |
| :--- | :--- | :--- |
| **Silent Error Rate (SER)** | $< 0.1\%$ *(Zero tolerance for unflagged errors)* | Ground-truth benchmark suite |
| **Detection Rate (DR)** | $> 99.0\%$ *(Errors quarantined to Review tier)* | Injected error regression suite |
| **Critical-Field Exact Accuracy** *(Verified Tier, Digital PDFs)* | Target: $\ge 99.0\%$ *(Baselined against D1 Ground Truth)* | Golden-set regression suite in CI |
| **Table Cell Structural & Value $F_1$** | Target: $\ge 95.0\%$ *(Baselined against D1 Ground Truth)* | Grid alignment diff against ground truth |
| **Provenance Coverage of Displayed Numerals** | $100.0\%$ | Automated UI claim scanner |
| **Unsupported Numeric Claims in Answers** | $0$ *(Hard Gate)* | Server-side Deterministic Claim Verifier |
| **Human Review Intervention Rate** | Tracked per doc type; target $< 10.0\%$ | Extraction telemetry |
| **Document Processing Cost Ceiling** | Capped per page | Token & execution budget telemetry |

---

## 8. Domain Glossary
- **Canonical Model:** Unified object schema representing document layout, hierarchy, tables, cells, text elements, and figures regardless of source format.
- **Element:** An atomic extracted block (paragraph, table cell, figure, header).
- **Fact:** A semantic financial datum (Entity, Metric, Fiscal Period, Currency, Scale, Normalized Decimal Value).
- **Evidence:** Bounding box coordinates, page index, source render key, cell crop key, and raw printed text.
- **Tier ($V / E / M / R / F$):** Accuracy rating ($V$: Verified, $E$: Extracted, $M$: Estimated, $R$: Needs Review, $F$: Failed).
- **Adjudication:** The automated or human protocol for resolving extraction disagreements between ensemble parsers.
- **Golden Set:** Immutable benchmark suite of enterprise financial documents with verified ground-truth values.
- **Layout Fingerprint:** Perceptual image hash combined with structural tabular n-grams identifying recurring publisher templates.
- **Audit Pack:** Complete forensic export containing every dashboard metric, source snippet, validation record, and reviewer signature.

---

## 9. Foundational Architectural Decisions (D1 – D8)
- **D1 — The Evidence Contract:** Sell reasonable assurance with 4 clear tiers and 2-click drill-downs instead of unprovable "zero errors".
- **D2 — Multi-Engine Ensemble:** Table cells extracted by `pdfplumber` + `Docling`; disagreement triggers pixel crop re-reading via vision before escalating to human review.
- **D3 — Separation of LLM and Math:** LLM generates zero math. Extraction is pipelines; arithmetic is `decimal.Decimal`; claim verifier strips ungrounded tokens.
- **D4 — Pragmatic Phasing:** Native office formats (PDF, DOCX, XLSX, CSV, PPTX) in Phase 1 for maximum ROI; scans and chart geometry in Phase 2.
- **D5 — Compounding Memory:** Store procedural layout templates and entity aliases; never store fact values in memory.
- **D6 — CI-Gated Evaluation:** Hard accuracy gates in continuous integration; no merge permitted that regresses extraction fidelity.
- **D7 — Forensic Audit Pack:** One-click compliance bundle connecting balance sheet metrics to original document pixels.
- **D8 — Deterministic Scenario Modeling:** Driver-based scenario projections replace ungrounded statistical forecasts for sparse corporate filings.

---

## 10. Risk Matrix & Mitigations

| Risk | Severity | Mitigation Strategy |
| :--- | :--- | :--- |
| **R1: Scanned/Noisy Document Errors** | High | Ensemble disagreement triggers $R$-tier; low OCR confidence triggers confusion-pair adjudication; never auto-accept ambiguous digits. |
| **R2: Chart Value Inaccuracies** | High | Geometric scale inversion replaces LLM guesswork; values are tagged as Estimated with explicit error margins. |
| **R3: Runaway Multimodal Vision Costs** | Medium | Content-hash caching; vision invoked only on cropped ambiguous bboxes or visual figures; hard per-document budget limits. |
| **R4: Statistical Hallucinations** | High | Hard gate in code: $\ge 20$ observations required for statistical models; otherwise scenario math only. |
| **R5: Publisher Template Drift** | Medium | Perceptual and structural similarity scoring; drift drops below confidence threshold, triggering full re-extraction. |
