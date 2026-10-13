"use client";

import React from "react";

export interface AnomalyItem {
  ruleId: string;
  ruleName: string;
  severity: "Critical" | "High" | "Medium" | "Low";
  description: string;
  affectedElement: string;
}

interface AnomalyFeedProps {
  anomalies: AnomalyItem[];
  onDrilldown?: (elementId: string) => void;
}

export const AnomalyFeed: React.FC<AnomalyFeedProps> = ({ anomalies, onDrilldown }) => {
  const severityColors = {
    Critical: "var(--tier-failed)",
    High: "var(--tier-review)",
    Medium: "#5B9CFF",
    Low: "var(--text-muted)",
  };

  return (
    <div style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--border-default)", borderRadius: "6px", padding: "20px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <h3 style={{ fontSize: "15px", fontWeight: 600 }}>Active Inconsistencies & Anomaly Feed</h3>
        <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>{anomalies.length} Flagged Items</span>
      </div>

      <div style={{ display: "grid", gap: "10px" }}>
        {anomalies.map((anom, idx) => (
          <div
            key={idx}
            style={{
              backgroundColor: "var(--bg-raised)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "4px",
              padding: "12px 16px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: 700,
                    color: severityColors[anom.severity],
                    textTransform: "uppercase",
                  }}
                >
                  [{anom.severity}]
                </span>
                <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)" }}>
                  {anom.ruleName} ({anom.ruleId})
                </span>
              </div>
              <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "4px" }}>
                {anom.description}
              </div>
            </div>

            <button
              onClick={() => onDrilldown && onDrilldown(anom.affectedElement)}
              style={{
                backgroundColor: "var(--bg-inset)",
                border: "1px solid var(--border-default)",
                color: "var(--text-primary)",
                padding: "6px 12px",
                borderRadius: "4px",
                fontSize: "11px",
                cursor: "pointer",
                whiteSpace: "nowrap",
              }}
            >
              Drilldown to Evidence →
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
