"use client";

import React, { useState } from "react";
import { TierBadge, TierType } from "./TierBadge";
import { IconGitBranch, IconCross } from "./Icons";

interface MetricCardProps {
  label: string;
  value: string;
  tier: TierType;
  periodChange?: string;
  formulaName?: string;
  inputs?: Array<{ name: string; value: string; tier: TierType }>;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  tier,
  periodChange,
  formulaName = "Formula Registry Calculation",
  inputs = [],
}) => {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <>
      <div
        onClick={() => setDrawerOpen(true)}
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-default)",
          borderRadius: "6px",
          padding: "20px",
          cursor: "pointer",
          transition: "all 140ms ease-out",
          position: "relative",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = "var(--border-strong)";
          e.currentTarget.style.backgroundColor = "var(--bg-raised)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = "var(--border-default)";
          e.currentTarget.style.backgroundColor = "var(--bg-surface)";
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "10px" }}>
          <span style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 500 }}>
            {label}
          </span>
          <TierBadge tier={tier} />
        </div>

        <div className="font-mono" style={{ fontSize: "26px", fontWeight: 600, color: "var(--text-primary)", letterSpacing: "-0.02em" }}>
          {value}
        </div>

        {periodChange && (
          <div style={{ marginTop: "8px", fontSize: "12px", display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ color: periodChange.startsWith("+") ? "var(--tier-verified)" : "var(--tier-failed)", fontWeight: 500 }}>
              {periodChange}
            </span>
            <span style={{ color: "var(--text-muted)", fontSize: "11px" }}>vs Prior Period</span>
          </div>
        )}

        <div style={{ marginTop: "14px", fontSize: "11px", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "6px" }}>
          <IconGitBranch size={13} color="var(--text-muted)" />
          <span>Click to inspect Lineage DAG</span>
        </div>
      </div>

      {/* Lineage Drawer */}
      {drawerOpen && (
        <div
          style={{
            position: "fixed",
            top: 0,
            right: 0,
            bottom: 0,
            width: "400px",
            backgroundColor: "var(--bg-raised)",
            borderLeft: "1px solid var(--border-strong)",
            boxShadow: "-16px 0 40px rgba(0,0,0,0.7)",
            padding: "28px",
            zIndex: 2000,
            overflowY: "auto",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <IconGitBranch size={16} color="var(--accent)" />
              <h3 style={{ fontSize: "15px", fontWeight: 600 }}>Deterministic Lineage DAG</h3>
            </div>
            <button
              onClick={() => setDrawerOpen(false)}
              style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", display: "flex", alignItems: "center" }}
            >
              <IconCross size={16} color="var(--text-muted)" />
            </button>
          </div>

          <div style={{ marginBottom: "24px" }}>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>Target Metric</div>
            <div className="font-mono" style={{ fontSize: "22px", fontWeight: 600, marginTop: "4px", color: "var(--tier-verified)" }}>
              {value}
            </div>
            <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "4px", fontFamily: "'IBM Plex Mono', monospace" }}>
              {formulaName}
            </div>
          </div>

          <div style={{ marginBottom: "24px" }}>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "10px", textTransform: "uppercase", letterSpacing: "0.04em" }}>
              Input Primary Facts (DAG Roots)
            </div>
            <div style={{ display: "grid", gap: "8px" }}>
              {inputs.map((inp, idx) => (
                <div
                  key={idx}
                  style={{
                    backgroundColor: "var(--bg-inset)",
                    border: "1px solid var(--border-subtle)",
                    borderRadius: "4px",
                    padding: "12px 14px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <div>
                    <div style={{ fontSize: "12px", fontWeight: 500, color: "var(--text-primary)" }}>{inp.name}</div>
                    <div className="font-mono" style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "2px" }}>
                      {inp.value}
                    </div>
                  </div>
                  <TierBadge tier={inp.tier} showLabel={false} />
                </div>
              ))}
            </div>
          </div>

          <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "18px", fontSize: "11px", color: "var(--text-muted)", lineHeight: "1.5" }}>
            Attestation: Inputs validated deterministically via Decimal precision. Zero neural approximation.
          </div>
        </div>
      )}
    </>
  );
};
