# ARGUS

### Agentic Financial Document Intelligence & Evidence-Grounded Extraction Engine

Argus is an autonomous, institutional-grade document intelligence platform built for financial filings (10-K, 10-Q, 8-K), investor presentations, corporate earnings releases, logistics documentation, and complex tabular statements.

Argus pairs deterministic mathematical validation, vector chart geometry decoding, and multi-document accounting reconciliation with an autonomous orchestrator loop and a zero-emoji financial UI.

---

## Key Capabilities

* **Multi-Format Ingestion:** Native extraction for PDF, DOCX, XLSX, and CSV with page-by-page rendering and SHA-256 deduplication.
* **Dual-Layer OCR & Geometry:** Detects scanned pages, missing text layers, and renders high-DPI rasters with automated OCR confusion correction (`$S` -> `$5`, `O` -> `0`).
* **Vector Chart Geometry Decoder:** Extracts vector drawing primitives (`path`, `rect`, `line`, `curve`) from PDF vector streams to mathematically reverse-engineer bar heights, trends, and exact numeric series without raster distortion.
* **Financial Concept Ontology & Footing:** Over 25+ standardized GAAP/IFRS line items with strict decimal-precision footing and cross-statement accounting balance checks.
* **Claim Verifier & NLI Engine:** Post-generation claim verifier that decomposes answers into individual atomic claims and verifies each against extracted bounding boxes and citation tokens.
* **Hierarchical Document Navigation:** Detects document outlines, headings, and bookmarks for jumping directly to financial disclosures and footnote notes.
* **Hybrid Lexical + Vector Retrieval:** Multi-tier dense and BM25 search over document chunks with cross-encoder re-ranking.
* **Multi-Document Financial Reconciliation:** Automatically matches line items across multi-year filings, tracks historical revisions, computes variances, and flags unannounced restatements.
* **Audit Pack Export:** Produces cryptographically hashed, evidence-grounded audit packs verifying every single numerical figure down to page and pixel coordinates.

---

## Architecture Overview

```
                        +----------------------------+
                        |  Multi-Format Ingestion    |
                        |   (PDF, DOCX, XLSX, CSV)   |
                        +--------------+-------------+
                                       |
                 +---------------------+---------------------+
                 |                                           |
                 v                                           v
      +----------------------+                    +----------------------+
      | Native Text & Tables |                    | OCR & Geometry Layer |
      |  (pdfplumber / fitz) |                    |  (Tesseract / Render)|
      +----------+-----------+                    +----------+-----------+
                 |                                           |
                 +---------------------+---------------------+
                                       |
                                       v
                    +-------------------------------------+
                    |   Vector Chart Geometry Decoder     |
                    |   (Direct SVG/Path Reverse Eng.)    |
                    +------------------+------------------+
                                       |
                                       v
                    +-------------------------------------+
                    |    Canonical Schema & Normalizer    |
                    |   (Exact Decimals + Bounding Boxes) |
                    +------------------+------------------+
                                       |
        +------------------------------+------------------------------+
        |                              |                              |
        v                              v                              v
+----------------+            +-----------------+           +--------------------+
| Accounting DAG |            | Hybrid Chunker  |           | Multi-Doc Registry |
|   Validation   |            |  & Search Index |           |  & Reconciliation  |
+-------+--------+            +--------+--------+           +---------+----------+
        |                              |                              |
        +------------------------------+------------------------------+
                                       |
                                       v
                    +-------------------------------------+
                    |   Agentic Orchestrator & Verifier   |
                    | (Entailment / Contradiction Guard)  |
                    +------------------+------------------+
                                       |
                                       v
                    +-------------------------------------+
                    |   Institutional React Web Console   |
                    |  (Zero-Emoji Financial Dark Theme)  |
                    +-------------------------------------+
```

---

## Directory Structure

```text
.
├── apps/
│   ├── api/                  # FastAPI backend server
│   │   ├── main.py           # Application entrypoint & CORS config
│   │   └── routers/          # Document ingestion, calculation, & audit endpoints
│   └── web/                  # Next.js 14 institutional frontend
│       ├── src/app/          # Global styles, page routes, layout
│       └── src/components/   # Minimalist SVG icons, explorer, reconciliation tab
├── evals/                    # Automated evaluation harness
│   ├── benchmark_runner.py   # Precision/Recall benchmark engine
│   ├── edgar_downloader.py   # Automated SEC EDGAR 10-K ingestion
│   └── golden/               # SEC golden truth datasets (AAPL, MSFT)
├── packages/
│   ├── agents/               # Claim verification & orchestrator agent loops
│   ├── calc/                 # Lineage DAG, formula registry, reconciliation engine
│   ├── canonical/            # Pydantic v2 schemas for tables, facts, & bounding boxes
│   ├── extractors/           # Multi-format, OCR, vector chart, & structure extractors
│   ├── llm/                  # Mock provider and LLM integration abstractions
│   └── retrieval/            # Hybrid dense + lexical search & chunking engine
├── samples/                  # Multi-format sample document suite
└── tests/                    # 120-test automated verification suite
```

---

## Getting Started

### Prerequisites

* Python 3.11+
* Node.js 18+ and `npm`
* Tesseract OCR (`brew install tesseract` on macOS)

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/NeelShah1505/Argus.git
cd Argus

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Run the test suite (120 tests across all 10 phases)
pytest tests/

# Launch the FastAPI backend server
uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend API documentation will be available at `http://localhost:8000/docs`.

### 2. Frontend Setup

```bash
# From repository root
cd apps/web

# Install frontend dependencies
npm install

# Start Next.js development server
npm run dev
```

The web console will be accessible at `http://localhost:3000`.

---

## Running Automated Benchmarks

Argus includes an SEC EDGAR golden benchmark runner evaluating table extraction precision, cell-level recall, and calculation lineage accuracy:

```bash
python3 evals/run_benchmarks.py
```

---

## License

Apache-2.0
