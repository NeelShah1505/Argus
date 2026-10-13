"use client";

import React, { useState } from "react";
import { TierBadge, TierType } from "./TierBadge";

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
          transition: "border-color 150ms ease",
        }}
        onMouseEnter={(e) => (e.currentTarget.style.borderColor = "var(--tier-verified)")}
        onMouseLeave={(e) => (e.currentTarget.style.borderColor = "var(--border-default)")}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
          <span style={{ fontSize: "12px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
            {label}
          </span>
          <TierBadge tier={tier} />
        </div>

        <div className="font-mono" style={{ fontSize: "28px", fontWeight: 600, color: "var(--text-primary)" }}>
          {value}
        </div>

        {periodChange && (
          <div style={{ marginTop: "8px", fontSize: "12px", color: periodChange.startsWith("+") ? "var(--tier-verified)" : "var(--tier-failed)" }}>
            {periodChange} vs Prior Period
          </div>
        )}

        <div style={{ marginTop: "12px", fontSize: "11px", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: "4px" }}>
          <span>🔍 Click to inspect Lineage DAG</span>
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
            width: "380px",
            backgroundColor: "var(--bg-raised)",
            borderLeft: "1px solid var(--border-strong)",
            boxShadow: "-12px 0 32px rgba(0,0,0,0.7)",
            padding: "24px",
            zIndex: 2000,
            overflowY: "auto",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px", borderBottom: "1px solid var(--border-subtle)", paddingBottom: "12px" }}>
            <h3 style={{ fontSize: "16px", fontWeight: 600 }}>Deterministic Lineage DAG</h3>
            <button onClick={() => setDrawerOpen(false)} style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "18px" }}>
              ✕
            </button>
          </div>

          <div style={{ marginBottom: "20px" }}>
            <div style={{ fontSize: "12px", color: "var(--text-muted)" }}>Target Metric</div>
            <div className="font-mono" style={{ fontSize: "22px", fontWeight: 600, marginTop: "4px", color: "var(--tier-verified)" }}>
              {value}
            </div>
            <div style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "4px" }}>
              {formulaName}
            </div>
          </div>

          <div style={{ marginBottom: "20px" }}>
            <div style={{ fontSize: "12px", color: "var(--text-muted)", marginBottom: "8px", textTransform: "uppercase" }}>
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
                    padding: "10px 12px",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                  }}
                >
                  <div>
                    <div style={{ fontSize: "12px", fontWeight: 500 }}>{inp.name}</div>
                    <div className="font-mono" style={{ fontSize: "13px", color: "var(--text-primary)", marginTop: "2px" }}>
                      {inp.value}
                    </div>
                  </div>
                  <TierBadge tier={inp.tier} showLabel={false} />
                </div>
              ))}
            </div>
          </div>

          <div style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "16px", fontSize: "11px", color: "var(--text-muted)" }}>
            Attestation: Inputs validated deterministically via Decimal precision. Zero neural approximation.
          </div>
        </div>
      )}
    </>
  );
};
