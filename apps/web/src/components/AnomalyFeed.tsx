"use client";

import React from "react";
import { IconAlert, IconArrowRight } from "./Icons";

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
  const severityConfigs = {
    Critical: { color: "var(--tier-failed)", bg: "var(--tier-failed-bg)", border: "1px solid rgba(244, 63, 94, 0.25)" },
    High: { color: "var(--tier-review)", bg: "var(--tier-review-bg)", border: "1px solid rgba(245, 158, 11, 0.25)" },
    Medium: { color: "var(--tier-extracted)", bg: "var(--tier-extracted-bg)", border: "1px solid rgba(96, 165, 250, 0.25)" },
    Low: { color: "var(--text-muted)", bg: "var(--bg-inset)", border: "1px solid var(--border-subtle)" },
  };

  return (
    <div style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--border-default)", borderRadius: "8px", padding: "24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "18px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <IconAlert size={16} color="var(--tier-review)" />
          <h3 style={{ fontSize: "15px", fontWeight: 600 }}>Active Inconsistencies & Anomaly Feed</h3>
        </div>
        <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "'IBM Plex Mono', monospace" }}>
          {anomalies.length} Flagged Exceptions
        </span>
      </div>

      <div style={{ display: "grid", gap: "10px" }}>
        {anomalies.map((anom, idx) => {
          const cfg = severityConfigs[anom.severity] || severityConfigs.Medium;
          return (
            <div
              key={idx}
              style={{
                backgroundColor: "var(--bg-raised)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "6px",
                padding: "14px 18px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "16px",
              }}
            >
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span
                    style={{
                      fontSize: "10px",
                      fontWeight: 600,
                      fontFamily: "'IBM Plex Mono', monospace",
                      color: cfg.color,
                      backgroundColor: cfg.bg,
                      border: cfg.border,
                      padding: "2px 6px",
                      borderRadius: "3px",
                      textTransform: "uppercase",
                    }}
                  >
                    {anom.severity}
                  </span>
                  <span style={{ fontSize: "13px", fontWeight: 600, color: "var(--text-primary)" }}>
                    {anom.ruleName}
                  </span>
                  <span className="font-mono" style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    ({anom.ruleId})
                  </span>
                </div>
                <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "4px", lineHeight: "1.5" }}>
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
                  fontWeight: 500,
                  cursor: "pointer",
                  whiteSpace: "nowrap",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  transition: "border-color 120ms ease",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--border-strong)")}
                onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border-default)")}
              >
                <span>Drilldown</span>
                <IconArrowRight size={12} color="var(--text-muted)" />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
};
