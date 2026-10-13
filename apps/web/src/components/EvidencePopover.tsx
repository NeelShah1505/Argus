"use client";

import React, { useState } from "react";
import { TierBadge, TierType } from "./TierBadge";

export interface EvidenceData {
  documentId: string;
  pageNumber: number;
  rawText: string;
  normalizedValue?: string;
  tier: TierType;
  enginesUsed: string[];
  agreementScore: number;
  validationsPassed: string[];
  bbox?: { x0: number; y0: number; x1: number; y1: number };
}

interface EvidencePopoverProps {
  children: React.ReactNode;
  evidence: EvidenceData;
  onOpenInDocument?: (docId: string, pageNum: number) => void;
}

export const EvidencePopover: React.FC<EvidencePopoverProps> = ({
  children,
  evidence,
  onOpenInDocument,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <span style={{ position: "relative", display: "inline-block" }}>
      <span
        onClick={() => setIsOpen(!isOpen)}
        style={{
          cursor: "pointer",
          borderBottom: "1px dotted var(--tier-verified)",
          fontFamily: "'IBM Plex Mono', monospace",
          fontVariantNumeric: "tabular-nums",
          paddingBottom: "1px",
        }}
        title="Click to view forensic evidence"
      >
        {children}
      </span>

      {isOpen && (
        <div
          style={{
            position: "absolute",
            bottom: "125%",
            left: "50%",
            transform: "translateX(-50%)",
            width: "320px",
            backgroundColor: "var(--bg-raised)",
            border: "1px solid var(--border-strong)",
            borderRadius: "8px",
            boxShadow: "0 12px 32px rgba(0,0,0,0.6)",
            padding: "16px",
            zIndex: 1000,
            color: "var(--text-primary)",
            fontSize: "12px",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "12px",
              borderBottom: "1px solid var(--border-subtle)",
              paddingBottom: "8px",
            }}
          >
            <span style={{ fontWeight: 600, color: "var(--text-secondary)", fontSize: "11px", textTransform: "uppercase" }}>
              Forensic Evidence Dossier
            </span>
            <TierBadge tier={evidence.tier} />
          </div>

          {/* Source Thumbnail Mockup with Boxed Region */}
          <div
            style={{
              height: "90px",
              backgroundColor: "var(--bg-inset)",
              borderRadius: "4px",
              position: "relative",
              overflow: "hidden",
              border: "1px solid var(--border-subtle)",
              marginBottom: "12px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <div style={{ color: "var(--text-muted)", fontSize: "11px" }}>
              Page {evidence.pageNumber} Canvas Render
            </div>
            {/* Boxed Region Overlay */}
            <div
              style={{
                position: "absolute",
                top: "25%",
                left: "30%",
                width: "40%",
                height: "50%",
                border: "2px solid var(--tier-verified)",
                backgroundColor: "var(--tier-verified-bg)",
                borderRadius: "2px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "11px",
                fontFamily: "'IBM Plex Mono', monospace",
                fontWeight: 600,
                color: "var(--tier-verified)",
              }}
            >
              {evidence.rawText}
            </div>
          </div>

          <div style={{ display: "grid", gap: "6px", marginBottom: "12px" }}>
            <div>
              <span style={{ color: "var(--text-muted)" }}>Raw Extracted: </span>
              <span className="font-mono" style={{ color: "var(--text-primary)", fontWeight: 600 }}>
                {evidence.rawText}
              </span>
            </div>
            <div>
              <span style={{ color: "var(--text-muted)" }}>Consensus: </span>
              <span>
                {evidence.enginesUsed.join(" + ")} ({(evidence.agreementScore * 100).toFixed(0)}%)
              </span>
            </div>
            {evidence.validationsPassed.length > 0 && (
              <div>
                <span style={{ color: "var(--text-muted)" }}>Validated Checks: </span>
                <span style={{ color: "var(--tier-verified)" }}>
                  {evidence.validationsPassed.join(", ")}
                </span>
              </div>
            )}
          </div>

          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "8px" }}>
            <button
              onClick={() => {
                setIsOpen(false);
                if (onOpenInDocument) onOpenInDocument(evidence.documentId, evidence.pageNumber);
              }}
              style={{
                padding: "6px 12px",
                borderRadius: "4px",
                backgroundColor: "var(--tier-verified-bg)",
                border: "1px solid var(--tier-verified)",
                color: "var(--tier-verified)",
                fontSize: "11px",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              Open in Document Viewer →
            </button>
            <button
              onClick={() => setIsOpen(false)}
              style={{
                background: "transparent",
                border: "none",
                color: "var(--text-muted)",
                fontSize: "11px",
                cursor: "pointer",
              }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </span>
  );
};
