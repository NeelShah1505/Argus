import React from "react";

export type TierType = "V" | "E" | "M" | "R" | "F";

interface TierBadgeProps {
  tier: TierType;
  tolerance?: string;
  showLabel?: boolean;
}

export const TierBadge: React.FC<TierBadgeProps> = ({ tier, tolerance, showLabel = true }) => {
  const configs: Record<
    TierType,
    { label: string; code: string; bg: string; color: string; border: string; dotColor: string }
  > = {
    V: {
      label: "Verified",
      code: "VERIFIED",
      bg: "rgba(16, 185, 129, 0.08)",
      color: "#10B981",
      border: "1px solid rgba(16, 185, 129, 0.25)",
      dotColor: "#10B981",
    },
    E: {
      label: "Extracted",
      code: "EXTRACTED",
      bg: "rgba(96, 165, 250, 0.08)",
      color: "#60A5FA",
      border: "1px solid rgba(96, 165, 250, 0.25)",
      dotColor: "#60A5FA",
    },
    M: {
      label: tolerance ? `Estimated (${tolerance})` : "Estimated",
      code: "ESTIMATED",
      bg: "rgba(167, 139, 250, 0.08)",
      color: "#A78BFA",
      border: "1px dashed rgba(167, 139, 250, 0.35)",
      dotColor: "#A78BFA",
    },
    R: {
      label: "Needs Review",
      code: "REVIEW",
      bg: "rgba(245, 158, 11, 0.08)",
      color: "#F59E0B",
      border: "1px solid rgba(245, 158, 11, 0.25)",
      dotColor: "#F59E0B",
    },
    F: {
      label: "Failed",
      code: "FAILED",
      bg: "rgba(244, 63, 94, 0.08)",
      color: "#F43F5E",
      border: "1px solid rgba(244, 63, 94, 0.25)",
      dotColor: "#F43F5E",
    },
  };

  const cfg = configs[tier] || configs.R;

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        padding: showLabel ? "3px 9px" : "3px 6px",
        borderRadius: "4px",
        fontSize: "11px",
        fontFamily: "'IBM Plex Mono', monospace",
        fontWeight: 500,
        letterSpacing: "0.02em",
        backgroundColor: cfg.bg,
        color: cfg.color,
        border: cfg.border,
        userSelect: "none",
        whiteSpace: "nowrap",
      }}
      title={`Accuracy Tier ${tier}: ${cfg.label}`}
    >
      <span
        style={{
          width: "5px",
          height: "5px",
          borderRadius: "50%",
          backgroundColor: cfg.dotColor,
          display: "inline-block",
        }}
      />
      {showLabel ? (
        <span>{cfg.label}</span>
      ) : (
        <span>{tier}</span>
      )}
    </span>
  );
};
