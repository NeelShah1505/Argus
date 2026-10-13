# Argus — Design System & UI/UX Specification

**Positioning Statement:** *"Every number, on trial."*  
Argus is designed not as a generic SaaS dashboard, but as a high-precision financial instrument. The aesthetic merges the typographic dignity of a vintage Swiss annual report with the ultra-dense ergonomics of a Bloomberg terminal.

---

## 1. Core Design Principles

1. **Evidence is One Gesture Away:** Every financial number on screen can be traced to its exact source pixel in $\le 2$ clicks. Clicking or hovering a number summons its forensic evidence dossier.
2. **Density with Air:** Financial analysts process thousands of cells per session. Interfaces prioritize high information density (compact tables, 12.5px mono numerals), separated by intentional negative space and structured borders.
3. **Status is Color + Shape + Label:** Colorblindness (protanopia/deuteranopia) is common in institutional finance. Accuracy tiers are NEVER communicated by color alone. Every indicator combines an icon, a distinctive border style, and a text badge.
4. **Numerals are Monospaced & Tabular:** All numbers, financial values, dates, percentages, and share counts use `IBM Plex Mono` with `font-variant-numeric: tabular-nums`. Digits align vertically down columns; visual tampering or misalignment is impossible.
5. **Purposeful Micro-Motion:** Animations are restricted to 120ms–180ms ease-out transitions that indicate state change (e.g., cell validation pass, drawer slide, bbox pulse). No gratuitous floating elements.

---

## 2. Color System & Design Tokens

### 2.1 Dark Canvas Theme (Primary — Optimized for 10-Hour Analyst Shifts)

```css
:root {
  /* Surfaces & Hierarchy */
  --bg-canvas:        #0A0D12;  /* Deep abyssal slate background */
  --bg-surface:       #10151C;  /* Panel and container base */
  --bg-raised:        #161D26;  /* Card, popover, and dropdown surface */
  --bg-inset:         #06080B;  /* Sunken wells, code blocks, table headers */

  /* Borders & Dividers */
  --border-subtle:    rgba(255, 255, 255, 0.06);
  --border-default:   rgba(255, 255, 255, 0.12);
  --border-strong:    rgba(255, 255, 255, 0.22);

  /* Typography & Readability */
  --text-primary:     #E9EEF4;  /* Crisp, high-contrast off-white */
  --text-secondary:   #9BA9B7;  /* Balanced cool slate for labels */
  --text-muted:       #5D6B7A;  /* Subdued helper text and captions */

  /* The 5 Accuracy Tiers (The Language of the Platform) */
  --tier-verified:    #2FD6A0;  /* Luminous Mint: dual agreement + math passed */
  --tier-verified-bg: rgba(47, 214, 160, 0.10);
  --tier-extracted:   #7FA6C9;  /* Cool Steel Blue: confident single engine */
  --tier-extracted-bg:rgba(127, 166, 201, 0.10);
  --tier-estimated:   #9B8CFF;  /* Iris Violet: chart-measured with tolerance */
  --tier-estimated-bg:rgba(155, 140, 255, 0.10);
  --tier-review:      #F5B541;  /* Amber Alert: disagreement / check failure */
  --tier-review-bg:   rgba(245, 181, 65, 0.12);
  --tier-failed:      #F0545C;  /* Crimson: extraction or identity failure */
  --tier-failed-bg:   rgba(240, 84, 92, 0.12);

  /* Brand Accent */
  --accent:           #2FD6A0;  /* Deliberately matches Verified Mint */
  --focus-ring:       #2FD6A0;

  /* Colorblind-Safe Chart Palette (8 Channels) */
  --chart-1: #2FD6A0;
  --chart-2: #5B9CFF;
  --chart-3: #F5B541;
  --chart-4: #F0545C;
  --chart-5: #9B8CFF;
  --chart-6: #64C7CC;
  --chart-7: #C9D1D9;
  --chart-8: #E58FB1;
}
```

### 2.2 Light Paper Theme (Print & Boardroom Mode)
- `--bg-canvas`: `#FAFAF7` (Natural warm book paper)
- `--bg-surface`: `#FFFFFF`
- `--bg-raised`: `#F3F4F1`
- `--text-primary`: `#14181D`
- `--tier-verified`: `#0E9F6E` (Forest green adjusted for AA contrast)
- `--tier-review`: `#B7791F`

---

## 3. Typography Hierarchy

| Role | Font Family | Optical Size / Weight | Usage |
| :--- | :--- | :--- | :--- |
| **Display Headings** | `Fraunces` | Serif, Optical 72, Weight 500 | Main screen titles, executive reports, hero statements. |
| **Section Headings** | `IBM Plex Sans` | Sans-Serif, Weight 600 | H2–H4 panel headers, modal titles, drawer labels. |
| **Interface & Body** | `IBM Plex Sans` | Sans-Serif, Weight 400 / 500 | Form controls, descriptions, tooltips, analytical prose. |
| **Data, Values & Code**| `IBM Plex Mono` | Monospace, Tabular Figures | Table cells, metric values, bounding box coords, citations. |

### Scale Ladder
- `11px` — Caption, footnote index, bounding box coordinates (`IBM Plex Mono`)
- `12px` — Table cells, dense metadata, tier status pills
- `13px` — Review Console spreadsheet cells, secondary labels
- `14px` — Base interface text, form inputs, button labels
- `16px` — Card titles, subheadings (`IBM Plex Sans` 600)
- `20px` — Section headers
- `28px` — Primary Metric values on KPI cards (`IBM Plex Mono` 600)
- `40px` — Executive Display Headings (`Fraunces` 500)

---

## 4. Spacing, Borders & Radius Tokens

- **Base Spacing Grid:** 4px scale (`4px`, `8px`, `12px`, `16px`, `24px`, `32px`, `48px`, `64px`).
- **Corner Radii:**
  - Micro controls & buttons: `4px`
  - Cards & panels: `6px`
  - Dialogs & modals: `10px`
  - Tier pills & badges: `9999px` (Full capsule)
- **Focus Rings:** `2px solid var(--accent)` with `2px` offset; universally navigable via Tab.
- **Iconography:** Lucide Icons (stroke width 1.5px, size 16px default).

---

## 5. Signature Components (The Core Product Experience)

### 5.1 `TierBadge`
A compact pill communicating accuracy:
- **Verified (`[V]`):** Filled mint background, checkmark icon (`✓ Verified`).
- **Extracted (`[E]`):** Outline steel blue, single chevron (`• Extracted`).
- **Estimated (`[M]`):** Dashed violet outline, tilde icon (`≈ Estimated ±2.5%`). Hover displays tolerance.
- **Needs Review (`[R]`):** Pulsing amber warning triangle (`⚠ Review Required`).
- **Failed (`[F]`):** Crimson cross (`✕ Extraction Failed`).

### 5.2 `EvidencePopover` *(The Signature Trust Mechanic)*
Hovering any number in the application renders a delicate dotted underline. Clicking the number opens the interactive Evidence Popover in $160\text{ms}$:
1. **Thumbnail Page Render:** High-resolution preview of the original document page with the exact bounding box outlined in glowing Mint `--tier-verified` (or Amber for Review).
2. **Crop Snippet:** Zoomed $3\times$ crop of the printed cell.
3. **Raw Extracted Text:** Unprocessed OCR/character stream (e.g., `"$(1,245.5)"`).
4. **Engines & Consensus:** *"Engine A (pdfplumber) and Engine B (Docling) agreed (100% match)"*.
5. **Validation Proof:** Checkmark list: *"Balance Sheet Footing Passed"*, *"Sign Sanity Validated"*.
6. **"Open in Document Viewer" Button:** Immediately jumps the Document Explorer pane, scrolls to the page, and triggers a 400ms pulsing glow on the source bbox.

### 5.3 `ReviewGrid` *(The Review Console Core)*
A virtualized spreadsheet built on TanStack Table for extreme performance:
- Sticky frozen header and index columns.
- Keyboard Navigation:
  - `j` / `k` or `↑` / `↓`: Navigate rows.
  - `h` / `l` or `←` / `→`: Navigate cells.
  - `E`: Enter inline cell editing with instant real-time diff preview.
  - `Enter`: Commit correction (triggers instant subtotal re-calculation).
  - `F`: Flag cell for secondary audit.
  - `A`: Approve cell consensus.
  - `?`: Toggle keyboard shortcuts overlay.
- Conflicted cells display a split chip displaying Engine A candidate vs. Engine B candidate side-by-side with the high-resolution crop visible in the side panel.

### 5.4 `MetricCard` with Lineage Drawer
- Metric numeral displayed prominently in 28px `IBM Plex Mono`.
- Inline `TierBadge` and period variance chip (e.g., `+8.2% YoY`).
- Sparkline trend curve.
- Clicking the card opens the **Lineage Drawer**: a visual mini-DAG illustrating:
  $$\text{Primary Fact A (Revenue)} \times \text{Primary Fact B (Margin)} \longrightarrow \text{Derived Metric}$$
  Every node in the DAG is clickable to summon its underlying `EvidencePopover`.

### 5.5 `ChartWithEvidence`
Rendered with Apache ECharts:
- Verified series rendered with solid stroke.
- Estimated series rendered with dashed stroke and a semi-transparent hatched tolerance band.
- Hovering any chart data point summons a miniature `EvidencePopover` pinpointing the exact table row or figure coordinates from which the data point originated.

---

## 6. The 7 Core Screens

### Screen 1: Workspace Inbox
- Upload dropzone accepting multi-file batches (PDF, DOCX, XLSX, CSV, PPTX).
- Document data table with real-time state chips (`UPLOADED` $\to$ `EXTRACTING` $\to$ `VALIDATED`).
- High-priority exception counter badge: *"Needs Your Review: 14 Cells"*.

### Screen 2: Document Explorer
- Tri-pane layout:
  - **Left Pane:** Document outline tree (Bookmarks, Sections, Tables, Figures).
  - **Center Pane:** Interactive canvas rendering document pages with interactive colored bounding box overlays tinted by accuracy tier.
  - **Right Pane:** Structured canonical tree showing extracted elements, metadata, and raw text.
- Synchronized selection: Clicking an element in the tree pans the page to the bounding box; clicking a bounding box on the page selects the element in the tree.

### Screen 3: Review Console *(The Financial Audit Machine)*
- Dedicated view for reconciling flagged documents:
  - **Left Side (45% Width):** Synchronized PDF.js page viewport that auto-scrolls to the exact coordinates of the currently active cell in the spreadsheet.
  - **Center Side (40% Width):** Virtualized `ReviewGrid` spreadsheet with keyboard-first controls.
  - **Right Side (15% Width):** Candidate Adjudication Panel displaying Engine A crop, Engine B crop, and vision re-read consensus.

### Screen 4: Insights Dashboard
- Executive overview presenting critical financial statements (Income Statement, Balance Sheet, Cash Flow).
- KPI metric cards, comparative growth tables, and ratio matrices.
- Integrated **Anomaly Feed** sorted by severity (Critical, High, Medium) with 1-click drill-downs to source anomalies.

### Screen 5: Grounded Q&A ("Ask Argus")
- Conversational research interface.
- Analyst questions answered in structured, cited prose.
- Every claim features clickable citation chips (`[Apple 10-K, p.32, Table 4]`).
- Designed **Abstention State**: When evidence is missing, renders a clean, constructive card detailing exactly which document or footnote needs to be uploaded.

### Screen 6: Scenario & Projections Modeler
- Interactive driver modeling interface:
  - Slider controls for Revenue Growth Rate %, Gross Margin bps, OpEx Escalation.
  - Live recalculation curve labeled prominently: *"Scenario Model — Not a Statistical Forecast"*.
  - Assumptions Ledger displaying every variable, its default value, and the user who modified it.

### Screen 7: Quality, Admin & Audit Pack Center
- Real-time CI eval scorecard tracking extraction accuracy over time.
- Layout Template Memory list with matching confidence percentages.
- Document token and processing cost tracker.
- **One-Click Audit Pack Export:** Generates a cryptographically signed PDF compilation containing every dashboard figure, source pixel screenshot, identity validation record, and reviewer signature.

---

## 7. Accessibility & Ergonomics Standards

- **Contrast Ratios:** All text, badges, and border tokens strictly exceed WCAG 2.1 AA standards ($4.5:1$ for normal body text, $3:1$ for large headings and controls).
- **Keyboard Traversal:** The entire review workflow can be operated with zero mouse dependency.
- **Reduced Motion:** If `prefers-reduced-motion` is detected, all transitions collapse to instant $0\text{ms}$ updates.
- **Screen Reader Semantics:** Data tables utilize native semantic HTML elements (`<table>`, `<thead>`, `<th>`, `<tbody>`, `<td>`) with `aria-label` describing cell coordinates and accuracy tiers.
