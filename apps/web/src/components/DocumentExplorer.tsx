"use client";

import React, { useState } from "react";
import { TierBadge, TierType } from "./TierBadge";
import { IconFile, IconLayers, IconCompass } from "./Icons";

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
  const [activePage, setActivePage] = useState<string>("ops");

  const sampleBoxes: OverlayBox[] = [
    { id: "box_1", label: "Total Revenue: $391,036M", tier: "V", x0: 80, y0: 160, x1: 920, y1: 220 },
    { id: "box_2", label: "Cost of Sales: $(213,972)M", tier: "V", x0: 80, y0: 240, x1: 920, y1: 300 },
    { id: "box_3", label: "Gross Profit: $177,064M", tier: "V", x0: 80, y0: 320, x1: 920, y1: 380 },
    { id: "box_4", label: "Segment Delta Footnote", tier: "R", x0: 80, y0: 450, x1: 920, y1: 520 },
  ];

  const selectedBox = sampleBoxes.find((b) => b.id === selectedBoxId) || sampleBoxes[0];

  const tocItems = [
    { id: "ops", title: "Consolidated Statement of Operations", page: 1 },
    { id: "bs", title: "Consolidated Balance Sheet", page: 2 },
    { id: "cf", title: "Cash Flows Statement", page: 3 },
    { id: "n4", title: "Note 4: Segment Reporting", page: 4 },
  ];

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "260px 1fr 300px",
        gap: "16px",
        height: "600px",
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-default)",
        borderRadius: "8px",
        overflow: "hidden",
      }}
    >
      {/* Left Outline Tree */}
      <div style={{ borderRight: "1px solid var(--border-subtle)", padding: "16px", fontSize: "12.5px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--text-muted)", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "14px" }}>
          <IconCompass size={13} color="var(--text-muted)" />
          <span>Document Outline</span>
        </div>
        <div style={{ display: "grid", gap: "4px" }}>
          {tocItems.map((item) => {
            const isActive = activePage === item.id;
            return (
              <div
                key={item.id}
                onClick={() => setActivePage(item.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                  padding: "8px 10px",
                  borderRadius: "4px",
                  backgroundColor: isActive ? "var(--bg-raised)" : "transparent",
                  color: isActive ? "var(--text-primary)" : "var(--text-secondary)",
                  fontWeight: isActive ? 500 : 400,
                  cursor: "pointer",
                  transition: "all 120ms ease",
                  borderLeft: isActive ? "2px solid var(--accent)" : "2px solid transparent",
                }}
              >
                <IconFile size={14} color={isActive ? "var(--accent)" : "var(--text-muted)"} />
                <span style={{ flex: 1, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{item.title}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Center Canvas with Bounding Box Overlays */}
      <div
        style={{
          backgroundColor: "var(--bg-inset)",
          padding: "24px",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          overflow: "auto",
        }}
      >
        <div
          style={{
            width: "480px",
            height: "540px",
            backgroundColor: "#0D1117",
            border: "1px solid var(--border-strong)",
            borderRadius: "6px",
            boxShadow: "0 12px 32px rgba(0,0,0,0.6)",
            position: "relative",
            padding: "28px",
            color: "#F0F4F8",
          }}
        >
          <div style={{ fontSize: "14px", fontWeight: 600, color: "#FFFFFF", marginBottom: "4px" }}>
            Consolidated Statement of Operations
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: "20px" }}>
            (In Millions, Except Per Share Data)
          </div>

          {/* Render Bounding Box Overlays */}
          {sampleBoxes.map((box) => {
            const isSelected = box.id === selectedBoxId;
            const borderColor = box.tier === "V" ? "var(--tier-verified)" : "var(--tier-review)";
            const bgColor = box.tier === "V" ? "rgba(16, 185, 129, 0.12)" : "rgba(245, 158, 11, 0.12)";

            // Scale normalized [0, 1000] to canvas pixel space
            const top = (box.y0 / 1000) * 540;
            const height = ((box.y1 - box.y0) / 1000) * 540;

            return (
              <div
                key={box.id}
                onClick={() => setSelectedBoxId(box.id)}
                style={{
                  position: "absolute",
                  left: "28px",
                  right: "28px",
                  top: `${top}px`,
                  height: `${height}px`,
                  border: `1.5px solid ${borderColor}`,
                  backgroundColor: bgColor,
                  borderRadius: "3px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "0 10px",
                  fontSize: "11px",
                  fontWeight: 500,
                  boxShadow: isSelected ? `0 0 12px ${borderColor}` : "none",
                  transition: "all 140ms ease-out",
                }}
              >
                <span className="font-mono">{box.label}</span>
                <TierBadge tier={box.tier} showLabel={false} />
              </div>
            );
          })}
        </div>
      </div>

      {/* Right Element Inspector */}
      <div style={{ borderLeft: "1px solid var(--border-subtle)", padding: "20px", fontSize: "12px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--text-muted)", fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: "16px" }}>
          <IconLayers size={13} color="var(--text-muted)" />
          <span>Selected Element</span>
        </div>

        <div style={{ display: "grid", gap: "14px" }}>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Element ID</span>
            <div className="font-mono" style={{ fontSize: "12px", marginTop: "3px", color: "var(--text-primary)" }}>{selectedBox.id}</div>
          </div>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Extracted Label</span>
            <div style={{ fontWeight: 600, marginTop: "3px", color: "var(--text-primary)" }}>{selectedBox.label}</div>
          </div>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Accuracy Tier</span>
            <div style={{ marginTop: "4px" }}>
              <TierBadge tier={selectedBox.tier} />
            </div>
          </div>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Coordinates [0-1000]</span>
            <div className="font-mono" style={{ fontSize: "11px", marginTop: "3px", color: "var(--text-secondary)" }}>
              x: [{selectedBox.x0}, {selectedBox.x1}], y: [{selectedBox.y0}, {selectedBox.y1}]
            </div>
          </div>
          <div>
            <span style={{ color: "var(--text-muted)" }}>Verification Method</span>
            <div style={{ color: "var(--tier-verified)", marginTop: "3px", fontSize: "11px", fontWeight: 500 }}>
              Dual Engine Consensus (100% Agreement)
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
