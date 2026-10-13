"use client";

import React, { useState } from "react";
import { TierBadge, TierType } from "./TierBadge";

interface OverlayBox {
  id: string;
  label: string;
  tier: TierType;
  x0: number; // 0..1000
  y0: number;
  x1: number;
  y1: number;
}

export const DocumentExplorer: React.FC = () => {
  const [selectedBoxId, setSelectedBoxId] = useState<string>("box_1");

  const sampleBoxes: OverlayBox[] = [
    { id: "box_1", label: "Total Revenue: $391,036M", tier: "V", x0: 80, y0: 160, x1: 920, y1: 220 },
    { id: "box_2", label: "Cost of Sales: $(213,972)M", tier: "V", x0: 80, y0: 240, x1: 920, y1: 300 },
    { id: "box_3", label: "Gross Profit: $177,064M", tier: "V", x0: 80, y0: 320, x1: 920, y1: 380 },
    { id: "box_4", label: "Segment Delta Footnote", tier: "R", x0: 80, y0: 450, x1: 920, y1: 520 },
  ];

  const selectedBox = sampleBoxes.find((b) => b.id === selectedBoxId) || sampleBoxes[0];

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "240px 1fr 300px",
        gap: "16px",
        height: "580px",
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-default)",
        borderRadius: "8px",
        overflow: "hidden",
      }}
    >
      {/* Left Outline Tree */}
      <div style={{ borderRight: "1px solid var(--border-subtle)", padding: "16px", fontSize: "13px" }}>
        <div style={{ color: "var(--text-muted)", fontSize: "11px", textTransform: "uppercase", marginBottom: "12px" }}>
          Document Outline
        </div>
        <div style={{ display: "grid", gap: "8px" }}>
          <div style={{ padding: "6px 8px", backgroundColor: "var(--bg-raised)", borderRadius: "4px", color: "var(--text-primary)", fontWeight: 500 }}>
            📄 Consolidated Operations
          </div>
          <div style={{ padding: "6px 8px", color: "var(--text-secondary)", cursor: "pointer" }}>
            📄 Consolidated Balance Sheet
          </div>
          <div style={{ padding: "6px 8px", color: "var(--text-secondary)", cursor: "pointer" }}>
            📄 Cash Flows Statement
          </div>
          <div style={{ padding: "6px 8px", color: "var(--text-secondary)", cursor: "pointer" }}>
            📄 Note 4: Segment Reporting
          </div>
        </div>
      </div>

      {/* Center Canvas with Bounding Box Overlays */}
      <div
        style={{
          backgroundColor: "var(--bg-inset)",
          padding: "20px",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          overflow: "auto",
        }}
      >
        <div
          style={{
            width: "460px",
            height: "520px",
            backgroundColor: "#FFFFFF",
            borderRadius: "4px",
            boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
            position: "relative",
            padding: "24px",
            color: "#14181D",
          }}
        >
          <div style={{ fontSize: "14px", fontWeight: 700, marginBottom: "8px" }}>
            Consolidated Statement of Operations
          </div>
          <div style={{ fontSize: "10px", color: "#666", marginBottom: "16px" }}>
            (In Millions, Except Per Share Data)
          </div>

          {/* Render Bounding Box Overlays */}
          {sampleBoxes.map((box) => {
            const isSelected = box.id === selectedBoxId;
            const borderColor = box.tier === "V" ? "var(--tier-verified)" : "var(--tier-review)";
            const bgColor = box.tier === "V" ? "rgba(47, 214, 160, 0.15)" : "rgba(245, 181, 65, 0.15)";

            // Scale normalized [0, 1000] to canvas pixel space
            const top = (box.y0 / 1000) * 520;
            const height = ((box.y1 - box.y0) / 1000) * 520;

            return (
              <div
                key={box.id}
                onClick={() => setSelectedBoxId(box.id)}
                style={{
                  position: "absolute",
                  left: "24px",
                  right: "24px",
                  top: `${top}px`,
                  height: `${height}px`,
                  border: `2px solid ${borderColor}`,
                  backgroundColor: bgColor,
                  borderRadius: "3px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0 8px",
                  fontSize: "11px",
                  fontWeight: 600,
                  boxShadow: isSelected ? `0 0 10px ${borderColor}` : "none",
                  transition: "all 140ms ease-out",
                }}
              >
                <span>{box.label}</span>
                <TierBadge tier={box.tier} showLabel={false} />
              </div>
            );
          })}
        </div>
      </div>

      {/* Right Element Inspector */}
      <div style={{ borderLeft: "1px solid var(--border-subtle)", padding: "16px", fontSize: "12px" }}>
        <div style={{ color: "var(--text-muted)", fontSize: "11px", textTransform: "uppercase", marginBottom: "12px" }}>
          Selected Element Detail
        </div>
        <div style={{ display: "grid", gap: "10px" }}>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Element ID: </span>
            <span className="font-mono">{selectedBox.id}</span>
          </div>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Extracted Label: </span>
            <div style={{ fontWeight: 600, marginTop: "4px" }}>{selectedBox.label}</div>
          </div>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Accuracy Tier: </span>
            <div style={{ marginTop: "4px" }}>
              <TierBadge tier={selectedBox.tier} />
            </div>
          </div>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Coordinates: </span>
            <div className="font-mono" style={{ fontSize: "11px", marginTop: "4px", color: "var(--text-secondary)" }}>
              x: [{selectedBox.x0}, {selectedBox.x1}], y: [{selectedBox.y0}, {selectedBox.y1}]
            </div>
          </div>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Dual Consensus: </span>
            <div style={{ color: "var(--tier-verified)", marginTop: "4px" }}>
              pdfplumber + Docling (100% Agreement)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
