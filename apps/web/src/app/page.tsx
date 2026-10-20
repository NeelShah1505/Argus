"use client";

import React, { useState, useEffect } from "react";
import { AnomalyFeed } from "../components/AnomalyFeed";
import { AskArgus } from "../components/AskArgus";
import { AuditPackViewer } from "../components/AuditPackViewer";
import { DocumentExplorer } from "../components/DocumentExplorer";
import { DocumentWorkbench } from "../components/DocumentWorkbench";
import { EvidencePopover } from "../components/EvidencePopover";
import { MetricCard } from "../components/MetricCard";
import { ReconciliationViewer } from "../components/ReconciliationViewer";
import { ReviewGrid } from "../components/ReviewGrid";
import { ScenarioModeler } from "../components/ScenarioModeler";
import { TierBadge } from "../components/TierBadge";
import {
  IconFile,
  IconUpload,
  IconShield,
  IconLayers,
  IconCompass,
  IconSliders,
  IconArrowRight,
  IconCheck,
  IconScan,
} from "../components/Icons";

export default function ArgusApp() {
  const [activeTab, setActiveTab] = useState<
    "workbench" | "insights" | "review" | "ask" | "reconciliation" | "scenarios" | "audit" | "inbox"
  >("workbench");

  const [apiConnected, setApiConnected] = useState<boolean | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadedDocs, setUploadedDocs] = useState<Array<{ id: string; filename: string; version: string; status: string; exceptions: string }>>([
    {
      id: "doc_apple_q4",
      filename: "Apple_FY24_Q4_Actual_Financial_Statements.pdf",
      version: "v1",
      status: "VERIFIED",
      exceptions: "4 Tables Extracted",
    },
    {
      id: "doc_annual_2024",
      filename: "Acme_Corp_Consolidated_Financials_2024.pdf",
      version: "v1",
      status: "VERIFIED",
      exceptions: "0 Exceptions",
    },
    {
      id: "doc_scanned_inv",
      filename: "Scanned_Logistics_Invoice.pdf",
      version: "v1",
      status: "VERIFIED",
      exceptions: "Tesseract OCR Active",
    },
  ]);

  // Check backend health
  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then((res) => setApiConnected(res.ok))
      .catch(() => setApiConnected(false));
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/api/v1/documents?tenant_id=tenant_demo", {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        const data = await res.json();
        setUploadedDocs((prev) => [
          {
            id: data.id,
            filename: data.filename,
            version: `v${data.version}`,
            status: "VERIFIED",
            exceptions: `${data.tables_extracted} Tables Extracted`,
          },
          ...prev,
        ]);
        alert(`Document '${file.name}' successfully ingested and canonicalized!`);
      } else {
        alert(`Upload error: ${res.statusText}`);
      }
    } catch (err) {
      alert(`Could not connect to backend at http://localhost:8000.`);
    } finally {
      setUploading(false);
    }
  };

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
      { id: "c_1_3", rowIdx: 1, colIdx: 3, rawText: "Verified", tier: "V" as const },
    ],
    [
      { id: "c_2_0", rowIdx: 2, colIdx: 0, rawText: "Cost of Goods Sold", tier: "V" as const },
      { id: "c_2_1", rowIdx: 2, colIdx: 1, rawText: "$(214,137)M", tier: "V" as const },
      { id: "c_2_2", rowIdx: 2, colIdx: 2, rawText: "$(213,972)M", tier: "V" as const },
      { id: "c_2_3", rowIdx: 2, colIdx: 3, rawText: "Verified", tier: "V" as const },
    ],
    [
      { id: "c_3_0", rowIdx: 3, colIdx: 0, rawText: "Gross Profit Subtotal", tier: "V" as const },
      { id: "c_3_1", rowIdx: 3, colIdx: 1, rawText: "$169,148M", tier: "V" as const },
      { id: "c_3_2", rowIdx: 3, colIdx: 2, rawText: "$177,064M", tier: "V" as const },
      { id: "c_3_3", rowIdx: 3, colIdx: 3, rawText: "Verified", tier: "V" as const },
    ],
    [
      { id: "c_4_0", rowIdx: 4, colIdx: 0, rawText: "Operating Expenses (R&D)", tier: "V" as const },
      { id: "c_4_1", rowIdx: 4, colIdx: 1, rawText: "$(29,915)M", tier: "V" as const },
      { id: "c_4_2", rowIdx: 4, colIdx: 2, rawText: "$(31,370)M", tier: "V" as const },
      { id: "c_4_3", rowIdx: 4, colIdx: 3, rawText: "Verified", tier: "V" as const },
    ],
    [
      { id: "c_5_0", rowIdx: 5, colIdx: 0, rawText: "Restructuring Note Delta", tier: "R" as const },
      { id: "c_5_1", rowIdx: 5, colIdx: 1, rawText: "$0M", tier: "V" as const },
      { id: "c_5_2", rowIdx: 5, colIdx: 2, rawText: "$1,450M", tier: "R" as const, candidates: { engineA: "$1,450M", engineB: "$1,150M" } },
      { id: "c_5_3", rowIdx: 5, colIdx: 3, rawText: "Disagreement", tier: "R" as const },
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

  const navItems = [
    { key: "workbench", label: "Extract & Document Workbench", icon: IconScan },
    { key: "review", label: "Review Console", icon: IconLayers },
    { key: "reconciliation", label: "Reconciliation", icon: IconCheck },
    { key: "insights", label: "Executive Analytics", icon: IconShield },
    { key: "scenarios", label: "Scenario Modeler", icon: IconSliders },
    { key: "audit", label: "Audit Pack Center", icon: IconFile },
    { key: "inbox", label: "Workspace Inbox", icon: IconUpload },
  ];

  return (
    <div style={{ minHeight: "100vh", backgroundColor: "var(--bg-canvas)", color: "var(--text-primary)" }}>
      {/* Top Header */}
      <header
        style={{
          borderBottom: "1px solid var(--border-default)",
          backgroundColor: "var(--bg-surface)",
          padding: "12px 28px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px" }}>
            <h1 className="font-serif" style={{ fontSize: "21px", fontWeight: 700, letterSpacing: "-0.02em", color: "var(--text-primary)" }}>
              Argus
            </h1>
            <span className="font-mono" style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              v2.4 Enterprise
            </span>
          </div>
          <span style={{ fontSize: "11px", color: "var(--text-muted)", paddingLeft: "14px", borderLeft: "1px solid var(--border-subtle)" }}>
            Autonomous Document Intelligence & Verification
          </span>
        </div>

        <div style={{ display: "flex", gap: "18px", alignItems: "center" }}>
          {/* API Status Indicator */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px", fontFamily: "'IBM Plex Mono', monospace" }}>
            <span
              style={{
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                backgroundColor: apiConnected ? "var(--tier-verified)" : "var(--tier-failed)",
                display: "inline-block",
              }}
            />
            <span style={{ color: "var(--text-muted)" }}>
              {apiConnected ? "API Connected (:8000)" : "Connecting API..."}
            </span>
          </div>

          {/* OCR Engine Active Badge */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px" }}>
            <span style={{ color: "var(--text-muted)" }}>OCR Engine:</span>
            <span style={{ color: "var(--accent)", fontWeight: 600 }} className="font-mono">Tesseract 5.5.3 Active</span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "11px" }}>
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
          gap: "4px",
          padding: "6px 28px",
          borderBottom: "1px solid var(--border-subtle)",
          backgroundColor: "var(--bg-surface)",
          overflowX: "auto",
        }}
      >
        {navItems.map((t) => {
          const isActive = activeTab === t.key;
          const IconComp = t.icon;
          return (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key as any)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "8px",
                padding: "8px 14px",
                borderRadius: "4px",
                border: "none",
                backgroundColor: isActive ? "var(--bg-raised)" : "transparent",
                color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                fontWeight: isActive ? 600 : 400,
                cursor: "pointer",
                fontSize: "12.5px",
                transition: "all 120ms ease-out",
                borderBottom: isActive ? "2px solid var(--accent)" : "2px solid transparent",
              }}
            >
              <IconComp size={14} color={isActive ? "var(--accent)" : "var(--text-muted)"} />
              <span>{t.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Main Body Content */}
      <main style={{ maxWidth: activeTab === "workbench" ? "100%" : "1400px", margin: "0 auto", padding: activeTab === "workbench" ? "14px 20px" : "32px" }}>
        {/* TAB 0: Master Document Workbench */}
        {activeTab === "workbench" && <DocumentWorkbench />}
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
                borderRadius: "8px",
                padding: "24px",
              }}
            >
              <h3 style={{ fontSize: "15px", fontWeight: 600, marginBottom: "8px", color: "var(--text-primary)" }}>
                The Forensic Trace Guarantee
              </h3>
              <p style={{ fontSize: "13px", color: "var(--text-secondary)", lineHeight: "1.6" }}>
                Hover or click any value in Argus to invoke the cryptographic Evidence Dossier. For example, our verified operating income of{" "}
                <EvidencePopover
                  evidence={{
                    documentId: "doc_annual_2024",
                    pageNumber: 1,
                    rawText: "$120,944M",
                    tier: "V",
                    enginesUsed: ["pdfplumber", "PyMuPDF"],
                    agreementScore: 1.0,
                    validationsPassed: ["Subtotal Footing", "Balance Sheet Identity"],
                  }}
                  onOpenInDocument={() => setActiveTab("workbench")}
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


        {/* TAB 3: Review Console */}
        {activeTab === "review" && (
          <div style={{ display: "grid", gap: "20px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h2 style={{ fontSize: "18px", fontWeight: 600 }}>Review Console — High-Speed Exception Resolution</h2>
                <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "4px" }}>
                  Navigate with keyboard: <kbd>j</kbd>/<kbd>k</kbd> rows, <kbd>E</kbd> edit, <kbd>Enter</kbd> save, <kbd>A</kbd> approve. Corrections generate immutable audit events.
                </p>
              </div>
              <TierBadge tier="R" />
            </div>

            <ReviewGrid
              initialRows={sampleGrid}
              onCellCorrection={(cellId, newText) => {
                alert(`Cell ${cellId} corrected to '${newText}'. Document version bumped to v2.`);
              }}
            />
          </div>
        )}

        {/* TAB 4: Ask Argus */}
        {activeTab === "ask" && (
          <div>
            <AskArgus />
          </div>
        )}

        {/* TAB 5: Financial Reconciliation (Phase 9) */}
        {activeTab === "reconciliation" && (
          <div>
            <ReconciliationViewer />
          </div>
        )}

        {/* TAB 6: Scenario Modeler */}
        {activeTab === "scenarios" && (
          <div>
            <ScenarioModeler />
          </div>
        )}

        {/* TAB 7: Compliance Audit Pack */}
        {activeTab === "audit" && (
          <div>
            <AuditPackViewer />
          </div>
        )}

        {/* TAB 8: Workspace Document Inbox */}
        {activeTab === "inbox" && (
          <div style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--border-default)", borderRadius: "8px", padding: "28px" }}>
            <h2 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "6px" }}>Workspace Document Inbox</h2>
            <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginBottom: "24px" }}>
              Upload corporate filings in native PDF, DOCX, XLSX, or CSV format. Deduplicated via SHA-256 and routed through multi-engine consensus.
            </p>

            {/* Drag & Drop Upload Zone */}
            <div
              style={{
                border: "1.5px dashed var(--border-strong)",
                borderRadius: "8px",
                padding: "44px 20px",
                textAlign: "center",
                backgroundColor: "var(--bg-inset)",
                marginBottom: "28px",
                position: "relative",
              }}
            >
              <input
                type="file"
                accept=".pdf,.docx,.xlsx,.csv"
                onChange={handleFileUpload}
                disabled={uploading}
                style={{
                  position: "absolute",
                  inset: 0,
                  opacity: 0,
                  cursor: uploading ? "not-allowed" : "pointer",
                }}
              />
              <div style={{ display: "flex", justifyContent: "center", marginBottom: "14px" }}>
                <IconUpload size={32} color="var(--accent)" />
              </div>
              <div style={{ fontSize: "14px", fontWeight: 600, color: "var(--text-primary)" }}>
                {uploading ? "Ingesting and canonicalizing document..." : "Click or drop financial documents here to upload"}
              </div>
              <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "6px" }}>
                Supported Formats: PDF, DOCX, XLSX, CSV (Max 100MB per file)
              </div>
            </div>

            {/* Document List Table */}
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12.5px" }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border-default)", textAlign: "left", color: "var(--text-muted)" }}>
                  <th style={{ padding: "10px 8px" }}>Document Filename</th>
                  <th style={{ padding: "10px 8px" }}>Version</th>
                  <th style={{ padding: "10px 8px" }}>Pipeline Status</th>
                  <th style={{ padding: "10px 8px" }}>Extracted Stats</th>
                  <th style={{ padding: "10px 8px" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {uploadedDocs.map((doc, idx) => (
                  <tr key={idx} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                    <td style={{ padding: "12px 8px", fontWeight: 500 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                        <IconFile size={14} color="var(--text-muted)" />
                        <span>{doc.filename}</span>
                      </div>
                    </td>
                    <td className="font-mono" style={{ padding: "12px 8px", fontSize: "11px", color: "var(--text-secondary)" }}>
                      {doc.version}
                    </td>
                    <td style={{ padding: "12px 8px" }}>
                      <TierBadge tier={doc.status === "VERIFIED" ? "V" : "R"} />
                    </td>
                    <td style={{ padding: "12px 8px", color: "var(--tier-verified)", fontSize: "11px" }}>
                      {doc.exceptions}
                    </td>
                    <td style={{ padding: "12px 8px" }}>
                      <button
                        onClick={() => setActiveTab("workbench")}
                        style={{
                          background: "none",
                          border: "none",
                          color: "var(--accent)",
                          cursor: "pointer",
                          fontWeight: 500,
                          fontSize: "12px",
                          display: "flex",
                          alignItems: "center",
                          gap: "4px",
                        }}
                      >
                        <span>Inspect</span>
                        <IconArrowRight size={12} color="var(--accent)" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
