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
    { label: string; icon: string; bg: string; color: string; border: string }
  > = {
    V: {
      label: "Verified",
      icon: "✓",
      bg: "var(--tier-verified-bg)",
      color: "var(--tier-verified)",
      border: "1px solid var(--tier-verified)",
    },
    E: {
      label: "Extracted",
      icon: "•",
      bg: "var(--tier-extracted-bg)",
      color: "var(--tier-extracted)",
      border: "1px solid var(--tier-extracted)",
    },
    M: {
      label: tolerance ? `Estimated (${tolerance})` : "Estimated",
      icon: "≈",
      bg: "var(--tier-estimated-bg)",
      color: "var(--tier-estimated)",
      border: "1px dashed var(--tier-estimated)",
    },
    R: {
      label: "Needs Review",
      icon: "⚠",
      bg: "var(--tier-review-bg)",
      color: "var(--tier-review)",
      border: "1px solid var(--tier-review)",
    },
    F: {
      label: "Failed",
      icon: "✕",
      bg: "var(--tier-failed-bg)",
      color: "var(--tier-failed)",
      border: "1px solid var(--tier-failed)",
    },
  };

  const cfg = configs[tier] || configs.R;

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        padding: "2px 8px",
        borderRadius: "9999px",
        fontSize: "11px",
        fontFamily: "'IBM Plex Mono', monospace",
        fontWeight: 600,
        backgroundColor: cfg.bg,
        color: cfg.color,
        border: cfg.border,
        userSelect: "none",
        whiteSpace: "nowrap",
      }}
      title={`Accuracy Tier ${tier}: ${cfg.label}`}
    >
      <span>{cfg.icon}</span>
      {showLabel && <span>{cfg.label}</span>}
    </span>
  );
};
