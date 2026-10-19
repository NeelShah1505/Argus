# Argus — Foundational Architectural Decision Records (ADRs)

**Scope:** Foundational System Principles (D1 – D8)  
**Status:** Approved & Immutable for Phase 1

---

## ADR-01 (D1): The Evidence Contract vs. The Zero-Error Fallacy

### Context & Problem
Enterprise sales in institutional finance and audit fail when vendors claim "100% AI accuracy". Financial analysts know that non-deterministic neural networks make mistakes. When an AI system presents an inaccurate balance sheet number with high confidence, trust is permanently severed.

### Decision
Argus implements and markets the **Evidence Contract**, modeled on CPA audit standards ("reasonable assurance with complete provenance"):
1. The platform guarantees **zero unflagged errors** in the Verified ($V$) tier.
2. Every number is classified into one of four explicit accuracy tiers ($V, E, M, R$).
3. Any number is verifiable against its source pixel coordinates in $\le 2$ clicks.
4. Any ambiguity or validation failure halts automated promotion and visually flags the datum into Tier $R$ (Needs Review).

### Consequences
- **Positive:** Closes enterprise sales by offering defensible, auditable guarantees rather than unprovable marketing claims.
- **Trade-off:** Requires a dedicated Review Console UI for human sign-off on ambiguous edge cases.

---

## ADR-02 (D2): Multi-Engine Ensemble & Cell-Level Adjudication

### Context & Problem
Single-parser extraction is brittle. `pdfplumber` excels at character-level geometry but struggles with complex borderless tables; layout models like `Docling` excel at semantic reading order but can merge adjacent cells. A single dropped parenthesis or shifted column destroys financial models.

### Decision
Mandate a multi-engine extraction ensemble for all tabular data:
1. Every table is parsed independently by `pdfplumber` and `Docling`.
2. Both outputs are aligned to a normalized coordinate grid.
3. Cells are voted on individually:
   - **Full Consensus:** Automatically accepted into Tier $E$ or $V$.
   - **Disagreement:** Triggers automated **Cell Adjudication**: the bounding box crop is rendered from the page canvas and re-read with multimodal vision. If still conflicted, both candidates are presented side-by-side in the Review Console.

### Consequences
- **Positive:** Eliminates 95%+ of silent extraction errors before human intervention.
- **Trade-off:** $2\times$ processing overhead for tabular extraction, managed via async workers.

---

## ADR-03 (D3): Strict Separation of LLM Reasoning and Deterministic Math

### Context & Problem
LLMs are probabilistic token predictors and are fundamentally incapable of reliable floating-point arithmetic or accounting footing. Letting an LLM calculate "Gross Margin %" or "YoY Revenue Delta" produces catastrophic hallucinations.

### Decision
1. **The LLM Never Calculates Numbers:** All calculations are executed by a typed Python calculation registry using `decimal.Decimal`.
2. **Deterministic Claim Verifier:** A post-generation verification step (`claim_verifier.py`) inspects the LLM's analytical prose, extracts every numeric token, canonicalizes it through the 32-case financial number pipeline, verifies that each token maps to a registered Fact ID or Calculation ID in the context, and strips any ungrounded numbers.

### Consequences
- **Positive:** Mathematical correctness is absolute ($100\%$ reproducible). Hallucinations cannot leak into the UI.
- **Trade-off:** Agents cannot perform ad-hoc mental calculations; every metric must be registered as a typed formula.

---

## ADR-04 (D4): Pragmatic Format Phasing Strategy

### Context & Problem
Document extraction projects frequently stall trying to solve heavy scanned OCR, complex handwritten notes, and arbitrary formats all on Day 1.

### Decision
Phase the format rollout based on business value and extraction fidelity:
- **Phase 1 (Immediate Build):** Digital-native PDF, DOCX, XLSX, CSV, PPTX. Native office formats represent ~80% of corporate volume and can be extracted with lossless precision via programmatic libraries.
- **Phase 2:** Scanned PDFs, image-based tables (TATR), OCR pipelines (PaddleOCR/surya), and chart geometry measurement.
- **Phase 3:** Unstructured emails (EML/MSG), HTML filings, raw ZIP archives.

### Consequences
- **Positive:** Ships a robust, enterprise-grade core in weeks without getting bogged down in noisy scan OCR edge cases.
- **Trade-off:** Scanned image-only PDFs are quarantined to Tier $R$ or deferred until Phase 2.

---

## ADR-05 (D5): Compounding Procedural Memory vs. Hallucinated Facts

### Context & Problem
Storing financial facts in vector memory leads to temporal contamination (e.g., retrieving Q2 2023 figures for a Q2 2024 query). However, throwing away human reviewer corrections forces users to re-correct the same table layouts repeatedly.

### Decision
Implement a strict memory split:
- **Memory stores HOW:** Layout fingerprints, column mapping rules, subtotal quirks, entity alias dictionaries.
- **Memory NEVER stores WHAT:** Numerical fact values reside exclusively in the PostgreSQL relational fact store.
- **Correction Propagation:** A correction in the Review Console creates an immutable version bump and updates the procedural layout template for that publisher.

### Consequences
- **Positive:** Reviewer workload compounds down over time without any risk of hallucinated or stale financial facts.
- **Trade-off:** Requires a dual-vector layout fingerprinting algorithm (pHash + structural grid n-grams).

---

## ADR-06 (D6): CI-Gated Accuracy Harness

### Context & Problem
Prompt and parser changes frequently introduce silent regressions where fixing one table format breaks another.

### Decision
Establish an automated evaluation harness integrated into continuous integration:
1. Maintain an immutable Golden Set of benchmark documents.
2. Evaluate critical-field exact match (values, signs, scales, currency, periods).
3. Hard CI Gate: No code merge permitted if extraction $F_1 < 97\%$ or unsupported claim rate $> 0$.

### Consequences
- **Positive:** Engineering changes are measured against quantitative accuracy metrics, preventing regression drift.
- **Trade-off:** Developers must run `make eval` before merging significant pipeline changes.

---

## ADR-07 (D7): Forensic Audit Pack Export

### Context & Problem
Institutional clients must defend their findings to auditors, investment committees, and regulators. A screenshot of a web dashboard is insufficient.

### Decision
Provide a one-click **Audit Pack Export** feature:
- Compiles an executive dossier PDF linking every metric and chart series directly to high-resolution snippets of the original filing.
- Includes timestamped validation logs, mathematical footing proof, and cryptographic reviewer signatures.

### Consequences
- **Positive:** Immediate enterprise sales differentiator that transforms Argus from a utility into an indispensable compliance asset.
- **Trade-off:** Requires headless PDF rendering service (e.g., WeasyPrint or Playwright).

---

## ADR-08 (D8): Driver-Based Scenario Projections over Small-Sample Forecasting

### Context & Problem
Corporate annual reports typically yield $3$ to $8$ historical annual data points. Training ARIMA, Prophet, or neural time-series models on $N=5$ points is statistical malpractice.

### Decision
1. Gating Rule: Statistical time-series forecasting is prohibited in code for series with $N < 20$ observations.
2. For sparse corporate filings, Argus provides **Driver-Based Scenario Models** where users manipulate explicit operational assumptions (e.g., volume growth %, gross margin bps).
3. All outputs are labeled prominently in the UI as: *"Scenario Model — Not a Statistical Forecast"*.

### Consequences
- **Positive:** Retains intellectual credibility with CFOs and Wall Street analysts.
- **Trade-off:** Eliminates speculative "AI predictive" hype in favor of institutional rigor.
