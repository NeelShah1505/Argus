"use client";

import React, { useState } from "react";
import { TierBadge } from "./TierBadge";
import { IconSliders } from "./Icons";

export const ScenarioModeler: React.FC = () => {
  const [baseRev, setBaseRev] = useState(100000);
  const [growthRate, setGrowthRate] = useState(8.5);
  const [grossMargin, setGrossMargin] = useState(44.0);

  // Compute 3-year deterministic projection
  const y1Rev = baseRev * (1 + growthRate / 100);
  const y1Gp = y1Rev * (grossMargin / 100);

  const y2Rev = y1Rev * (1 + growthRate / 100);
  const y2Gp = y2Rev * (grossMargin / 100);

  const y3Rev = y2Rev * (1 + growthRate / 100);
  const y3Gp = y3Rev * (grossMargin / 100);

  return (
    <div style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--border-default)", borderRadius: "8px", padding: "28px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <IconSliders size={18} color="var(--accent)" />
            <h3 style={{ fontSize: "18px", fontWeight: 600 }}>Driver-Based Scenario Modeling</h3>
          </div>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "4px" }}>
            Deterministic operational projection. Mathematical scaling with explicit assumption attribution.
          </p>
        </div>
        <span
          style={{
            backgroundColor: "var(--bg-inset)",
            border: "1px dashed var(--tier-estimated)",
            color: "var(--tier-estimated)",
            padding: "4px 10px",
            borderRadius: "4px",
            fontSize: "11px",
            fontWeight: 500,
          }}
        >
          Sensitivity Model
        </span>
      </div>

      {/* Driver Controls */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "20px", marginBottom: "28px" }}>
        <div style={{ backgroundColor: "var(--bg-raised)", padding: "18px", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "10px" }}>
            <span style={{ color: "var(--text-secondary)" }}>Annual Revenue Growth</span>
            <span className="font-mono" style={{ fontWeight: 600, color: "var(--tier-verified)" }}>{growthRate}%</span>
          </div>
          <input
            type="range"
            min="-10"
            max="30"
            step="0.5"
            value={growthRate}
            onChange={(e) => setGrowthRate(parseFloat(e.target.value))}
            style={{ width: "100%", accentColor: "var(--tier-verified)", cursor: "pointer" }}
          />
        </div>

        <div style={{ backgroundColor: "var(--bg-raised)", padding: "18px", borderRadius: "6px", border: "1px solid var(--border-subtle)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "10px" }}>
            <span style={{ color: "var(--text-secondary)" }}>Target Gross Margin</span>
            <span className="font-mono" style={{ fontWeight: 600, color: "var(--tier-verified)" }}>{grossMargin}%</span>
          </div>
          <input
            type="range"
            min="20"
            max="70"
            step="0.5"
            value={grossMargin}
            onChange={(e) => setGrossMargin(parseFloat(e.target.value))}
            style={{ width: "100%", accentColor: "var(--tier-verified)", cursor: "pointer" }}
          />
        </div>
      </div>

      {/* Projection Table */}
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px", marginBottom: "24px" }}>
        <thead>
          <tr style={{ borderBottom: "1px solid var(--border-default)", textAlign: "left", color: "var(--text-muted)" }}>
            <th style={{ padding: "10px 8px" }}>Projection Period</th>
            <th style={{ padding: "10px 8px" }}>Projected Revenue</th>
            <th style={{ padding: "10px 8px" }}>Projected Gross Profit</th>
            <th style={{ padding: "10px 8px" }}>Accuracy Tier</th>
          </tr>
        </thead>
        <tbody>
          <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
            <td style={{ padding: "12px 8px" }}>Year 1 Pro Forma</td>
            <td className="font-mono" style={{ padding: "12px 8px", fontWeight: 600 }}>${y1Rev.toLocaleString(undefined, { maximumFractionDigits: 0 })}M</td>
            <td className="font-mono" style={{ padding: "12px 8px", color: "var(--tier-verified)" }}>${y1Gp.toLocaleString(undefined, { maximumFractionDigits: 0 })}M</td>
            <td style={{ padding: "12px 8px" }}><TierBadge tier="M" tolerance="Scenario" /></td>
          </tr>
          <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
            <td style={{ padding: "12px 8px" }}>Year 2 Pro Forma</td>
            <td className="font-mono" style={{ padding: "12px 8px", fontWeight: 600 }}>${y2Rev.toLocaleString(undefined, { maximumFractionDigits: 0 })}M</td>
            <td className="font-mono" style={{ padding: "12px 8px", color: "var(--tier-verified)" }}>${y2Gp.toLocaleString(undefined, { maximumFractionDigits: 0 })}M</td>
            <td style={{ padding: "12px 8px" }}><TierBadge tier="M" tolerance="Scenario" /></td>
          </tr>
          <tr>
            <td style={{ padding: "12px 8px" }}>Year 3 Pro Forma</td>
            <td className="font-mono" style={{ padding: "12px 8px", fontWeight: 600 }}>${y3Rev.toLocaleString(undefined, { maximumFractionDigits: 0 })}M</td>
            <td className="font-mono" style={{ padding: "12px 8px", color: "var(--tier-verified)" }}>${y3Gp.toLocaleString(undefined, { maximumFractionDigits: 0 })}M</td>
            <td style={{ padding: "12px 8px" }}><TierBadge tier="M" tolerance="Scenario" /></td>
          </tr>
        </tbody>
      </table>

      {/* Assumptions Ledger */}
      <div style={{ backgroundColor: "var(--bg-inset)", padding: "14px 18px", borderRadius: "4px", fontSize: "11.5px", color: "var(--text-muted)", border: "1px solid var(--border-subtle)" }}>
        <strong style={{ color: "var(--text-secondary)" }}>Assumptions Ledger:</strong> Base Revenue = $100,000M (FY2024 Verified). Compounding growth model: R_t = R_(t-1) * (1 + g). Zero stochastic drift.
      </div>
    </div>
  );
};
