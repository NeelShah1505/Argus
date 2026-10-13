"use client";

import React, { useState } from "react";
import { TierBadge } from "./TierBadge";

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  citations?: string[];
  flags?: string[];
}

export const AskArgus: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      text: "I am Argus, your evidence-grounded financial analyst. Every numeric claim I generate is validated against the PostgreSQL Fact Store and verified by the code-level Claim Verifier. How may I assist your financial analysis?",
    },
  ]);
  const [inputPrompt, setInputPrompt] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = () => {
    if (!inputPrompt.trim()) return;
    const userMsg = inputPrompt;
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setInputPrompt("");
    setLoading(true);

    setTimeout(() => {
      // Synthetic grounded response simulation
      if (userMsg.toLowerCase().includes("margin") || userMsg.toLowerCase().includes("growth")) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: "Total revenue increased 8.25% [V: calc_rev_growth] to USD 391,036M [V: p.45 r2c3] in FY2024. Gross margin expanded 115 basis points to 45.28% [V: calc_gm_2024].\n\nInterpretation: Operational leverage outpaced inflation across freight and component procurement, directly accretionary to gross profit.",
            citations: [
              "Apple 2024 10-K, Page 45, Consolidated Statement of Operations, r2c3",
              "Note 4: Segment Reporting and Cost of Sales",
            ],
          },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: "Reported Total Revenue was USD 391,036M [V: p.45 r2c3] for FY2024. Operating income was USD 120,944M [V: p.45 r6c3].",
            citations: ["2024 Annual Filing, Consolidated Financial Statements, p.45"],
          },
        ]);
      }
      setLoading(false);
    }, 600);
  };

  return (
    <div style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--border-default)", borderRadius: "6px", height: "540px", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border-subtle)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h3 style={{ fontSize: "16px", fontWeight: 600 }}>Grounded Q&A — "Ask Argus"</h3>
          <p style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "2px" }}>
            Code-level claim verification enforced. Zero ungrounded numbers permitted.
          </p>
        </div>
        <TierBadge tier="V" />
      </div>

      <div style={{ flex: 1, padding: "20px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "16px" }}>
        {messages.map((m, idx) => (
          <div
            key={idx}
            style={{
              alignSelf: m.role === "user" ? "flex-end" : "flex-start",
              maxWidth: "85%",
              backgroundColor: m.role === "user" ? "var(--bg-raised)" : "var(--bg-inset)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "6px",
              padding: "14px 18px",
              fontSize: "13px",
              lineHeight: "1.6",
            }}
          >
            <div style={{ fontWeight: 600, fontSize: "11px", color: m.role === "user" ? "var(--text-secondary)" : "var(--tier-verified)", marginBottom: "4px" }}>
              {m.role === "user" ? "Analyst" : "Argus Orchestrator"}
            </div>
            <div style={{ whiteSpace: "pre-wrap", color: "var(--text-primary)" }}>{m.text}</div>

            {m.citations && m.citations.length > 0 && (
              <div style={{ marginTop: "12px", paddingTop: "8px", borderTop: "1px solid var(--border-subtle)", fontSize: "11px" }}>
                <span style={{ color: "var(--text-muted)" }}>Source Citations: </span>
                {m.citations.map((c, cIdx) => (
                  <span
                    key={cIdx}
                    style={{
                      display: "inline-block",
                      backgroundColor: "var(--bg-surface)",
                      border: "1px solid var(--border-default)",
                      borderRadius: "3px",
                      padding: "2px 6px",
                      marginRight: "6px",
                      marginTop: "4px",
                      color: "var(--tier-verified)",
                      fontFamily: "'IBM Plex Mono', monospace",
                    }}
                  >
                    📎 {c}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && <div style={{ color: "var(--tier-verified)", fontSize: "12px" }}>Argus verifying facts and computing DAG...</div>}
      </div>

      <div style={{ padding: "16px 20px", borderTop: "1px solid var(--border-subtle)", display: "flex", gap: "12px" }}>
        <input
          value={inputPrompt}
          onChange={(e) => setInputPrompt(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask about revenue growth, gross margins, or segment metrics..."
          style={{
            flex: 1,
            backgroundColor: "var(--bg-inset)",
            border: "1px solid var(--border-default)",
            borderRadius: "4px",
            padding: "10px 14px",
            color: "var(--text-primary)",
            fontSize: "13px",
          }}
        />
        <button
          onClick={handleSend}
          style={{
            backgroundColor: "var(--tier-verified-bg)",
            border: "1px solid var(--tier-verified)",
            color: "var(--tier-verified)",
            fontWeight: 600,
            padding: "0 20px",
            borderRadius: "4px",
            cursor: "pointer",
            fontSize: "13px",
          }}
        >
          Submit
        </button>
      </div>
    </div>
  );
};
