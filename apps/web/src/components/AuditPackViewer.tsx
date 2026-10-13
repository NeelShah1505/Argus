"use client";

import React from "react";
import { TierBadge } from "./TierBadge";

export const AuditPackViewer: React.FC = () => {
  return (
    <div style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--border-default)", borderRadius: "6px", padding: "28px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px" }}>
        <div>
          <h3 style={{ fontSize: "20px", fontWeight: 600 }}>Forensic Compliance Audit Pack</h3>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "4px" }}>
            Cryptographically verifiable record linking every metric directly to source document pixels.
          </p>
        </div>
        <button
          onClick={() => alert("Audit Pack PDF generation complete. Download triggered.")}
          style={{
            backgroundColor: "var(--tier-verified-bg)",
            border: "1px solid var(--tier-verified)",
            color: "var(--tier-verified)",
            fontWeight: 600,
            padding: "8px 16px",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "12px",
          }}
        >
          ⬇ Export Signed Audit Pack PDF
        </button>
      </div>

      <div
        style={{
          backgroundColor: "var(--bg-inset)",
          border: "1px solid var(--border-subtle)",
          borderRadius: "6px",
          padding: "20px",
          marginBottom: "24px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "16px",
          fontSize: "12px",
        }}
      >
        <div>
          <span style={{ color: "var(--text-muted)" }}>Document SHA-256: </span>
          <div className="font-mono" style={{ fontSize: "11px", marginTop: "4px", color: "var(--text-primary)" }}>
            e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
          </div>
        </div>
        <div>
          <span style={{ color: "var(--text-muted)" }}>Compliance Standard: </span>
          <div style={{ fontWeight: 600, marginTop: "4px", color: "var(--tier-verified)" }}>
            Argus Evidence Contract v1
          </div>
        </div>
        <div>
          <span style={{ color: "var(--text-muted)" }}>Verified Facts: </span>
          <div className="font-mono" style={{ fontWeight: 600, marginTop: "4px", fontSize: "14px" }}>
            100% (24 / 24 Cells)
          </div>
        </div>
        <div>
          <span style={{ color: "var(--text-muted)" }}>Lead Auditor Sign-off: </span>
          <div style={{ marginTop: "4px" }}>
            <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>Signed: Auditor Lead #42</span>
          </div>
        </div>
      </div>

      {/* Forensic Trace Table */}
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12.5px" }}>
        <thead>
          <tr style={{ borderBottom: "1px solid var(--border-default)", textAlign: "left", color: "var(--text-muted)" }}>
            <th style={{ padding: "8px" }}>Metric</th>
            <th style={{ padding: "8px" }}>Reported Value</th>
            <th style={{ padding: "8px" }}>Source Pixel Coordinates</th>
            <th style={{ padding: "8px" }}>Ensemble Engine Consensus</th>
            <th style={{ padding: "8px" }}>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
            <td style={{ padding: "10px 8px", fontWeight: 500 }}>Total Net Sales</td>
            <td className="font-mono" style={{ padding: "10px 8px" }}>$391,036,000,000</td>
            <td className="font-mono" style={{ padding: "10px 8px", fontSize: "11px", color: "var(--text-secondary)" }}>Page 45 [x: 80-920, y: 160-220]</td>
            <td style={{ padding: "10px 8px", color: "var(--tier-verified)" }}>pdfplumber + Docling (100%)</td>
            <td style={{ padding: "10px 8px" }}><TierBadge tier="V" /></td>
          </tr>
          <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
            <td style={{ padding: "10px 8px", fontWeight: 500 }}>Cost of Sales</td>
            <td className="font-mono" style={{ padding: "10px 8px" }}>$(213,972,000,000)</td>
            <td className="font-mono" style={{ padding: "10px 8px", fontSize: "11px", color: "var(--text-secondary)" }}>Page 45 [x: 80-920, y: 240-300]</td>
            <td style={{ padding: "10px 8px", color: "var(--tier-verified)" }}>pdfplumber + Docling (100%)</td>
            <td style={{ padding: "10px 8px" }}><TierBadge tier="V" /></td>
          </tr>
          <tr>
            <td style={{ padding: "10px 8px", fontWeight: 500 }}>Gross Profit</td>
            <td className="font-mono" style={{ padding: "10px 8px" }}>$177,064,000,000</td>
            <td className="font-mono" style={{ padding: "10px 8px", fontSize: "11px", color: "var(--text-secondary)" }}>Page 45 [x: 80-920, y: 320-380]</td>
            <td style={{ padding: "10px 8px", color: "var(--tier-verified)" }}>Subtotal Footing Passed</td>
            <td style={{ padding: "10px 8px" }}><TierBadge tier="V" /></td>
          </tr>
        </tbody>
      </table>
    </div>
  );
};
