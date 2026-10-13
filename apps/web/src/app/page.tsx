"use client";

import React, { useState } from "react";
import { AnomalyFeed } from "../components/AnomalyFeed";
import { AskArgus } from "../components/AskArgus";
import { AuditPackViewer } from "../components/AuditPackViewer";
import { DocumentExplorer } from "../components/DocumentExplorer";
import { EvidencePopover } from "../components/EvidencePopover";
import { MetricCard } from "../components/MetricCard";
import { ReviewGrid } from "../components/ReviewGrid";
import { ScenarioModeler } from "../components/ScenarioModeler";
import { TierBadge } from "../components/TierBadge";

export default function ArgusApp() {
  const [activeTab, setActiveTab] = useState<
    "inbox" | "explorer" | "review" | "insights" | "ask" | "scenarios" | "audit"
  >("insights");

  // Sample data for ReviewGrid
  const sampleGrid = [
    [
      { id: "c_0_0", rowIdx: 0, colIdx: 0, rawText: "Financial Line Item", tier: "V" as const, isHeader: true },
      { id: "c_0_1", rowIdx: 0, colIdx: 1, rawText: "FY2023 Reported", tier: "V" as const, isHeader: true },
      { id: "c_0_2", rowIdx: 0, colIdx: 2, rawText: "FY2024 Reported", tier: "V" as const, isHeader: true },
      { id: "c_0_3", rowIdx: 0, colIdx: 3, rawText: "Consensus Tier", tier: "V" as const, isHeader: true },
    ],
    [
      { id: "c_1_0", rowIdx: 1, colIdx: 0, rawText: "Total Net Revenue", tier: "V" as const },
      { id: "c_1_1", rowIdx: 1, colIdx: 1, rawText: "$383,285M", tier: "V" as const },
      { id: "c_1_2", rowIdx: 1, colIdx: 2, rawText: "$391,036M", tier: "V" as const },
      { id: "c_1_3", rowIdx: 1, colIdx: 3, rawText: "✓ Verified", tier: "V" as const },
    ],
    [
      { id: "c_2_0", rowIdx: 2, colIdx: 0, rawText: "Cost of Goods Sold", tier: "V" as const },
      { id: "c_2_1", rowIdx: 2, colIdx: 1, rawText: "$(214,137)M", tier: "V" as const },
      { id: "c_2_2", rowIdx: 2, colIdx: 2, rawText: "$(213,972)M", tier: "V" as const },
      { id: "c_2_3", rowIdx: 2, colIdx: 3, rawText: "✓ Verified", tier: "V" as const },
    ],
    [
      { id: "c_3_0", rowIdx: 3, colIdx: 0, rawText: "Gross Profit Subtotal", tier: "V" as const },
      { id: "c_3_1", rowIdx: 3, colIdx: 1, rawText: "$169,148M", tier: "V" as const },
      { id: "c_3_2", rowIdx: 3, colIdx: 2, rawText: "$177,064M", tier: "V" as const },
      { id: "c_3_3", rowIdx: 3, colIdx: 3, rawText: "✓ Verified", tier: "V" as const },
    ],
    [
      { id: "c_4_0", rowIdx: 4, colIdx: 0, rawText: "Operating Expenses (R&D)", tier: "V" as const },
      { id: "c_4_1", rowIdx: 4, colIdx: 1, rawText: "$(29,915)M", tier: "V" as const },
      { id: "c_4_2", rowIdx: 4, colIdx: 2, rawText: "$(31,370)M", tier: "V" as const },
      { id: "c_4_3", rowIdx: 4, colIdx: 3, rawText: "✓ Verified", tier: "V" as const },
    ],
    [
      { id: "c_5_0", rowIdx: 5, colIdx: 0, rawText: "Restructuring Note Delta", tier: "R" as const },
      { id: "c_5_1", rowIdx: 5, colIdx: 1, rawText: "$0M", tier: "V" as const },
      { id: "c_5_2", rowIdx: 5, colIdx: 2, rawText: "$1,450M", tier: "R" as const, candidates: { engineA: "$1,450M", engineB: "$1,150M" } },
      { id: "c_5_3", rowIdx: 5, colIdx: 3, rawText: "⚠ Disagreement", tier: "R" as const },
    ],
  ];

  const sampleAnomalies = [
    {
      ruleId: "ANOM-02",
      ruleName: "Ensemble Variance Mismatch",
      severity: "High" as const,
      description: "Restructuring Note Delta cell variance between pdfplumber ($1,450M) and Docling ($1,150M).",
      affectedElement: "c_5_2",
    },
    {
      ruleId: "ANOM-03",
      ruleName: "YoY Variance Outlier",
      severity: "Medium" as const,
      description: "Other non-operating expense expanded by 58.4% YoY exceeding standard 40% band.",
      affectedElement: "c_6_2",
    },
  ];

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "var(--bg-canvas)", color: "var(--text-primary)" }}>
      {/* Top Header */}
      <header
        style={{
          borderBottom: "1px solid var(--border-default)",
          backgroundColor: "var(--bg-surface)",
          padding: "14px 28px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <h1 className="font-serif" style={{ fontSize: "24px", fontWeight: 600, letterSpacing: "-0.02em" }}>
            Argus
          </h1>
          <span style={{ fontSize: "11px", color: "var(--text-muted)", paddingLeft: "12px", borderLeft: "1px solid var(--border-subtle)" }}>
            Financial Intelligence Platform
          </span>
        </div>

        <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px" }}>
            <span style={{ color: "var(--text-muted)" }}>Evidence Guarantee:</span>
            <span style={{ color: "var(--tier-verified)", fontWeight: 600 }}>Zero Silent Errors</span>
          </div>
          <TierBadge tier="V" />
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav
        style={{
          display: "flex",
          gap: "8px",
          padding: "10px 28px",
          borderBottom: "1px solid var(--border-subtle)",
          backgroundColor: "var(--bg-surface)",
          overflowX: "auto",
        }}
      >
        {[
          { key: "insights", label: "Executive Insights" },
          { key: "review", label: "Review Console (Keyboard)" },
          { key: "explorer", label: "Document Explorer" },
          { key: "ask", label: "Ask Argus (Grounded Q&A)" },
          { key: "scenarios", label: "Scenario Modeler" },
          { key: "audit", label: "Audit Pack Center" },
          { key: "inbox", label: "Workspace Inbox" },
        ].map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key as any)}
            style={{
              padding: "6px 14px",
              borderRadius: "4px",
              border: "none",
              backgroundColor: activeTab === t.key ? "var(--bg-raised)" : "transparent",
              color: activeTab === t.key ? "var(--tier-verified)" : "var(--text-secondary)",
              fontWeight: activeTab === t.key ? 600 : 400,
              cursor: "pointer",
              fontSize: "13px",
              transition: "all 120ms ease-out",
            }}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {/* Main Body Content */}
      <main style={{ maxWidth: "1380px", margin: "0 auto", padding: "28px" }}>
        {/* TAB 1: Insights Dashboard */}
        {activeTab === "insights" && (
          <div style={{ display: "grid", gap: "24px" }}>
            {/* Top KPI Cards with Deterministic Lineage Drawers */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "16px" }}>
              <MetricCard
                label="Consolidated Net Revenue"
                value="$391,036M"
                tier="V"
                periodChange="+8.25%"
                formulaName="Reported Statement of Operations"
                inputs={[
                  { name: "Product Sales", value: "$298,085M", tier: "V" },
                  { name: "Services Revenue", value: "$92,951M", tier: "V" },
                ]}
              />

              <MetricCard
                label="Gross Margin"
                value="45.28%"
                tier="V"
                periodChange="+1.15%"
                formulaName="gross_margin = (revenue - cost_of_sales) / revenue"
                inputs={[
                  { name: "Total Revenue", value: "$391,036M", tier: "V" },
                  { name: "Cost of Sales", value: "$213,972M", tier: "V" },
                ]}
              />

              <MetricCard
                label="Operating Margin"
                value="30.93%"
                tier="V"
                periodChange="+0.45%"
                formulaName="operating_margin = operating_income / revenue"
                inputs={[
                  { name: "Operating Income", value: "$120,944M", tier: "V" },
                  { name: "Total Revenue", value: "$391,036M", tier: "V" },
                ]}
              />

              <MetricCard
                label="Current Liquidity Ratio"
                value="1.07x"
                tier="V"
                periodChange="+0.08x"
                formulaName="current_ratio = current_assets / current_liab"
                inputs={[
                  { name: "Current Assets", value: "$95,273M", tier: "V" },
                  { name: "Current Liabilities", value: "$88,750M", tier: "V" },
                ]}
              />
            </div>

            {/* Interactive Evidence Proof Demonstration */}
            <div
              style={{
                backgroundColor: "var(--bg-surface)",
                border: "1px solid var(--border-default)",
                borderRadius: "6px",
                padding: "20px",
              }}
            >
              <h3 style={{ fontSize: "16px", fontWeight: 600, marginBottom: "8px" }}>
                The Two-Click Forensic Trace Demonstration
              </h3>
              <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6" }}>
                Hover or click any value in Argus to invoke the cryptographic Evidence Dossier. For example, our verified operating income of{" "}
                <EvidencePopover
                  evidence={{
                    documentId: "doc_annual_2024",
                    pageNumber: 45,
                    rawText: "$120,944M",
                    tier: "V",
                    enginesUsed: ["pdfplumber", "Docling"],
                    agreementScore: 1.0,
                    validationsPassed: ["Subtotal Footing", "Balance Sheet Identity"],
                  }}
                  onOpenInDocument={() => setActiveTab("explorer")}
                >
                  $120,944M
                </EvidencePopover>{" "}
                was extracted with 100% agreement and checked against all accounting identities.
              </p>
            </div>

            {/* Anomaly Feed */}
            <AnomalyFeed anomalies={sampleAnomalies} onDrilldown={() => setActiveTab("review")} />
          </div>
        )}

        {/* TAB 2: Review Console */}
        {activeTab === "review" && (
          <div style={{ display: "grid", gap: "20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h2 style={{ fontSize: "20px", fontWeight: 600 }}>Review Console — High-Speed Exception Resolution</h2>
                <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "4px" }}>
                  Navigate with keyboard: <kbd>j</kbd>/<kbd>k</kbd> rows, <kbd>E</kbd> edit, <kbd>Enter</kbd> save, <kbd>A</kbd> approve. Corrections generate immutable audit events.
                </p>
              </div>
              <TierBadge tier="R" />
            </div>

            <ReviewGrid
              initialRows={sampleGrid}
              onCellCorrection={(cellId, newText) => {
                alert(`Cell ${cellId} corrected to '${newText}'. Document version bumped to v2. Audit event logged.`);
              }}
            />
          </div>
        )}

        {/* TAB 3: Document Explorer */}
        {activeTab === "explorer" && (
          <div style={{ display: "grid", gap: "20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h2 style={{ fontSize: "20px", fontWeight: 600 }}>Document Explorer & Bounding Box Overlays</h2>
                <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "4px" }}>
                  Interactive canvas mapping normalized bounding boxes directly on rendered document pages.
                </p>
              </div>
              <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>150 DPI Render Sync</span>
            </div>

            <DocumentExplorer />
          </div>
        )}

        {/* TAB 4: Ask Argus */}
        {activeTab === "ask" && (
          <div>
            <AskArgus />
          </div>
        )}

        {/* TAB 5: Scenario Modeler */}
        {activeTab === "scenarios" && (
          <div>
            <ScenarioModeler />
          </div>
        )}

        {/* TAB 6: Audit Pack Center */}
        {activeTab === "audit" && (
          <div>
            <AuditPackViewer />
          </div>
        )}

        {/* TAB 7: Workspace Inbox */}
        {activeTab === "inbox" && (
          <div style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--border-default)", borderRadius: "6px", padding: "28px" }}>
            <h2 style={{ fontSize: "20px", fontWeight: 600, marginBottom: "8px" }}>Workspace Document Inbox</h2>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginBottom: "24px" }}>
              Upload corporate filings in native PDF, DOCX, XLSX, CSV, or PPTX format. Deduplicated via SHA-256.
            </p>

            <div
              style={{
                border: "2px dashed var(--border-strong)",
                borderRadius: "8px",
                padding: "48px",
                textAlign: "center",
                backgroundColor: "var(--bg-inset)",
                marginBottom: "28px",
              }}
            >
              <div style={{ fontSize: "36px", marginBottom: "12px" }}>📁</div>
              <div style={{ fontSize: "15px", fontWeight: 600 }}>Drop financial documents here, or click to upload</div>
              <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "6px" }}>
                Supported: PDF, DOCX, XLSX, CSV (Max 100MB per file)
              </div>
            </div>

            {/* Document List Table */}
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-default)", textAlign: "left", color: "var(--text-muted)" }}>
                  <th style={{ padding: "8px" }}>Document Filename</th>
                  <th style={{ padding: "8px" }}>Version</th>
                  <th style={{ padding: "8px" }}>Pipeline Status</th>
                  <th style={{ padding: "8px" }}>Exceptions Flagged</th>
                  <th style={{ padding: "8px" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: "12px 8px", fontWeight: 500 }}>Apple_2024_10K_Annual_Report.pdf</td>
                  <td className="font-mono" style={{ padding: "12px 8px" }}>v1</td>
                  <td style={{ padding: "12px 8px" }}><TierBadge tier="V" /></td>
                  <td style={{ padding: "12px 8px", color: "var(--tier-verified)" }}>0 Exceptions</td>
                  <td style={{ padding: "12px 8px" }}>
                    <button onClick={() => setActiveTab("explorer")} style={{ background: "none", border: "none", color: "var(--tier-verified)", cursor: "pointer", fontWeight: 600 }}>
                      Inspect →
                    </button>
                  </td>
                </tr>
                <tr>
                  <td style={{ padding: "12px 8px", fontWeight: 500 }}>BetaHoldings_Q3_Restructuring.xlsx</td>
                  <td className="font-mono" style={{ padding: "12px 8px" }}>v2 (Corrected)</td>
                  <td style={{ padding: "12px 8px" }}><TierBadge tier="R" /></td>
                  <td style={{ padding: "12px 8px", color: "var(--tier-review)" }}>1 Discrepancy</td>
                  <td style={{ padding: "12px 8px" }}>
                    <button onClick={() => setActiveTab("review")} style={{ background: "none", border: "none", color: "var(--tier-review)", cursor: "pointer", fontWeight: 600 }}>
                      Review →
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
