import React from "react";

export default function HomePage() {
  return (
    <main style={{ minHeight: "100vh", padding: "48px 32px", maxWidth: "1280px", margin: "0 auto" }}>
      <header style={{ marginBottom: "40px", borderBottom: "1px solid var(--border-default)", paddingBottom: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
          <div>
            <h1 className="font-serif" style={{ fontSize: "36px", fontWeight: 500, color: "var(--text-primary)" }}>
              Argus
            </h1>
            <p style={{ color: "var(--text-secondary)", marginTop: "6px", fontSize: "14px" }}>
              Evidence-First Financial Document Intelligence Platform
            </p>
          </div>
          <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            <span
              style={{
                fontSize: "12px",
                padding: "4px 10px",
                borderRadius: "9999px",
                backgroundColor: "var(--tier-verified-bg)",
                color: "var(--tier-verified)",
                border: "1px solid var(--tier-verified)",
                fontWeight: 600,
              }}
            >
              ✓ System Online
            </span>
            <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>v1.0.0-core</span>
          </div>
        </div>
      </header>

      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "20px", marginBottom: "40px" }}>
        <div
          style={{
            backgroundColor: "var(--bg-surface)",
            border: "1px solid var(--border-default)",
            borderRadius: "6px",
            padding: "20px",
          }}
        >
          <div style={{ fontSize: "12px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            The Evidence Contract
          </div>
          <div style={{ fontSize: "18px", fontWeight: 600, marginTop: "8px", color: "var(--text-primary)" }}>
            Zero Silent Errors
          </div>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "8px", lineHeight: "1.5" }}>
            Every reported numeral is verified by dual-engine consensus and accounting identities, or visually flagged for review.
          </p>
        </div>

        <div
          style={{
            backgroundColor: "var(--bg-surface)",
            border: "1px solid var(--border-default)",
            borderRadius: "6px",
            padding: "20px",
          }}
        >
          <div style={{ fontSize: "12px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Forensic Provenance
          </div>
          <div style={{ fontSize: "18px", fontWeight: 600, marginTop: "8px", color: "var(--text-primary)" }}>
            2-Click Pixel Trace
          </div>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "8px", lineHeight: "1.5" }}>
            Every data point links directly to its source bounding box coordinates and original page render.
          </p>
        </div>

        <div
          style={{
            backgroundColor: "var(--bg-surface)",
            border: "1px solid var(--border-default)",
            borderRadius: "6px",
            padding: "20px",
          }}
        >
          <div style={{ fontSize: "12px", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Deterministic Calculation
          </div>
          <div style={{ fontSize: "18px", fontWeight: 600, marginTop: "8px", color: "var(--text-primary)" }}>
            Zero LLM Hallucinations
          </div>
          <p style={{ fontSize: "13px", color: "var(--text-secondary)", marginTop: "8px", lineHeight: "1.5" }}>
            Calculations executed via typed Decimal formulas. Server-side claim verifiers strip ungrounded numbers.
          </p>
        </div>
      </section>

      <section
        style={{
          backgroundColor: "var(--bg-surface)",
          border: "1px solid var(--border-default)",
          borderRadius: "6px",
          padding: "24px",
        }}
      >
        <h2 style={{ fontSize: "16px", fontWeight: 600, marginBottom: "16px" }}>Accuracy Tier Language</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ display: "inline-block", width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "var(--tier-verified)" }} />
            <span style={{ fontSize: "13px", color: "var(--text-primary)" }}>Tier V (Verified)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ display: "inline-block", width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "var(--tier-extracted)" }} />
            <span style={{ fontSize: "13px", color: "var(--text-primary)" }}>Tier E (Extracted)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ display: "inline-block", width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "var(--tier-estimated)" }} />
            <span style={{ fontSize: "13px", color: "var(--text-primary)" }}>Tier M (Estimated ±Tol)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ display: "inline-block", width: "10px", height: "10px", borderRadius: "50%", backgroundColor: "var(--tier-review)" }} />
            <span style={{ fontSize: "13px", color: "var(--text-primary)" }}>Tier R (Needs Review)</span>
          </div>
        </div>
      </section>
    </main>
  );
}
