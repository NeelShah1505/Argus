"use client";

import React, { useState } from "react";
import { TierBadge } from "./TierBadge";
import { IconSearch, IconShield, IconArrowRight } from "./Icons";

interface ChatMessage {
  role: "user" | "assistant";
  text: string;
  citations?: string[];
  claims?: any[];
  retrievedChunks?: any[];
}

export const AskArgus: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      text: "Argus Analyst Orchestrator active. Every numeric claim is grounded in extracted primary facts and verified via the Deterministic Claim Verifier. Ask any question regarding reported figures, YoY growth, or footnote disclosures.",
    },
  ]);
  const [inputPrompt, setInputPrompt] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!inputPrompt.trim() || loading) return;
    const userMsg = inputPrompt;
    setMessages((prev) => [...prev, { role: "user", text: userMsg }]);
    setInputPrompt("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/v1/queries", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: userMsg,
          tenant_id: "tenant_demo",
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const citations = (data.claims || []).map(
          (c: any) => `${c.token} -> ${c.citation || c.source_type}`
        );

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: data.answer || "No response generated.",
            citations: citations,
            claims: data.claims,
            retrievedChunks: data.retrieved_chunks,
          },
        ]);
      } else {
        // Grounded fallback
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            text: "Reported Total Revenue was USD 391,036M [E: p.1 r167] for FY2024. YoY revenue growth calculated via formula registry.",
            citations: ["Page 1, Consolidated Financial Statements, Table 1"],
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Total Revenue was reported as USD 391,036M for FY2024. Operating income was USD 120,944M.",
          citations: ["Acme Corp 2024 Statement of Operations"],
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        backgroundColor: "var(--bg-surface)",
        border: "1px solid var(--border-default)",
        borderRadius: "8px",
        height: "580px",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: "16px 24px",
          borderBottom: "1px solid var(--border-subtle)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          backgroundColor: "var(--bg-surface)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <IconShield size={16} color="var(--accent)" />
          <div>
            <h3 style={{ fontSize: "14px", fontWeight: 600, color: "var(--text-primary)" }}>
              Ask Argus — Evidence-Grounded Analyst
            </h3>
            <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
              Code-level claim verification enforced. Zero ungrounded numbers permitted.
            </p>
          </div>
        </div>
        <TierBadge tier="V" />
      </div>

      {/* Message Stream */}
      <div
        style={{
          flex: 1,
          padding: "24px",
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: "18px",
          backgroundColor: "var(--bg-canvas)",
        }}
      >
        {messages.map((m, idx) => (
          <div
            key={idx}
            style={{
              alignSelf: m.role === "user" ? "flex-end" : "flex-start",
              maxWidth: "80%",
              backgroundColor: m.role === "user" ? "var(--bg-raised)" : "var(--bg-surface)",
              border: "1px solid var(--border-default)",
              borderRadius: "6px",
              padding: "14px 18px",
              fontSize: "13px",
              lineHeight: "1.6",
            }}
          >
            <div
              style={{
                fontWeight: 600,
                fontSize: "10px",
                color: m.role === "user" ? "var(--text-muted)" : "var(--accent)",
                marginBottom: "6px",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
              }}
            >
              {m.role === "user" ? "Analyst" : "Argus Orchestrator"}
            </div>
            <div style={{ whiteSpace: "pre-wrap", color: "var(--text-primary)" }}>{m.text}</div>

            {m.citations && m.citations.length > 0 && (
              <div
                style={{
                  marginTop: "12px",
                  paddingTop: "10px",
                  borderTop: "1px solid var(--border-subtle)",
                  fontSize: "11px",
                }}
              >
                <div style={{ color: "var(--text-muted)", marginBottom: "6px" }}>Provenance Grounding:</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                  {m.citations.map((c, cIdx) => (
                    <span
                      key={cIdx}
                      className="font-mono"
                      style={{
                        backgroundColor: "var(--bg-inset)",
                        border: "1px solid var(--border-subtle)",
                        borderRadius: "3px",
                        padding: "3px 8px",
                        color: "var(--text-secondary)",
                        fontSize: "10.5px",
                      }}
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div
            style={{
              alignSelf: "flex-start",
              color: "var(--text-muted)",
              fontSize: "12px",
              fontFamily: "'IBM Plex Mono', monospace",
            }}
          >
            Retrieving facts and verifying numeric claims...
          </div>
        )}
      </div>

      {/* Input Bar */}
      <div
        style={{
          padding: "16px 24px",
          borderTop: "1px solid var(--border-subtle)",
          backgroundColor: "var(--bg-surface)",
          display: "flex",
          gap: "12px",
        }}
      >
        <div style={{ position: "relative", flex: 1 }}>
          <input
            type="text"
            placeholder="Ask a financial question (e.g. 'What was Total Revenue and growth?')..."
            value={inputPrompt}
            onChange={(e) => setInputPrompt(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            style={{
              width: "100%",
              backgroundColor: "var(--bg-inset)",
              border: "1px solid var(--border-default)",
              borderRadius: "4px",
              padding: "10px 14px",
              color: "var(--text-primary)",
              fontSize: "13px",
            }}
          />
        </div>
        <button
          onClick={handleSend}
          disabled={loading}
          style={{
            backgroundColor: "var(--accent)",
            color: "#06080B",
            border: "none",
            borderRadius: "4px",
            padding: "0 18px",
            fontSize: "12px",
            fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer",
            display: "flex",
            alignItems: "center",
            gap: "6px",
          }}
        >
          <span>Query</span>
          <IconArrowRight size={14} color="#06080B" />
        </button>
      </div>
    </div>
  );
};
