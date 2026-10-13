"use client";

import React, { useEffect, useState } from "react";
import { TierBadge, TierType } from "./TierBadge";

export interface GridCell {
  id: string;
  rowIdx: number;
  colIdx: number;
  rawText: string;
  normalizedValue?: string;
  tier: TierType;
  isHeader?: boolean;
  candidates?: { engineA?: string; engineB?: string };
}

interface ReviewGridProps {
  initialRows: GridCell[][];
  onCellCorrection?: (cellId: string, newText: string) => void;
  onCellSelect?: (cell: GridCell) => void;
}

export const ReviewGrid: React.FC<ReviewGridProps> = ({
  initialRows,
  onCellCorrection,
  onCellSelect,
}) => {
  const [grid, setGrid] = useState<GridCell[][]>(initialRows);
  const [activeRow, setActiveRow] = useState(1);
  const [activeCol, setActiveCol] = useState(1);
  const [editingCellId, setEditingCellId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const numRows = grid.length;
  const numCols = grid[0]?.length || 0;

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (editingCellId) {
        if (e.key === "Enter") {
          e.preventDefault();
          commitEdit();
        } else if (e.key === "Escape") {
          setEditingCellId(null);
        }
        return;
      }

      if (e.key === "j" || e.key === "ArrowDown") {
        e.preventDefault();
        setActiveRow((r) => Math.min(r + 1, numRows - 1));
      } else if (e.key === "k" || e.key === "ArrowUp") {
        e.preventDefault();
        setActiveRow((r) => Math.max(r - 1, 0));
      } else if (e.key === "l" || e.key === "ArrowRight") {
        e.preventDefault();
        setActiveCol((c) => Math.min(c + 1, numCols - 1));
      } else if (e.key === "h" || e.key === "ArrowLeft") {
        e.preventDefault();
        setActiveCol((c) => Math.max(c - 1, 0));
      } else if (e.key === "e" || e.key === "E") {
        e.preventDefault();
        startEdit();
      } else if (e.key === "a" || e.key === "A") {
        e.preventDefault();
        approveActiveCell();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [editingCellId, activeRow, activeCol, numRows, numCols, grid]);

  const activeCell = grid[activeRow]?.[activeCol];

  useEffect(() => {
    if (activeCell && onCellSelect) {
      onCellSelect(activeCell);
    }
  }, [activeRow, activeCol]);

  const startEdit = () => {
    if (activeCell) {
      setEditingCellId(activeCell.id);
      setEditValue(activeCell.rawText);
    }
  };

  const commitEdit = () => {
    if (!editingCellId) return;
    const updated = grid.map((row) =>
      row.map((cell) => {
        if (cell.id === editingCellId) {
          return {
            ...cell,
            rawText: editValue,
            tier: "V" as TierType,
          };
        }
        return cell;
      })
    );
    setGrid(updated);
    if (onCellCorrection) {
      onCellCorrection(editingCellId, editValue);
    }
    setEditingCellId(null);
  };

  const approveActiveCell = () => {
    if (!activeCell) return;
    const updated = grid.map((row) =>
      row.map((cell) => {
        if (cell.id === activeCell.id) {
          return { ...cell, tier: "V" as TierType };
        }
        return cell;
      })
    );
    setGrid(updated);
  };

  return (
    <div style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--border-default)", borderRadius: "6px" }}>
      {/* Shortcut bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "8px 16px",
          borderBottom: "1px solid var(--border-subtle)",
          fontSize: "12px",
          color: "var(--text-muted)",
        }}
      >
        <div style={{ display: "flex", gap: "12px" }}>
          <span><kbd style={{ padding: "2px 5px", background: "var(--bg-inset)", border: "1px solid var(--border-default)", borderRadius: "3px" }}>j/k</kbd> Row</span>
          <span><kbd style={{ padding: "2px 5px", background: "var(--bg-inset)", border: "1px solid var(--border-default)", borderRadius: "3px" }}>h/l</kbd> Cell</span>
          <span><kbd style={{ padding: "2px 5px", background: "var(--bg-inset)", border: "1px solid var(--border-default)", borderRadius: "3px" }}>E</kbd> Edit Inline</span>
          <span><kbd style={{ padding: "2px 5px", background: "var(--bg-inset)", border: "1px solid var(--border-default)", borderRadius: "3px" }}>Enter</kbd> Save</span>
          <span><kbd style={{ padding: "2px 5px", background: "var(--bg-inset)", border: "1px solid var(--border-default)", borderRadius: "3px" }}>A</kbd> Approve</span>
        </div>
        <div style={{ color: "var(--tier-verified)", fontWeight: 600 }}>
          Active Cell: r{activeRow}c{activeCol}
        </div>
      </div>

      {/* Grid container */}
      <div style={{ overflowX: "auto", maxHeight: "420px" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12.5px" }}>
          <tbody>
            {grid.map((row, rIdx) => (
              <tr key={rIdx} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                {row.map((cell, cIdx) => {
                  const isActive = activeRow === rIdx && activeCol === cIdx;
                  const isEditing = editingCellId === cell.id;

                  return (
                    <td
                      key={cell.id}
                      onClick={() => {
                        setActiveRow(rIdx);
                        setActiveCol(cIdx);
                      }}
                      style={{
                        padding: "8px 12px",
                        backgroundColor: isActive ? "rgba(47, 214, 160, 0.08)" : rIdx === 0 ? "var(--bg-inset)" : "transparent",
                        outline: isActive ? "2px solid var(--tier-verified)" : "none",
                        outlineOffset: "-2px",
                        fontWeight: rIdx === 0 ? 600 : 400,
                        color: rIdx === 0 ? "var(--text-secondary)" : "var(--text-primary)",
                        cursor: "pointer",
                        position: "relative",
                      }}
                    >
                      {isEditing ? (
                        <input
                          autoFocus
                          value={editValue}
                          onChange={(e) => setEditValue(e.target.value)}
                          style={{
                            width: "100%",
                            background: "var(--bg-raised)",
                            color: "var(--text-primary)",
                            border: "1px solid var(--tier-verified)",
                            padding: "4px 8px",
                            borderRadius: "3px",
                            fontFamily: "'IBM Plex Mono', monospace",
                          }}
                        />
                      ) : (
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "8px" }}>
                          <span className="font-mono">{cell.rawText}</span>
                          {rIdx > 0 && <TierBadge tier={cell.tier} showLabel={false} />}
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
